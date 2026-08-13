"""知识检索节点 + Knowledge QA 节点(V1.2 §8.1 diagnostic/expert_finding 知识路、§10.10)。

KnowledgeRetrievalNode:diagnostic / expert_finding 时经 MCP search_knowledge
取知识证据,经 RagEvidenceAdapter 转为人员证据;MCP 失败降级(结构化路径仍可用)。
contact_lookup / explicit_responsibility 不执行(§8.1:不执行无意义工具调用)。

KnowledgeQANode:intent=knowledge_qa 时经 MCP search_knowledge 取证据,
写 retrieval.rag_documents;无证据时由 AnswerBuilder 诚实空答(§10.10)。
"""
from __future__ import annotations

from app.agent.orchestrator import AgentNode, ServiceRegistry
from app.contracts.agent_state import AgentState, Intent, QueryType, StateUpdate
from app.contracts.mcp import RagHit
from app.mcp_knowledge.client import KnowledgeMcpClient, get_mcp_client
from app.rag.evidence_adapter import RagEvidenceAdapter

_KNOWLEDGE_QUERY_TYPES = (QueryType.DIAGNOSTIC, QueryType.EXPERT_FINDING)


class KnowledgeRetrievalNode(AgentNode):
    """知识路检索节点(find_person 双路之 RAG 路)。"""

    name = "KnowledgeRetrievalNode"
    timeout_ms = 8000
    on_error = "degrade"

    async def execute(self, state: AgentState, services: ServiceRegistry) -> StateUpdate:
        if state.intent.intent != Intent.FIND_PERSON:
            return StateUpdate()
        if state.intent.query_type not in _KNOWLEDGE_QUERY_TYPES:
            return StateUpdate()  # §8.1:contact_lookup/explicit_responsibility 不走 RAG

        mcp = services.get("mcp_client") if "mcp_client" in services.services else get_mcp_client()
        query = state.request.normalized_query or state.request.original_query
        # diagnostic/expert_finding 用结构化关键词生成更短的检索式,提升 RAG 召回精度
        if state.intent.query_type == QueryType.DIAGNOSTIC:
            terms = (
                state.understanding.mentioned_systems
                + state.understanding.symptoms
                + state.understanding.objects
                + state.understanding.duty_clues
                + [c.get("canonical_name", "") for c in state.concept.resolved_concepts]
            )
            short = " ".join(t for t in terms if t).strip()
            if short:
                query = short
        elif state.intent.query_type == QueryType.EXPERT_FINDING:
            terms = (
                state.understanding.mentioned_systems
                + state.understanding.objects
                + state.understanding.explicit_terms
                + [c.get("canonical_name", "") for c in state.concept.resolved_concepts]
            )
            short = " ".join(t for t in terms if t).strip()
            if short:
                query = short
        update = StateUpdate()
        update.retrieval = state.retrieval.model_copy(deep=True)

        resp = await mcp.search_knowledge(
            query, user_context=state.request.user_context,
            trace_id=state.trace.trace_id, top_k=5,
        )
        if not resp.ok:
            # MCP 失败:路径 A 仍可用,显式降级(§12.2/§21 基线:MCP 不可用时路径 A 可降级 100%)
            update.retrieval.degraded_sources.append("mcp_search_knowledge")
            update.degraded = True
            return update

        hits = [RagHit.model_validate(h) for h in (resp.data or {}).get("hits", [])]
        update.retrieval.rag_documents = [h.model_dump() for h in hits]
        adapter = (services.get("rag_evidence_adapter")
                   if "rag_evidence_adapter" in services.services else RagEvidenceAdapter())
        update.retrieval.rag_person_evidence = [
            e.model_dump() for e in adapter.to_person_evidence(hits)
        ]
        return update


class KnowledgeQANode(AgentNode):
    """知识问答节点(§10.10):knowledge_qa 经 MCP 检索证据。"""

    name = "KnowledgeQANode"
    timeout_ms = 8000
    on_error = "degrade"

    async def execute(self, state: AgentState, services: ServiceRegistry) -> StateUpdate:
        if state.intent.intent != Intent.KNOWLEDGE_QA:
            return StateUpdate()
        mcp = services.get("mcp_client") if "mcp_client" in services.services else get_mcp_client()
        query = state.request.normalized_query or state.request.original_query
        update = StateUpdate()
        update.retrieval = state.retrieval.model_copy(deep=True)

        resp = await mcp.search_knowledge(
            query, user_context=state.request.user_context,
            trace_id=state.trace.trace_id, top_k=5,
        )
        if not resp.ok:
            update.retrieval.degraded_sources.append("mcp_search_knowledge")
            update.degraded = True
            return update
        hits = [RagHit.model_validate(h) for h in (resp.data or {}).get("hits", [])]
        update.retrieval.rag_documents = [h.model_dump() for h in hits]
        return update
