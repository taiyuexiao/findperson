"""Merger/Ranker/Gate 三个 Node:把服务挂到编排主链上。"""
from __future__ import annotations

from app.agent.candidate_merger import CandidateMerger
from app.agent.orchestrator import AgentNode, ServiceRegistry
from app.agent.people_ranker import ConfidenceGate, PeopleRanker
from app.contracts.agent_state import AgentState, Intent, StateUpdate


class CandidateMergerNode(AgentNode):
    """候选融合节点(§12.2)。"""

    name = "CandidateMergerNode"
    timeout_ms = 5000
    on_error = "degrade"

    async def execute(self, state: AgentState, services: ServiceRegistry) -> StateUpdate:
        if state.intent.intent != Intent.FIND_PERSON:
            return StateUpdate()
        merger = services.get("candidate_merger") if "candidate_merger" in services.services else CandidateMerger()
        merged = merger.merge(
            state.retrieval.structured_candidates,
            state.retrieval.rag_person_evidence,
            state.retrieval.responsibility_evidence,
        )
        update = StateUpdate()
        update.ranking = state.ranking.model_copy(deep=True)
        update.ranking.merged_candidates = [c.to_dict() for c in merged]
        return update


class PeopleRankerNode(AgentNode):
    """人员排序节点(§12.3)。"""

    name = "PeopleRankerNode"
    timeout_ms = 5000
    on_error = "degrade"

    async def execute(self, state: AgentState, services: ServiceRegistry) -> StateUpdate:
        if state.intent.intent != Intent.FIND_PERSON:
            return StateUpdate()
        merger = services.get("candidate_merger") if "candidate_merger" in services.services else CandidateMerger()
        # 用户反馈回流:聚合反馈微调排序;反馈服务故障不阻断主链(降级为无调整)
        feedback_adjust: dict[str, float] = {}
        try:
            from app.feedback.service import FeedbackService
            fb = (services.get("feedback_service")
                  if "feedback_service" in services.services else FeedbackService())
            feedback_adjust = await fb.person_adjustments()
        except Exception:  # noqa: BLE001 —— 反馈不可用不影响排序主链
            feedback_adjust = {}
        # ranked 输入是 merge 结果的字典形式,还原为轻量对象排序
        candidates = []
        from app.agent.candidate_merger import MergedPersonCandidate
        from app.contracts.evidence import PersonEvidence
        for raw in state.ranking.merged_candidates:
            c = MergedPersonCandidate(raw["person_id"])
            c.evidences = [PersonEvidence.model_validate(e) for e in raw["evidences"]]
            c.responsibilities = raw.get("responsibilities", [])
            candidates.append(c)
        ranker = services.get("people_ranker") if "people_ranker" in services.services else PeopleRanker()
        ranked, policy, top1 = ranker.rank(
            candidates, state.intent.query_type,
            query=state.request.normalized_query or state.request.original_query,
            feedback_adjust=feedback_adjust,
        )
        update = StateUpdate()
        update.ranking = state.ranking.model_copy(deep=True)
        update.ranking.ranked_candidates = ranked
        update.ranking.rank_policy = policy
        update.ranking.confidence = top1
        return update


class ConfidenceGateNode(AgentNode):
    """置信度闸门节点(§12.4)。"""

    name = "ConfidenceGateNode"
    timeout_ms = 3000
    on_error = "degrade"

    async def execute(self, state: AgentState, services: ServiceRegistry) -> StateUpdate:
        if state.intent.intent != Intent.FIND_PERSON:
            return StateUpdate()
        gate = services.get("confidence_gate") if "confidence_gate" in services.services else ConfidenceGate()
        decision = gate.decide(
            state.ranking.ranked_candidates,
            concept_ambiguous=state.concept.ambiguous,
            degraded=state.execution.degraded,
        )
        update = StateUpdate()
        update.ranking = state.ranking.model_copy(deep=True)
        update.ranking.gate_decision = decision
        return update
