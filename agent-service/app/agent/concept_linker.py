"""查询侧 ConceptLinker(V1.2 §7.6 / §7.3)。

与员工侧 RawTag ConceptLinker 共用同一套 Concept Registry 和 Candidate Recall 能力,
输入是 Query Structure(QueryStructurer 的 UnderstandingState)。

本模块实现六级映射链的前三级(确定性召回,§7.3):
  1. Canonical Name Exact
  2. Alias Exact
  3. RawTag Historical Mapping(历史上相同 RawTag 已审核映射,直接复用)
第四级 pg_trgm、第五级 Concept Vector 在模块 17,第六级 LLM 消歧在模块 18。

V1 阶段 1 的确认规则:确定性命中即 resolved;命中多个不同 Concept 则 ambiguous,
留给后续级别/人工(阶段 1 不调 LLM)。
"""
from __future__ import annotations

from app.agent.concept_registry import ConceptRegistry, get_concept_registry
from app.agent.orchestrator import AgentNode, ServiceRegistry
from app.contracts.agent_state import AgentState, ConceptState, Intent, StateUpdate
from app.contracts.concept import ConceptCandidate, RawTag
from app.core import db
from app.core.cache import CacheKeys, get_cache

# 确认阈值与可自动确认的确定性级别(§7.3:trgm/vector 只出候选,不自动映射)
RESOLVE_THRESHOLD = 0.9
AUTO_RESOLVE_SOURCES = ("exact", "alias", "historical")


class ConceptCandidateRecall:
    """候选概念召回(五级确定性召回)。

    前三级(exact/alias/historical)为可自动确认的确定性级别;
    第四级 pg_trgm、第五级 Concept Vector 只产出候选(§7.3:向量用于候选召回,
    不直接形成最终映射),是否链接由第六级 LLM 消歧(模块 18)或治理决定。
    """

    def __init__(self, registry: ConceptRegistry | None = None) -> None:
        self._registry = registry or get_concept_registry()

    async def recall(self, text: str, *, max_level: int = 5) -> list[ConceptCandidate]:
        """对单个表达做候选召回,按分数降序。

        max_level: 最多走到第几级(阶段 1 链路传 3,阶段 2 起传 5)。
        命中前三级即返回(确定性短路);否则继续第四/五级补充候选。
        """
        normalized = RawTag.normalize(text)
        concepts = await self._registry.load_concepts()
        candidates: list[ConceptCandidate] = []

        # 第一级:Canonical Name Exact
        for c in concepts.values():
            if c.canonical_name.lower() == normalized:
                candidates.append(ConceptCandidate(
                    concept_id=c.concept_id, candidate_source="exact",
                    candidate_score=1.0, matched_text=text,
                    canonical_name=c.canonical_name,
                ))

        # 第二级:Alias Exact
        if not candidates:
            aliases = await self._registry.load_aliases()
            cid = aliases.get(normalized)
            if cid and cid in concepts:
                candidates.append(ConceptCandidate(
                    concept_id=cid, candidate_source="alias",
                    candidate_score=0.98, matched_text=text,
                    canonical_name=concepts[cid].canonical_name,
                ))

        # 第三级:RawTag Historical Mapping(已审核的相同 RawTag 映射,直接复用)
        if not candidates:
            tag = await self._registry.get_raw_tag_by_text(normalized)
            if tag:
                mappings = await self._registry.load_tag_mappings()
                for m in mappings.get(tag.tag_id, []):
                    if m.concept_id in concepts:
                        candidates.append(ConceptCandidate(
                            concept_id=m.concept_id, candidate_source="historical",
                            candidate_score=min(0.97, m.confidence), matched_text=text,
                            canonical_name=concepts[m.concept_id].canonical_name,
                        ))

        if candidates or max_level < 4:
            candidates.sort(key=lambda c: c.candidate_score, reverse=True)
            return candidates

        # 第四级:pg_trgm Fuzzy Recall(§7.3)——分数上限 0.89,不进入自动确认区
        rows = await db.fetch(
            "SELECT concept_id, canonical_name,"
            "       greatest(similarity(canonical_name, $1), 0) AS sim"
            " FROM agent.concepts"
            " WHERE status IN ('seed','active') AND canonical_name % $1"
            " ORDER BY sim DESC LIMIT 5",
            text,
        )
        for r in rows:
            candidates.append(ConceptCandidate(
                concept_id=r["concept_id"], candidate_source="pg_trgm",
                candidate_score=round(min(0.89, float(r["sim"]) * 0.95), 4),
                matched_text=text, canonical_name=r["canonical_name"],
            ))

        # 第五级:Concept Vector Recall(§7.3)——只召回候选,不直接形成映射
        if max_level >= 5:
            vector_hits = await self._vector_recall(text, concepts)
            candidates.extend(vector_hits)

        candidates.sort(key=lambda c: c.candidate_score, reverse=True)
        return candidates

    async def _vector_recall(self, text: str, concepts: dict,
                             top_n: int = 5, min_score: float = 0.25) -> list[ConceptCandidate]:
        """用 Concept 独立向量空间(1024 维)做候选召回。分数上限 0.85。"""
        from app.core.embedding_client import cosine_similarity, get_concept_embedding
        emb = get_concept_embedding()
        query_vec = await emb.embed_query(text)
        rows = await db.fetch(
            "SELECT concept_id, embedding FROM agent.concepts"
            " WHERE status IN ('seed','active') AND embedding IS NOT NULL",
        )
        hits: list[ConceptCandidate] = []
        for r in rows:
            cid = r["concept_id"]
            if cid not in concepts:
                continue
            vec = r["embedding"]
            if isinstance(vec, str):  # asyncpg 默认把 vector 读成字符串字面量
                vec = [float(x) for x in vec.strip("[]").split(",")]
            score = cosine_similarity(query_vec, list(vec))
            if score >= min_score:
                hits.append(ConceptCandidate(
                    concept_id=cid, candidate_source="vector",
                    candidate_score=round(min(0.85, score * 0.9), 4),
                    matched_text=text, canonical_name=concepts[cid].canonical_name,
                ))
        hits.sort(key=lambda c: c.candidate_score, reverse=True)
        return hits[:top_n]


