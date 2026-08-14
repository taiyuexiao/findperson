"""TST-01 — 内容接口单元测试（创建 / 编辑 / 提交 / 审核 / 删除）"""
from helpers import auth


def test_create_content(http, temp_user):
    token, _, _ = temp_user
    r = http(lambda c: c.post("/api/v1/contents", json={
        "title": "测试内容标题", "summary": "测试摘要",
        "tags": ["测试"], "body": "正文", "status": "草稿",
    }, headers=auth(token)))
    assert r.status_code == 201
    body = r.json()
    assert body["id"].startswith("C")
    assert body["status"] == "草稿"
    assert body["ownerId"]


def test_create_and_get_content(http, temp_user):
    token, _, _ = temp_user
    cid = http(lambda c: c.post("/api/v1/contents", json={
        "title": "详情测试", "summary": "摘要", "body": "正文",
    }, headers=auth(token))).json()["id"]
    r = http(lambda c: c.get(f"/api/v1/contents/{cid}"))
    assert r.status_code == 200
    assert r.json()["id"] == cid


def test_update_content(http, temp_user):
    token, _, _ = temp_user
    cid = http(lambda c: c.post("/api/v1/contents", json={
        "title": "原标题", "summary": "摘要",
    }, headers=auth(token))).json()["id"]
    r = http(lambda c: c.put(f"/api/v1/contents/{cid}", json={
        "title": "改后标题", "summary": "改后摘要",
    }, headers=auth(token)))
    assert r.status_code == 200
    assert r.json()["title"] == "改后标题"


def test_submit_and_audit_approve(http, temp_user, admin):
    token, _, _ = temp_user
    cid = http(lambda c: c.post("/api/v1/contents", json={
        "title": "待发布", "summary": "摘要",
    }, headers=auth(token))).json()["id"]
    # 提交审核
    r_sub = http(lambda c: c.post(f"/api/v1/contents/{cid}/submit", headers=auth(token)))
    assert r_sub.status_code == 200
    assert r_sub.json()["status"] == "待审核"
    # admin 审核通过 → 已发布
    r_aud = http(lambda c: c.post(f"/api/v1/contents/{cid}/audit", json={
        "action": "approve", "reason": "合格",
    }, headers=auth(admin["token"])))
    assert r_aud.status_code == 200
    assert r_aud.json()["status"] == "已发布"


def test_audit_reject(http, temp_user, admin):
    token, _, _ = temp_user
    cid = http(lambda c: c.post("/api/v1/contents", json={
        "title": "待驳回", "summary": "摘要",
    }, headers=auth(token))).json()["id"]
    http(lambda c: c.post(f"/api/v1/contents/{cid}/submit", headers=auth(token)))
    r = http(lambda c: c.post(f"/api/v1/contents/{cid}/audit", json={
        "action": "reject", "reason": "不合格",
    }, headers=auth(admin["token"])))
    assert r.status_code == 200
    assert r.json()["status"] == "已驳回"


def test_delete_content_soft(http, temp_user):
    token, _, _ = temp_user
    cid = http(lambda c: c.post("/api/v1/contents", json={
        "title": "待删除", "summary": "摘要",
    }, headers=auth(token))).json()["id"]
    r = http(lambda c: c.delete(f"/api/v1/contents/{cid}", headers=auth(token)))
    assert r.status_code == 200
    # 软删除后详情 404
    r2 = http(lambda c: c.get(f"/api/v1/contents/{cid}"))
    assert r2.status_code == 404


def test_list_contents(http):
    r = http(lambda c: c.get("/api/v1/contents"))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_content_requires_auth(http):
    r = http(lambda c: c.post("/api/v1/contents", json={
        "title": "无鉴权", "summary": "摘要",
    }))
    assert r.status_code == 401
