"""TST-02 — 7 条验收路径集成测试

路径映射（后端可测范围）：
  1. 找负责人   → AGUI 问答收口（Agent 未接入时走降级 SSE）
  2. 发布内容   → 创建 → 提交 → 审核通过 → 已发布 + publish_events
  3. 审核       → 驳回（reject）状态流转 + 审核轨迹
  4. 改资料     → PUT /me/profile
  5. 评价       → 打标签 + 标签汇总
  6. 名片库     → 人员列表 + 详情
  7. 统计       → 统计快照 + 管理看板
"""
import uuid

from sqlalchemy import text

from app.core.database import SessionLocal
from helpers import auth


def _count_events(resource_id):
    db = SessionLocal()
    try:
        return db.execute(
            text("SELECT count(*) FROM rag.publish_events WHERE resource_id = :c"),
            {"c": resource_id},
        ).scalar()
    finally:
        db.close()


def test_path_01_find_person(http, temp_user):
    """找负责人：问答收口链路（降级）"""
    token, _, _ = temp_user
    r = http(lambda c: c.post("/api/agui/sessions", headers=auth(token)))
    assert r.status_code == 200
    sid = r.json()["id"]

    r2 = http(lambda c: c.post(f"/api/agui/sessions/{sid}/messages", json={
        "message": {"text": "谁负责公积金提取业务？"},
        "context": {},
    }, headers=auth(token)))
    assert r2.status_code == 200
    sse = r2.text
    assert "run_started" in sse and "run_finished" in sse
    assert "智能问答服务暂未接入" in sse

    # 消息落库
    r3 = http(lambda c: c.get(f"/api/v1/sessions/{sid}/messages", headers=auth(token)))
    assert r3.status_code == 200
    assert r3.json()["total"] >= 1


def test_path_02_publish_content(http, temp_user, admin):
    """发布内容：创建 → 提交 → 审核通过 → 已发布 + 事件信号"""
    token, _, _ = temp_user
    cid = http(lambda c: c.post("/api/v1/contents", json={
        "title": "验收-发布内容", "summary": "验收摘要", "tags": ["验收"],
    }, headers=auth(token))).json()["id"]

    assert _count_events(cid) == 0  # 草稿不触发事件

    http(lambda c: c.post(f"/api/v1/contents/{cid}/submit", headers=auth(token)))
    assert _count_events(cid) == 0  # 提交不触发事件

    r = http(lambda c: c.post(f"/api/v1/contents/{cid}/audit", json={
        "action": "approve", "reason": "验收通过",
    }, headers=auth(admin["token"])))
    assert r.status_code == 200
    assert r.json()["status"] == "已发布"
    assert _count_events(cid) == 1  # 发布触发 content_published


def test_path_03_audit(http, temp_user, admin):
    """审核：驳回流转 + 审核轨迹"""
    token, _, _ = temp_user
    cid = http(lambda c: c.post("/api/v1/contents", json={
        "title": "验收-审核驳回", "summary": "摘要",
    }, headers=auth(token))).json()["id"]
    http(lambda c: c.post(f"/api/v1/contents/{cid}/submit", headers=auth(token)))

    r = http(lambda c: c.post(f"/api/v1/contents/{cid}/audit", json={
        "action": "reject", "reason": "材料不全",
    }, headers=auth(admin["token"])))
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "已驳回"
    assert body["auditTrail"] and body["auditTrail"][-1]["result"] == "rejected"


def test_path_04_update_profile(http, temp_user):
    """改资料：更新自己资料"""
    token, user_id, _ = temp_user
    r = http(lambda c: c.put("/api/v1/me/profile", json={
        "role": "公积金业务经办", "selfPortrait": "负责公积金提取与贷款",
        "phone": "13900000000",
    }, headers=auth(token)))
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == user_id
    assert body["role"] == "公积金业务经办"


def test_path_05_review(http, temp_user):
    """评价：为他人打标签 + 标签汇总"""
    token, _, _ = temp_user
    tag = f"验收标签_{uuid.uuid4().hex[:6]}"
    r = http(lambda c: c.post("/api/v1/reviews", json={
        "personId": "P0002", "tag": tag,
    }, headers=auth(token)))
    assert r.status_code == 201
    assert r.json()["tag"] == tag

    r2 = http(lambda c: c.get("/api/v1/reviews/person/P0002"))
    assert r2.status_code == 200
    assert tag in r2.json()["tags"]


def test_path_06_business_card_library(http):
    """名片库：人员列表 + 详情"""
    r = http(lambda c: c.get("/api/v1/people"))
    assert r.status_code == 200
    assert isinstance(r.json(), list) and len(r.json()) > 0

    r2 = http(lambda c: c.get("/api/v1/people/P0001"))
    assert r2.status_code == 200
    assert r2.json()["id"] == "P0001"


def test_path_07_statistics(http, admin):
    """统计：统计快照 + 管理看板"""
    r = http(lambda c: c.get("/api/v1/admin/statistics/data", headers=auth(admin["token"])))
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    r2 = http(lambda c: c.get("/api/v1/admin/dashboard", headers=auth(admin["token"])))
    assert r2.status_code == 200
    body = r2.json()
    assert body["peopleCount"] >= 0 and body["contentCount"] >= 0
