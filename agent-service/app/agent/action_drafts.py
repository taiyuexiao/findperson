"""写操作动作草稿(edit 意图 → confirmation_card,V1.2 §5.2 + 实施方案v3 §3.3)。

三类写操作:
- profile:资料维护(联系方式/负责领域/自画像等当前用户可维护字段)
- review :他人画像(为同事添加事项评价)
- content:内容发布(确认后进入待审核,不得表述为已公开发布)

职责边界:
- Agent 只产出「确认卡片草稿」,不直接写业务表;确认后的写执行由前端确认链路
  调用业务后端 API 完成(v4 §五:确认更新主页/保存评价/确认发布);
- 卡片必须含:卡片标识/动作类型/待写入字段/状态/提交目标/draftId(手动补充回填用);
- 字段不足时不编造,转为澄清追问(§18:不编造事实)。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.contracts.agent_state import UserContext
from app.core import db
from app.core.llm_client import LLMPort, get_llm

ACTION_PROFILE = "profile"
ACTION_REVIEW = "review"
ACTION_CONTENT = "content"

# 他人画像事项上限(v4 §五:事项不超过 20 个字符)
REVIEW_TAG_MAX_LEN = 20

# 提交目标(前端确认后调用的业务后端 API;仅作展示与审计,不由 Agent 调用)
SUBMIT_TARGETS = {
    ACTION_PROFILE: "/api/v1/me",
    ACTION_REVIEW: "/api/v1/reviews",
    ACTION_CONTENT: "/api/v1/contents",
}

_EXTRACT_PROMPT = """你是写操作草稿提取器。用户想在首问责任平台执行一个写操作,动作类型为 {action_type}。
从用户的话里提取草稿字段,提取不到就留空,严禁编造。

动作类型说明:
- profile(资料维护):提取 nextProfilePatch,可含 contact(联系方式)/phone(手机号)/role(岗位)/domains(负责领域,数组)/selfPortrait(自画像)
- review(他人画像):提取 personName(被评价人姓名)与 tag(事项标签,不超过20字)
- content(内容发布):提取 title(标题)/tags(关联领域,数组)/summary(摘要)/body(正文)

严格输出 JSON(不要输出其他内容):
{schema}

