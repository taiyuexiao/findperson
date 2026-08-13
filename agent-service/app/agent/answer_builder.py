"""AnswerBuilder(V1.2 §13.1)。

Hermes/模板只负责自然语言组织。回答强制分「检索到的事实 / 建议」;
人员标注身份(正式责任人/明确负责领域命中者/相关参与者/能力候选人/领域专家)。
不得:新增 PeopleRanker 未返回人员、修改顺序、将文章作者描述成正式负责人。

V1 实现为确定性模板(离线可测、天然满足「不新增/不重排」);
LLM 润色留作后续可选项,不改变事实与顺序。
"""
from __future__ import annotations

from app.agent.orchestrator import AgentNode, ServiceRegistry
from app.contracts.agent_state import (
    AgentState, ConfidenceDecision, Intent, QueryType, ResponseState, StateUpdate,
)
from app.contracts.evidence import EvidenceType
from app.core import db

# 身份标签(§13.1)
IDENTITY_FORMAL = "正式责任人"
IDENTITY_LEAF = "明确负责领域命中者"
IDENTITY_RELATED = "相关参与者"
IDENTITY_EXPERT = "领域专家"
IDENTITY_CANDIDATE = "能力候选人"

# 事实部分最多呈现的候选人数(完整列表在 recommendation_cards 中另给 Top5)
MAX_FACT_CANDIDATES = 5


def _identity_of(candidate: dict) -> str:
    """按证据语义定身份标签(不得把文章作者标成正式责任人)。"""
    if candidate.get("has_formal"):
        return IDENTITY_FORMAL
    levels = {(e.get("detail") or {}).get("match_level") for e in candidate.get("evidences", [])}
    types = {e.get("evidence_type") for e in candidate.get("evidences", [])}
    if "leaf_exact" in levels:
        return IDENTITY_LEAF
    if EvidenceType.INFERRED_FROM_ARTICLE.value in types:
        return IDENTITY_EXPERT
    if EvidenceType.INFERRED_FROM_PROFILE.value in types:
        return IDENTITY_CANDIDATE
    return IDENTITY_RELATED


class AnswerBuilder:
    """回答组织器(确定性模板)。"""

    async def build(self, state: AgentState) -> ResponseState:
        response = ResponseState()
        decision = state.ranking.gate_decision or ConfidenceDecision.ANSWER
        ranked = state.ranking.ranked_candidates
        names = await self._load_names([c["person_id"] for c in ranked])

        if decision == ConfidenceDecision.NO_RESULT:
            # 空结果不编造(§18)
            response.facts = ["没有找到与您的问题匹配的责任人或专家。"]
            response.suggestions = ["可以尝试换个说法,例如补充系统名称、领域关键词;",
                                    "也可以在个人名片中完善“负责领域”信息。"]
            response.final_answer = self._render(response)
            return response
        if decision == ConfidenceDecision.CLARIFY:
            response.clarification = self._build_clarification(state)
            response.final_answer = response.clarification
            return response

        # answer / degraded_answer
        qt = state.intent.query_type
        if qt == QueryType.CONTACT_LOOKUP:
            self._build_contact_facts(state, ranked, names, response)
        else:
            self._build_person_facts(ranked, names, response)
        self._build_suggestions(state, ranked, response)
        response.recommendation_cards = self._build_cards(ranked, names)
        response.final_answer = self._render(response, degraded=(decision == ConfidenceDecision.DEGRADED_ANSWER))
        return response

    # ---------------- 事实组织 ----------------

    def _build_contact_facts(self, state, ranked, names, response) -> None:
        for c in ranked:
            for e in c.get("evidences", []):
                d = e.get("detail") or {}
                if d.get("name"):
                    response.facts.append(
                        f"{d['name']}({d.get('department','')}/{d.get('role','')}),"
                        f"联系方式:{d.get('contact') or '未登记'}。"
                    )

    def _build_person_facts(self, ranked, names, response) -> None:
        for c in ranked[:MAX_FACT_CANDIDATES]:  # 事实只呈现 Top N,避免刷屏
            pid = c["person_id"]
            identity = _identity_of(c)
            name = names.get(pid, pid)
            if identity == IDENTITY_FORMAL and c.get("responsibilities"):
                rec = c["responsibilities"][0]
                response.facts.append(
                    f"{name} 是【{rec['title']}】的{identity}(责任部门:{rec.get('owner_department','')},"
                    f"时限:{rec.get('time_limit','')},升级路径:{rec.get('escalation_path','')})。"
                )
            else:
                raw_tags = [((e.get("detail") or {}).get("source_raw_tag") or "")
                            for e in c.get("evidences", [])]
                raw_tags = [t for t in raw_tags if t]
                tag_txt = f",负责领域:{ '、'.join(raw_tags[:3]) }" if raw_tags else ""
                response.facts.append(f"{name} 是{identity}{tag_txt}。")

    def _build_suggestions(self, state, ranked, response) -> None:
        decision = state.ranking.gate_decision
        if decision == ConfidenceDecision.DEGRADED_ANSWER:
            response.suggestions.append(
                "本次结果部分来自降级路径(如知识服务不可用时的业务直读),建议稍后复核。")
        qt = state.intent.query_type
        if qt == QueryType.DIAGNOSTIC and ranked:
            response.suggestions.append("如首要责任人无法解决,可按升级路径逐级上报。")
        elif qt == QueryType.EXPERT_FINDING and ranked:
            top = ranked[0]["person_id"]
            response.suggestions.append("可以通过查看其发表的文章进一步了解其专业深度。")
        elif qt == QueryType.EXPLICIT_RESPONSIBILITY:
            if not any(c.get("has_formal") for c in ranked):
                response.suggestions.append(
                    "当前未查到该领域的正式责任登记,以上基于人员自填负责领域,建议向部门负责人确认。")

    def _build_clarification(self, state: AgentState) -> str:
        if state.intent.clarify_question:
            return state.intent.clarify_question
        if state.concept.ambiguous:
            terms = [t["term"] for t in state.concept.concept_link_trace]
            return (f"您提到的「{'、'.join(terms[:3])}」可能存在多种理解,"
                    f"能具体说明是哪方面的业务或系统吗?")
        return "找到多位可能相关的人员,能否补充更多条件(如具体系统、部门)?"

    def _build_cards(self, ranked, names) -> list[dict]:
        cards = []
        for c in ranked[:5]:
            pid = c["person_id"]
            cards.append({
                "person_id": pid,
                "name": names.get(pid, pid),
                "identity": _identity_of(c),
                "score": c["score"],
                "responsibilities": c.get("responsibilities", []),
                "evidence_count": c["evidence_count"],
            })
        return cards

    async def _load_names(self, person_ids: list[str]) -> dict[str, str]:
        if not person_ids:
            return {}
        rows = await db.fetch(
            "SELECT id, name FROM public.people WHERE id = ANY($1)", person_ids)
        return {r["id"]: r["name"] for r in rows}

    def _render(self, response: ResponseState, *, degraded: bool = False) -> str:
        parts = []
        if response.facts:
            parts.append("【检索到的事实】\n" + "\n".join(response.facts))
        if response.suggestions:
            parts.append("【建议】\n" + "\n".join(response.suggestions))
        if degraded:
            parts.append("(本回答包含降级路径结果)")
        return "\n\n".join(parts)