class QueryConceptLinker:
    """查询侧概念链接器:把 UnderstandingState 的各类表达对齐到 Canonical Concept。"""

    def __init__(self, recall: ConceptCandidateRecall | None = None) -> None:
        self._recall = recall or ConceptCandidateRecall()

    async def link(self, terms: list[str], *, query: str = "") -> ConceptState:
        """对一组表达做概念对齐,输出 ConceptState(§7.6 输出结构)。"""
        state = ConceptState()
        seen: set[str] = set()
        for term in terms:
            term = term.strip()
            if not term or RawTag.normalize(term) in seen:
                continue
            seen.add(RawTag.normalize(term))

            # query→concept 短缓存(§14.4)
            cache_key = CacheKeys.QUERY_CONCEPT.format(query=f"{term}")
            cached = await get_cache().get(cache_key)
            if cached is not None:
                candidates = cached
            else:
                candidates = await self._recall.recall(term)
                await get_cache().set(cache_key, candidates, ttl_seconds=300)

            for c in candidates:
                state.candidate_concepts.append(c.model_dump())
            state.concept_link_trace.append({
                "term": term,
                "candidates": [c.model_dump() for c in candidates],
                "levels_tried": ["exact", "alias", "historical"],
            })

            # 确认规则:只有确定性级别(exact/alias/historical)可自动 resolved;
            # pg_trgm/vector 候选保留待第六级消歧(模块 18);多概念歧义标记
            top = [c for c in candidates if c.candidate_score >= RESOLVE_THRESHOLD
                   and c.candidate_source in AUTO_RESOLVE_SOURCES]
            distinct = {c.concept_id for c in top}
            if len(distinct) == 1:
                c = top[0]
                if c.concept_id not in {r["concept_id"] for r in state.resolved_concepts}:
                    state.resolved_concepts.append({
                        "concept_id": c.concept_id,
                        "canonical_name": c.canonical_name,
                        "matched_text": term,
                        "source": c.candidate_source,
                        "confidence": c.candidate_score,
                    })
            elif len(distinct) > 1:
                state.ambiguous = True
        return state


class ConceptLinkerNode(AgentNode):
    """概念链接节点。仅 find_person 执行;结果落 ConceptState 并写 query_concept_logs。"""

    name = "ConceptLinkerNode"
    timeout_ms = 10000
    on_error = "degrade"

    async def execute(self, state: AgentState, services: ServiceRegistry) -> StateUpdate:
        if state.intent.intent != Intent.FIND_PERSON:
            return StateUpdate()
        u = state.understanding
        # 链接对象:显式词项优先,然后系统/对象/职责线索/症状(§7.6)
        terms = list(u.explicit_terms) + [
            t for t in (u.mentioned_systems + u.objects + u.duty_clues + u.symptoms)
            if t not in u.explicit_terms
        ]
        linker = services.get("concept_linker") if "concept_linker" in services.services else QueryConceptLinker()
        query = state.request.normalized_query or state.request.original_query
        concept_state = await linker.link(terms, query=query)

        # 查询概念日志(§7.6 评测与 trace 串联);失败不阻断主链
        try:
            await db.execute(
                "INSERT INTO agent.query_concept_logs(trace_id, query, link_trace, resolved_concepts)"
                " VALUES($1,$2,$3,$4)",
                state.trace.trace_id, query,
                _json([t for t in concept_state.concept_link_trace]),
                _json(concept_state.resolved_concepts),
            )
        except Exception:  # noqa: BLE001
            pass
        return StateUpdate(concept=concept_state)


def _json(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, default=str)
