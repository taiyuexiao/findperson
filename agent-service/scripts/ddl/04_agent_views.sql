-- 04_agent_views.sql —— PersonConceptEvidence 查询视图(V1.2 §9.2 / §17)
-- person_tags × tag_concept_map 的实时连接:RawTag/Concept 更新后证据天然增量刷新。
CREATE OR REPLACE VIEW agent.person_concept_evidence AS
SELECT
    pt.person_id,
    m.concept_id,
    'self_declared_scope'::text AS relation_type,
    'explicit_self_tag'::text AS evidence_type,
    'raw_tag'::text AS source_type,
    pt.tag_id AS source_id,
    rt.text AS source_raw_tag,
    m.confidence,
    CASE WHEN pt.is_active THEN 'active' ELSE 'inactive' END AS verification_status
FROM agent.person_tags pt
JOIN agent.tag_concept_map m ON m.tag_id = pt.tag_id
JOIN agent.raw_tags rt ON rt.tag_id = pt.tag_id
WHERE m.review_status IN ('auto_approved', 'approved');
