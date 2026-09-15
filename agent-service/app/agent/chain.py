"""Agent 主链装配(V1.2 §3.1 基本形式)。

AgentOrchestrator
  → IntentNode
  → QueryStructurerNode (仅 find_person)
  → ConceptLinkerNode   (仅 find_person)
  → StructuredRetrievalNode (仅 find_person;阶段 6 将在此并联 KnowledgeRetrievalNode)
  → CandidateMergerNode
  → PeopleRankerNode
  → ConfidenceGateNode
  → AnswerBuilderNode
"""
from __future__ import annotations

from app.agent.answer_builder import AnswerBuilderNode
from app.agent.concept_linker import ConceptLinkerNode
from app.agent.intent import IntentNode
from app.agent.nodes.knowledge_retrieval import KnowledgeQANode, KnowledgeRetrievalNode
from app.agent.nodes.ranking import (
    CandidateMergerNode, ConfidenceGateNode, PeopleRankerNode,
)
from app.agent.nodes.structured_retrieval import StructuredRetrievalNode
from app.agent.orchestrator import AgentOrchestrator, ServiceRegistry
from app.agent.query_structurer import QueryStructurerNode
from app.contracts.agent_state import Intent, QueryType


def build_service_registry() -> ServiceRegistry:
    """装配默认 Service(真实实现;测试可注入 stub)。"""
    return ServiceRegistry()


def build_orchestrator(services: ServiceRegistry | None = None) -> AgentOrchestrator:
    """构建主链编排器。find_person 以外的意图在 AnswerBuilder 提前终态。"""
    orch = AgentOrchestrator(services or build_service_registry())
    orch.add(IntentNode())
    find_person = lambda s: s.intent.intent == Intent.FIND_PERSON  # noqa: E731
    knowledge_qa = lambda s: s.intent.intent == Intent.KNOWLEDGE_QA  # noqa: E731
    dual_path = lambda s: (  # noqa: E731
        s.intent.intent == Intent.FIND_PERSON
        and s.intent.query_type in (QueryType.DIAGNOSTIC, QueryType.EXPERT_FINDING)
    )
    orch.add(QueryStructurerNode(), condition=find_person)
    orch.add(ConceptLinkerNode(), condition=find_person)
    # diagnostic / expert_finding:结构化路与知识路并联(RetrievalCoordinator,§3.1/§8.1)
    orch.add_parallel([StructuredRetrievalNode(), KnowledgeRetrievalNode()],
                      label="RetrievalCoordinator", condition=dual_path)
    # contact_lookup / explicit_responsibility:仅结构化路(§8.1:不执行无意义工具调用)
    orch.add(StructuredRetrievalNode(), condition=lambda s: find_person(s) and not dual_path(s))
    # knowledge_qa:MCP 知识检索(§10.10)
    orch.add(KnowledgeQANode(), condition=knowledge_qa)
    orch.add(CandidateMergerNode(), condition=find_person)
    orch.add(PeopleRankerNode(), condition=find_person)
    orch.add(ConfidenceGateNode(), condition=find_person)
    orch.add(AnswerBuilderNode())
    return orch