class AnswerBuilderNode(AgentNode):
    """回答生成节点。find_person 走完整组织;chat/unclear 走提前终态。"""

    name = "AnswerBuilderNode"
    timeout_ms = 8000
    on_error = "degrade"

    async def execute(self, state: AgentState, services: ServiceRegistry) -> StateUpdate:
        builder = services.get("answer_builder") if "answer_builder" in services.services else AnswerBuilder()
        update = StateUpdate()

        if state.intent.intent == Intent.CHAT:
            # chat:简单实现(§5.2),不进检索排序
            update.response = ResponseState(
                final_answer="您好!我是首问责任助手,可以帮您查找负责人、专家,或查询制度流程知识。")
            update.terminate = True
            return update
        if state.intent.intent == Intent.UNCLEAR or state.intent.needs_clarification:
            update.response = ResponseState(
                clarification=(state.intent.clarify_question
                               or "我没有完全理解您的问题,能否换一种说法,例如『谁负责XX系统』?"))
            update.response.final_answer = update.response.clarification
            update.terminate = True
            return update
        if state.intent.intent == Intent.EDIT:
            # 写操作:产出 confirmation_card 草稿(资料维护/他人画像/内容发布,§实施方案v3 §3.3)
            # Agent 不写业务表;确认后由前端确认链路调业务后端 API 执行。
            from app.agent.action_drafts import ActionDraftService
            service = (services.get("action_drafts")
                       if "action_drafts" in services.services else ActionDraftService())
            query = state.request.normalized_query or state.request.original_query
            result = await service.build(query, state.request.user_context,
                                         run_id=state.request.run_id)
            update.response = ResponseState(final_answer=result.reply_text,
                                            confirmation_card=result.card)
            if result.degraded:
                update.degraded = True
            update.terminate = True
            return update
        if state.intent.intent == Intent.KNOWLEDGE_QA:
            # §10.10:有证据 → 事实+引用;无证据 → 诚实空答,不编造
            hits = state.retrieval.rag_documents
            if hits:
                update.response = ResponseState(
                    facts=[h["content"] for h in hits[:3]],
                    suggestions=["以上回答基于已发布的知识文档,来源见引用;如需最新信息请确认文档版本。"],
                    citations=[{
                        "document_id": h["document_id"], "chunk_id": h["chunk_id"],
                        "version": h["version"], "source_uri": h["source_uri"],
                    } for h in hits],
                )
                update.response.final_answer = (
                    "【检索到的事实】\n" + "\n".join(update.response.facts)
                    + "\n\n【建议】\n" + "\n".join(update.response.suggestions)
                )
            else:
                update.response = ResponseState(
                    facts=["没有找到与您问题相关的已发布知识。"],
                    suggestions=["可以尝试换个说法,或补充制度/流程/系统的名称;",
                                 "也可以改问『谁负责XX』类找人问题。"],
                    final_answer="【检索到的事实】\n没有找到与您问题相关的已发布知识。\n\n【建议】\n可以尝试换个说法。",
                )
            if state.execution.degraded:
                update.degraded = True
            update.terminate = True
            return update

        update.response = await builder.build(state)
        return update
