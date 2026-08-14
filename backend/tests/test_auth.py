"""TST-01 — 认证接口单元测试（登录 / 注册 / 改密）"""
import uuid

from helpers import auth, purge_user


def test_login_success(http):
    r = http(lambda c: c.post("/api/v1/auth/login", json={
        "account": "p0001", "password": "swzr2026",
    }))
    assert r.status_code == 200
    body = r.json()
    assert body["token"]
    assert body["user"]["id"] == "P0001"
    assert body["user"]["systemRole"] == "管理员"


def test_login_wrong_password(http):
    r = http(lambda c: c.post("/api/v1/auth/login", json={
        "account": "p0001", "password": "wrong-password",
    }))
    assert r.status_code == 401


def test_login_nonexistent_account(http):
    r = http(lambda c: c.post("/api/v1/auth/login", json={
        "account": "no_such_user", "password": "whatever123",
    }))
    assert r.status_code == 401


def test_register_creates_user(http):
    account = f"pytest_reg_{uuid.uuid4().hex[:8]}"
    r = http(lambda c: c.post("/api/v1/auth/register", json={
        "account": account, "name": "测试注册用户", "password": "test123456",
    }))
    assert r.status_code == 200
    body = r.json()
    assert body["id"] and body["account"] == account
    purge_user(body["id"])


def test_register_duplicate_account(http):
    # 用 admin 账号（已存在）再次注册应返回 400
    r = http(lambda c: c.post("/api/v1/auth/register", json={
        "account": "p0001", "name": "重复", "password": "test123456",
    }))
    assert r.status_code == 400


def test_change_password_full_cycle(http, temp_user):
    token, user_id, account = temp_user
    # 改密
    r = http(lambda c: c.post("/api/v1/auth/change-password", json={
        "old_password": "test123456", "new_password": "newpass888",
    }, headers=auth(token)))
    assert r.status_code == 200
    # 旧密码登录失败
    r_old = http(lambda c: c.post("/api/v1/auth/login", json={
        "account": account, "password": "test123456",
    }))
    assert r_old.status_code == 401
    # 新密码登录成功
    r_new = http(lambda c: c.post("/api/v1/auth/login", json={
        "account": account, "password": "newpass888",
    }))
    assert r_new.status_code == 200


def test_change_password_wrong_old(http, temp_user):
    token, _, _ = temp_user
    r = http(lambda c: c.post("/api/v1/auth/change-password", json={
        "old_password": "wrong-old", "new_password": "newpass888",
    }, headers=auth(token)))
    assert r.status_code == 400