用户问题: {query}"""

_EXTRACT_SCHEMAS = {
    ACTION_PROFILE: '{"nextProfilePatch": {"contact": "", "phone": "", "role": "", "domains": [], "selfPortrait": ""}}',
    ACTION_REVIEW: '{"personName": "", "tag": ""}',
    ACTION_CONTENT: '{"title": "", "tags": [], "summary": "", "body": ""}',
}


@dataclass
class ActionDraftResult:
    """动作草稿构建结果。card 为 None 时表示字段不足需澄清/引导手动编辑。"""

    action_type: str = ""
    card: dict[str, Any] | None = None
    reply_text: str = ""
    missing: list[str] = field(default_factory=list)
    degraded: bool = False


class ActionDraftService:
    """edit 意图的动作分类与草稿提取。"""

    def __init__(self, llm: LLMPort | None = None) -> None:
        self._llm = llm

    # ---------------- 动作分类 ----------------

    @staticmethod
    def classify(query: str) -> str | None:
        """确定性规则分类(优先级:他人画像 > 内容发布 > 资料维护);不命中返回 None。"""
        q = query.strip()
        if re.search(r"(评价|画像|点评|打标签|写标签)", q) and re.search(r"(为|给|帮)?[^我].{0,8}(评价|画像|点评)", q):
            return ACTION_REVIEW
        if re.search(r"(发布|发一?篇|投稿|写一?篇|发内容|发文章)", q):
            return ACTION_CONTENT
        if re.search(r"(修改|更新|维护|完善|填写).{0,6}(资料|信息|联系方式|电话|领域|画像|岗位|主页)", q):
            return ACTION_PROFILE
        if re.search(r"(我的|个人)(资料|联系方式|电话|负责领域|自画像|岗位)", q):
            return ACTION_PROFILE
        return None

    # ---------------- 草稿构建 ----------------

    async def build(self, query: str, user_context: UserContext, *,
                    run_id: str) -> ActionDraftResult:
        action_type = self.classify(query)
        if action_type is None:
            return ActionDraftResult(
                reply_text=("我识别到您想执行写操作,但没有完全确认类型。您可以这样说:"
                            "『修改我的联系方式为…』、『为张三添加评价:…』、『发布一篇文章:…』。"))
        # 仅他人画像需要人名词典(评价对象兑底);DB 故障不阻断其余动作
        names: list[str] = []
        if action_type == ACTION_REVIEW:
            try:
                names = await self._known_people_names(query, exclude=user_context.name)
            except Exception:  # noqa: BLE001
                names = []
        extracted, degraded = await self._extract(action_type, query)
        builder = {
            ACTION_PROFILE: self._build_profile,
            ACTION_REVIEW: self._build_review,
            ACTION_CONTENT: self._build_content,
        }[action_type]
        result = builder(query, user_context, run_id=run_id, extracted=extracted, names=names)
        result.action_type = action_type
        result.degraded = result.degraded or degraded
        return result

    # ---------------- 三类草稿 ----------------

    def _build_profile(self, query, ctx: UserContext, *, run_id, extracted, names) -> ActionDraftResult:
        patch = {k: v for k, v in (extracted.get("nextProfilePatch") or {}).items()
                 if v not in (None, "", [])}
        if not patch:
            return ActionDraftResult(
                action_type=ACTION_PROFILE,
                reply_text=("请告诉我您要更新哪项资料(联系方式/负责领域/自画像/岗位)以及新内容,"
                            "例如『把我的负责领域更新为 RAG、知识检索』。"),
                missing=["nextProfilePatch"])
        card = self._card(ACTION_PROFILE, run_id, {
            "type": ACTION_PROFILE,
            "draftId": f"draft-{run_id}",
            "nextProfilePatch": patch,
        }, summary=f"更新资料:{ '、'.join(patch.keys()) }")
        return ActionDraftResult(
            action_type=ACTION_PROFILE, card=card,
            reply_text="已为您整理资料变更草稿,确认后仅更新您本人可维护的字段。",
        )

    def _build_review(self, query, ctx: UserContext, *, run_id, extracted, names) -> ActionDraftResult:
        person_name = str(extracted.get("personName") or "").strip()
        if not person_name and names:
            person_name = names[0]
        tag = str(extracted.get("tag") or "").strip()[:REVIEW_TAG_MAX_LEN]
        missing = []
        if not person_name:
            missing.append("personName")
        if not tag:
            missing.append("tag")
        if missing:
            return ActionDraftResult(
                action_type=ACTION_REVIEW,
                reply_text="请补充评价对象和事项标签,例如『为李四添加评价:模型网关排障』(事项不超过 20 字)。",
                missing=missing)
        if person_name == ctx.name:
            return ActionDraftResult(
                action_type=ACTION_REVIEW,
                reply_text="他人画像不能评价本人,请确认评价对象。",
                missing=["personName"])
        card = self._card(ACTION_REVIEW, run_id, {
            "type": ACTION_REVIEW,
            "draftId": f"draft-{run_id}",
            "nextReview": {
                "personName": person_name,
                "personId": "",
                "tag": tag,
                "date": date.today().isoformat(),
            },
        }, summary=f"为 {person_name} 添加事项:{tag}")
        return ActionDraftResult(
            action_type=ACTION_REVIEW, card=card,
            reply_text=f"已生成对 {person_name} 的画像评价草稿,确认保存后写入其他画像。",
        )

    def _build_content(self, query, ctx: UserContext, *, run_id, extracted, names) -> ActionDraftResult:
        title = str(extracted.get("title") or "").strip()
        summary = str(extracted.get("summary") or "").strip()
        body = str(extracted.get("body") or "").strip()
        tags = extracted.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in re.split(r"[,、,]", tags) if t.strip()]
        missing = [k for k, v in (("title", title), ("summary", summary)) if not v]
        if missing:
            return ActionDraftResult(
                action_type=ACTION_CONTENT,
                reply_text="请补充内容标题和摘要(正文可手动补充),例如『发布文章《K8s 部署实践》,摘要:…』。",
                missing=missing)
        card = self._card(ACTION_CONTENT, run_id, {
            "type": ACTION_CONTENT,
            "draftId": f"draft-{run_id}",
            "nextContent": {"title": title, "tags": tags, "summary": summary, "body": body or summary},
        }, summary=f"发布内容:{title}")
        return ActionDraftResult(
            action_type=ACTION_CONTENT, card=card,
            reply_text="已生成内容草稿,确认发布后进入待审核状态(审核通过前不会对外公开)。",
        )

    # ---------------- 内部 ----------------

    @staticmethod
    def _card(action_type: str, run_id: str, action: dict, *, summary: str) -> dict:
        return {
            "id": f"confirm-{run_id}",
            "kind": "confirmation",
            "action": action,
            "analysis": {"intent": "edit", "actionType": action_type, "summary": summary},
            "status": "active",
            "submitTarget": SUBMIT_TARGETS[action_type],
        }

    async def _extract(self, action_type: str, query: str) -> tuple[dict, bool]:
        """LLM 草稿字段提取;失败返回空骨架 + degraded(由调用方走规则/澄清)。"""
        llm = self._llm or get_llm()
        try:
            data, _ = await llm.structured_chat(
                [{"role": "user", "content": _EXTRACT_PROMPT.format(
                    action_type=action_type, schema=_EXTRACT_SCHEMAS[action_type], query=query)}],
                required_keys=list(__import__("json").loads(_EXTRACT_SCHEMAS[action_type]).keys()),
            )
            return data, False
        except Exception:  # noqa: BLE001 —— LLM 失败:空骨架,降级
            return {}, True

    @staticmethod
    async def _known_people_names(query: str, *, exclude: str = "") -> list[str]:
        """文中显式出现的人名(用于 review 对象兜底),排除本人。"""
        rows = await db.fetch("SELECT name FROM public.people WHERE status='active'")
        return [r["name"] for r in rows
                if r["name"] in query and r["name"] != exclude]
