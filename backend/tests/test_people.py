"""TST-01 — 人员/名片库接口单元测试"""
from helpers import auth


def test_list_people_public(http):
    r = http(lambda c: c.get("/api/v1/people"))
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # 返回项含关键字段
    assert "id" in data[0] and "name" in data[0]


def test_list_people_search_by_account(http):
    r = http(lambda c: c.get("/api/v1/people", params={"keyword": "p0001"}))
    assert r.status_code == 200
    data = r.json()
    assert any(u["account"] == "p0001" for u in data)


def test_get_person(http):
    r = http(lambda c: c.get("/api/v1/people/P0001"))
    assert r.status_code == 200
    assert r.json()["id"] == "P0001"
    assert r.json()["account"] == "p0001"


def test_get_person_not_found(http):
    r = http(lambda c: c.get("/api/v1/people/NO_SUCH_PERSON"))
    assert r.status_code == 404


def test_update_person(http, temp_user):
    token, user_id, _ = temp_user
    r = http(lambda c: c.patch(
        f"/api/v1/people/{user_id}",
        json={"role": "测试角色", "phone": "13800000000"},
    ))
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "测试角色"
    assert body["phone"] == "13800000000"


def test_get_person_reviews(http):
    r = http(lambda c: c.get("/api/v1/people/P0001/reviews"))
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body
