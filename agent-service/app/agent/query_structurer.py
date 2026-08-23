"""QueryStructurer(V1.2 §6.1)。

把用户问题结构化为统一框架(systems/objects/symptoms/duty_clues/people/departments/constraints)。

职责边界(§6.1):
- 只表达用户问题,不完成最终概念链接(概念链接是 ConceptLinker 的事);
- 明确区分「文本中显式出现」与「模型推断」的字段来源;
- 解析失败不产生虚假概念——失败时返回空框架 + degraded。
"""
from __future__ import annotations

import re

from app.agent.orchestrator import AgentNode, ServiceRegistry
from app.contracts.agent_state import (
    AgentState, Intent, StateUpdate, UnderstandingState,
)
from app.core import db
from app.core.llm_client import LLMPort, get_llm

STRUCTURER_PROMPT = """你是问题结构化器。从用户问题中抽取以下要素(不要编造,问题里没有就留空):

- systems:提到的系统/平台/产品/业务领域/事项名称(如 Dify、HiAgent、模型网关、食堂、出入境、数据治理、篮球)。注意:用户问"谁负责X/谁懂X/谁喜欢X/办理X找谁"时,X 本身就是,必须抽出
- objects:涉及的对象(如 Agent、大模型调用、接口)
- symptoms:症状/异常现象(如 响应慢、并发高时超时、报错)
- duty_clues:职责线索(如 性能优化、故障排查、运维、管理、办理)

严格输出 JSON(不要输出其他内容,没有就给空数组):
{{"systems": [], "objects": [], "symptoms": [], "duty_clues": []}}

{history_block}用户问题: {query}"""


class QueryStructurerService:
    """问题结构化服务:词典显式匹配 + LLM 要素抽取,合并并标注字段来源。"""

    def __init__(self, llm: LLMPort | None = None) -> None:
        self._llm = llm

    async def structure(self, query: str, history: list[dict] | None = None) -> UnderstandingState:
        state = UnderstandingState()

        # ---- 1) 词典显式匹配(显式出现,field_sources=explicit) ----
        people_rows = await db.fetch("SELECT name FROM public.people WHERE status='active'")
        dept_rows = await db.fetch("SELECT name FROM public.departments")
        for r in people_rows:
            if r["name"] in query:
                state.mentioned_people.append(r["name"])
                state.field_sources[f"people:{r['name']}"] = "explicit"
        # 多轮记忆:本轮未显式提及人名时,从对话历史补全(追问/指代,标 inferred)
        if history and not state.mentioned_people:
            from app.agent.memory import format_history
            history_text = format_history(history, max_chars=500)
            for r in people_rows:
                if r["name"] in history_text:
                    state.mentioned_people.append(r["name"])
                    state.field_sources[f"people:{r['name']}"] = "inferred"
        for r in dept_rows:
            if r["name"] in query:
                state.mentioned_departments.append(r["name"])
                state.field_sources[f"departments:{r['name']}"] = "explicit"

        # 书名号内容原样保留为对象:文章标题是检索最强线索,防 LLM 泛化丢字
        # (《智能问数的工作方法与要点》被抽成「智能问数」后区分度尽失)
        for m in re.finditer(r"《([^》]{2,60})》", query):
            title = m.group(1).strip()
            if title and title not in state.objects:
                state.objects.append(title)
                state.field_sources[f"objects:{title}"] = "explicit"

        # 概念显式匹配:canonical_name 与 alias 命中即放入 mentioned_systems(大小写不敏感)
        query_lower = query.lower()
        concept_rows = await db.fetch(
            "SELECT canonical_name FROM agent.concepts WHERE status IN ('seed','active')"
        )
        alias_rows = await db.fetch("SELECT alias FROM agent.concept_aliases")
        concept_names = {r["canonical_name"] for r in concept_rows}
        aliases = {r["alias"] for r in alias_rows}
        for name in sorted(concept_names, key=len, reverse=True):
            if name.lower() in query_lower:
                state.mentioned_systems.append(name)
                state.field_sources[f"systems:{name}"] = "explicit"
        for alias in sorted(aliases, key=len, reverse=True):
            if alias in query_lower and alias not in {n.lower() for n in concept_names}:
                state.mentioned_systems.append(alias)
                state.field_sources[f"systems:{alias}"] = "explicit"

        # ---- 2) LLM 要素抽取(模型推断,field_sources=inferred) ----
        # LLM 失败时仅保留词典显式匹配结果(§6.1:不产生虚假概念;词典结果在异常时不丢失)
        llm = self._llm or get_llm()
        history_block = ""
        if history:
            from app.agent.memory import format_history
            text = format_history(history)
            if text:
                history_block = f"对话历史(供理解追问/指代):\n{text}\n\n"
        try:
            data, _ = await llm.structured_chat(
                [{"role": "user", "content": STRUCTURER_PROMPT.format(query=query, history_block=history_block)}],
                required_keys=["systems", "objects", "symptoms", "duty_clues"],
            )
        except Exception:  # noqa: BLE001
            data = {}
        for field in ("systems", "objects", "symptoms", "duty_clues"):
            values = data.get(field) or []
            if not isinstance(values, list):
                values = [str(values)]
            target = {
                "systems": state.mentioned_systems,
                "objects": state.objects,
                "symptoms": state.symptoms,
                "duty_clues": state.duty_clues,
            }[field]
            for v in values:
                v = str(v).strip()
                if v and v not in target:
                    target.append(v)
                    # 显式出现在原文的标记 explicit,否则 inferred(§6.1 验收)
                    state.field_sources[f"{field}:{v}"] = "explicit" if v in query else "inferred"

        # explicit_terms:所有显式出现的词项汇总(供 ConceptLinker 优先对齐)
        state.explicit_terms = [k.split(":", 1)[1] for k, s in state.field_sources.items()
                                if s == "explicit" and not k.startswith(("people:", "departments:"))]
        return state


class QueryStructurerNode(AgentNode):
    """问题理解节点。仅 find_person 执行(编排器按条件挂载)。

    解析失败不产生虚假概念:LLM 失败时保留词典匹配结果,degraded 继续(§6.1)。
    """

    name = "QueryStructurerNode"
    timeout_ms = 15000
    on_error = "degrade"

    async def execute(self, state: AgentState, services: ServiceRegistry) -> StateUpdate:
        if state.intent.intent != Intent.FIND_PERSON:
            return StateUpdate()  # 非找人不执行(双保险,正常由编排条件控制)
        query = state.request.normalized_query or state.request.original_query
        service = (services.get("query_structurer") if "query_structurer" in services.services
                   else QueryStructurerService())
        try:
            understanding = await service.structure(query, history=state.request.history)
            return StateUpdate(understanding=understanding)
        except Exception as e:  # noqa: BLE001 —— LLM 失败:保留词典匹配,不产生虚假概念
            fallback = UnderstandingState()
            people_rows = await db.fetch("SELECT name FROM public.people WHERE status='active'")
            for r in people_rows:
                if r["name"] in query:
                    fallback.mentioned_people.append(r["name"])
                    fallback.field_sources[f"people:{r['name']}"] = "explicit"
            return StateUpdate(
                understanding=fallback, degraded=True,
                error={"code": "LLM_ERROR", "message": f"QueryStructurer LLM 失败,仅保留词典匹配: {e}"},
            )
