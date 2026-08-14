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

# 资料字段中文名(changes 展示用)
# 注意:键名必须落前端确认白名单(auth store updateProfile):contact/addDomains/selfPortrait
FIELD_LABELS = {
    "contact": "联系方式", "addDomains": "负责领域", "selfPortrait": "自画像",
}

# LLM/规则提取键 → 前端可维护键(不在白名单内的键确认时会被前端丢弃)
_PATCH_KEY_MAP = {"phone": "contact", "domains": "addDomains"}
_PATCH_DROP_KEYS = {"role", "name", "phone", "domains"}  # role/name 非本人可维护项

_EXTRACT_PROMPT = """你是写操作草稿提取器。用户想在首问责任平台执行一个写操作,动作类型为 {action_type}。
从用户的话里提取草稿字段,提取不到就留空,严禁编造。

动作类型说明:
- profile(资料维护):提取 nextProfilePatch,可含 contact(联系方式)/phone(手机号)/role(岗位)/domains(负责领域,数组)/selfPortrait(自画像)
- review(他人画像):提取 personName(被评价人姓名)与 tag(事项标签,不超过20字)
- content(内容发布):提取 title(标题)/tags(关联领域,数组)/summary(摘要)/body(正文)

严格输出 JSON(不要输出其他内容)。字段格式如下,值必须是从问题中提取的内容,严禁照抄示例中的空值:
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
        name_to_id: dict[str, str] = {}
        if action_type == ACTION_REVIEW:
            try:
                name_to_id = await self._known_people_map(query, exclude=user_context.name)
            except Exception:  # noqa: BLE001
                name_to_id = {}
        extracted, degraded = await self._extract(action_type, query)
        builder = {
            ACTION_PROFILE: self._build_profile,
            ACTION_REVIEW: self._build_review,
            ACTION_CONTENT: self._build_content,
        }[action_type]
        result = builder(query, user_context, run_id=run_id, extracted=extracted,
                         names=name_to_id)
        result.action_type = action_type
        result.degraded = result.degraded or degraded
        return result

    # ---------------- 三类草稿 ----------------

    def _build_profile(self, query, ctx: UserContext, *, run_id, extracted, names) -> ActionDraftResult:
        patch = {k: v for k, v in (extracted.get("nextProfilePatch") or {}).items()
                 if v not in (None, "", [])}
        if not patch:
            # 规则兑底:「电话/联系方式 ... X」(兼容 改为/修改为/是 等说法)
            m = re.search(r"(?:联系方式|电话|手机)[^0-9]{0,6}([0-9][0-9\-]{3,})", query)
            if m:
                patch = {"contact": m.group(1)}
        if not patch:
            return ActionDraftResult(
                action_type=ACTION_PROFILE,
                reply_text=("请告诉我您要更新哪项资料(联系方式/负责领域/自画像/岗位)以及新内容,"
                            "例如『把我的负责领域更新为 RAG、知识检索』。"),
                missing=["nextProfilePatch"])
        # 键名归一:phone→contact、domains→addDomains;剔除前端不可维护字段
        normalized: dict = {}
        for key, value in patch.items():
            mapped = _PATCH_KEY_MAP.get(key, key)
            if mapped in FIELD_LABELS and mapped not in normalized:
                normalized[mapped] = value
        patch = normalized
        if not patch:
            return ActionDraftResult(
                action_type=ACTION_PROFILE,
                reply_text=("识别到的字段不在本人可维护范围(联系方式/负责领域/自画像),"
                            "岗位/姓名等请联系管理员变更。"),
                missing=["nextProfilePatch"])
        changes = [f"{FIELD_LABELS.get(k, k)}将更新为 {('、'.join(v) if isinstance(v, list) else v)}"
                   for k, v in patch.items()]
        card = self._card(ACTION_PROFILE, run_id, {
            "type": ACTION_PROFILE,
            "draftId": f"draft-{run_id}",
            "title": "检测到资料维护需求",
            "description": "识别到你要更新本人资料,确认后仅更新你可维护的字段。",
            "changes": changes,
            "nextProfilePatch": patch,
        }, summary=f"更新资料:{ '、'.join(patch.keys()) }")
        return ActionDraftResult(
            action_type=ACTION_PROFILE, card=card,
            reply_text="已为您整理资料变更草稿,确认后仅更新您本人可维护的字段。",
        )

    def _build_review(self, query, ctx: UserContext, *, run_id, extracted, names) -> ActionDraftResult:
        person_name = str(extracted.get("personName") or "").strip()
        if not person_name and names:
            person_name = next(iter(names.keys()), "")
        tag = str(extracted.get("tag") or "").strip()[:REVIEW_TAG_MAX_LEN]
        if not tag:
            # 规则兑底:「评价:事项」「画像:事项」
            m = re.search(r"(?:评价|画像|点评)[:：]([^,，。！？!?]{1,20})", query)
            if m:
                tag = m.group(1).strip()[:REVIEW_TAG_MAX_LEN]
        if not person_name:
            return ActionDraftResult(
                action_type=ACTION_REVIEW,
                reply_text="请补充评价对象和事项标签,例如『为李四添加评价:模型网关排障』(事项不超过 20 字)。",
                missing=["personName"])
        if person_name == ctx.name:
            return ActionDraftResult(
                action_type=ACTION_REVIEW,
                reply_text="他人画像不能评价本人,请确认评价对象。",
                missing=["personName"])
        # 字段不完整仍出部分草稿卡(v4 §五:手动补充经 draftId 回填)
        card = self._card(ACTION_REVIEW, run_id, {
            "type": ACTION_REVIEW,
            "draftId": f"draft-{run_id}",
            "title": "为你生成一条待确认评价",
            "description": f"评价对象:{person_name};确认保存后写入其画像。",
            "changes": [f"评价对象:{person_name}", f"事项:{tag or '(待补充)'}",
                        f"日期:{date.today().isoformat()}"],
            "nextReview": {
                "personName": person_name,
                "personId": names.get(person_name, ""),
                "tag": tag,
                "text": tag,  # 前端评价卡渲染 nextReview.text
                "date": date.today().isoformat(),
            },
        }, summary=f"为 {person_name} 添加事项:{tag or '(待补充)'}")
        if not tag:
            return ActionDraftResult(
                action_type=ACTION_REVIEW, card=card,
                reply_text=(f"已生成对 {person_name} 的画像评价草稿,还请补充事项标签;"
                            "可点『继续修改』进入画像页补全后保存。"),
                missing=["tag"])
        return ActionDraftResult(
            action_type=ACTION_REVIEW, card=card,
            reply_text=f"已生成对 {person_name} 的画像评价草稿,确认保存后写入其他画像。",
        )

    def _build_content(self, query, ctx: UserContext, *, run_id, extracted, names) -> ActionDraftResult:
        title = str(extracted.get("title") or "").strip()
        if not title:
            # 规则兑底:《标题》或「一/篇 XXX」片段
            m = re.search(r"《([^》]{2,60})》", query) or re.search(r"一?篇([^,，。！？!?]{2,30})", query)
            if m:
                title = m.group(1).strip()
        summary = str(extracted.get("summary") or "").strip()
        body = str(extracted.get("body") or "").strip()
        tags = extracted.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in re.split(r"[,、,]", tags) if t.strip()]
        if not title:
            return ActionDraftResult(
                action_type=ACTION_CONTENT,
                reply_text="请补充内容标题和摘要(正文可手动补充),例如『发布文章《K8s 部署实践》,摘要:…』。",
                missing=["title"])
        # 摘要/正文缺失仍出部分草稿卡(v4 §五:手动补充经 draftId 跳转发布页回填)
        missing = [k for k, v in (("summary", summary),) if not v]
        card = self._card(ACTION_CONTENT, run_id, {
            "type": ACTION_CONTENT,
            "draftId": f"draft-{run_id}",
            "title": "已整理内容发布草稿",
            "description": "确认发布后进入待审核状态,审核通过前不会对外公开。",
            "changes": [f"标题:{title}"]
                       + ([f"关联领域:{'、'.join(tags)}"] if tags else [])
                       + ([f"摘要:{summary[:40]}"] if summary else []),
            "nextContent": {"title": title, "tags": tags,
                            "summary": summary, "body": body or summary},
        }, summary=f"发布内容:{title}")
        if missing:
            return ActionDraftResult(
                action_type=ACTION_CONTENT, card=card,
                reply_text=(f"已生成《{title}》的内容草稿,摘要/正文可点『手动补充』到发布页完善;"
                            "确认发布后进入待审核状态(审核通过前不会对外公开)。"),
                missing=missing)
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
    async def _known_people_map(query: str, *, exclude: str = "") -> dict[str, str]:
        """文中显式出现的人名 → id(用于 review 对象兜底),排除本人。"""
        rows = await db.fetch("SELECT id, name FROM public.people WHERE status='active'")
        return {r["name"]: r["id"] for r in rows
                if r["name"] in query and r["name"] != exclude}
