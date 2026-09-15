"""模块 17:第四级 pg_trgm + 第五级 Concept Vector 召回测试。"""
import pytest
import pytest_asyncio

from app.agent.concept_linker import ConceptCandidateRecall, QueryConceptLinker
from app.core.db import close_pool, health, init_pool

pytestmark = pytest.mark.asyncio(loop_scope="module")


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def pool():
    try:
        await init_pool()
    except Exception:
        pytest.skip("数据库不可用")
    if not await health():
        pytest.skip()
    yield
    await close_pool()


async def test_trgm_recall(pool) -> None:
    """第四级:pg_trgm 召回名称近似概念(§7.3),分数不进入自动确认区。"""
    recall = ConceptCandidateRecall()
    candidates = await recall.recall("数据治理工作")
    assert candidates, "trgm 应召回近似概念"
    trgm_hits = [c for c in candidates if c.candidate_source == "pg_trgm"]
    assert trgm_hits, "应包含 pg_trgm 召回"
    assert "数据治理" in trgm_hits[0].canonical_name
    assert trgm_hits[0].candidate_score < 0.9  # trgm 只出候选,不自动映射(§7.3)


async def test_vector_recall(pool) -> None:
    """第五级:Concept Vector 召回(独立 1024 维空间),只出候选(§7.3/§10.8)。"""
    recall = ConceptCandidateRecall()
    candidates = await recall.recall("数据仓库建模与指标管理")
    vector_hits = [c for c in candidates if c.candidate_source == "vector"]
    assert vector_hits, "向量应召回相关概念"
    assert all(c.candidate_score <= 0.85 for c in vector_hits)  # 上限封顶
    # 召回的概念应与数据领域相关
    names = [c.canonical_name for c in vector_hits]
    assert any("数据" in n for n in names)


async def test_deterministic_short_circuit(pool) -> None:
    """前三级命中即短路,不走 trgm/vector(§7.3 顺序)。"""
    recall = ConceptCandidateRecall()
    candidates = await recall.recall("数据治理")
    assert candidates[0].candidate_source == "exact"
    assert all(c.candidate_source in ("exact", "alias", "historical") for c in candidates)


async def test_trgm_vector_not_auto_resolved(pool) -> None:
    """链接器确认规则:trgm/vector 候选不自动 resolved(非法映射防线)。"""
    linker = QueryConceptLinker()
    state = await linker.link(["数据治理工作"], query="谁负责数据治理工作?")
    # trgm/vector 命中的概念不得自动进 resolved_concepts
    sources = {c["candidate_source"] for c in state.candidate_concepts}
    if sources <= {"pg_trgm", "vector"}:
        assert state.resolved_concepts == []
    else:
        # 若同时有确定性命中(不太可能),resolved 只能来自确定性级别
        assert all(r["source"] in ("exact", "alias", "historical")
                   for r in state.resolved_concepts)


async def test_max_level_3_compatible(pool) -> None:
    """max_level=3 时行为与阶段 1 完全一致(向后兼容)。"""
    recall = ConceptCandidateRecall()
    candidates = await recall.recall("数据治理工作", max_level=3)
    assert candidates == []  # 前三级无命中即空,不走 trgm
