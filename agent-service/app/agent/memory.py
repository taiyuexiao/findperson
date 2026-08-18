"""会话记忆(多轮对话上下文)。

从 agent.agui_messages 读取同一会话的最近 N 轮消息,注入 AgentState.request.history,
供 IntentNode / QueryStructurerNode 等节点的 LLM prompt 使用,支撑追问、指代消解。

约束:
- 记忆只读不回写(消息落库仍由 AguiService 负责);
- 读取失败不阻断主链(降级为空历史);
- 注入 prompt 时截断,防止上下文膨胀。
"""
from __future__ import annotations

from app.core import db

# 注入 LLM 的历史轮次上限(一轮 = user + assistant 两条)
MAX_HISTORY_TURNS = 6
# 单条历史文本注入 prompt 时的截断长度
MAX_HISTORY_TEXT = 120


async def load_history(session_id: str | None, *, max_turns: int = MAX_HISTORY_TURNS) -> list[dict]:
    """读取会话最近 N 轮历史,按时间正序返回 [{role, text}]。

    本轮用户消息在回答生成后才落库,因此查询到的均为历史消息,天然排除本轮。
    """
    if not session_id:
        return []
    try:
        rows = await db.fetch(
            "SELECT role, text FROM agent.agui_messages"
            " WHERE session_id=$1 ORDER BY id DESC LIMIT $2",
            session_id, max_turns * 2,
        )
    except Exception:  # noqa: BLE001 —— 记忆读取失败不阻断问答
        return []
    return [{"role": r["role"], "text": r["text"]} for r in reversed(rows)]


def format_history(history: list[dict], *, max_chars: int = MAX_HISTORY_TEXT) -> str:
    """格式化为 prompt 用的纯文本块;无历史返回空串。"""
    if not history:
        return ""
    lines = []
    for m in history:
        role = "用户" if m.get("role") == "user" else "助手"
        text = " ".join(str(m.get("text") or "").split())[:max_chars]
        if text:
            lines.append(f"{role}: {text}")
    return "\n".join(lines)
