"""pytest 共享 fixture —— TST-01 核心接口单元测试 + TST-02 验收路径集成测试

技术选型：httpx 的 ASGITransport 直接驱动 ASGI app（无需起服务器），
用标准库 asyncio 跑 async 逻辑（不引入 pytest-asyncio），连真实开发库 swzr-pg。

数据隔离：写操作用临时账号 / 内容（唯一后缀），在 teardown 通过 helpers 物理清理。
"""
import asyncio
import sys
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import httpx
import pytest

from app.main import app
from helpers import auth, purge_user  # noqa: E402

BASE_URL = "http://testserver"

# seed 账号（P0 种子数据，密码统一 swzr2026；见《开发进度.md》DB-06）
ADMIN_ACCOUNT = "p0001"
ADMIN_PASSWORD = "swzr2026"
USER_ACCOUNT = "p0002"
USER_PASSWORD = "swzr2026"


@pytest.fixture
def http():
    """运行一段 async 逻辑并返回其结果。

    用法（测试函数保持 sync def，业务逻辑写进 async 闭包）：
        def test_list_people(http):
            r = http(lambda c: c.get("/api/v1/people"))
            assert r.status_code == 200
    """
    def run(coro):
        async def _main():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url=BASE_URL) as c:
                return await coro(c)
        return asyncio.run(_main())
    return run


def _login(http, account, password):
    r = http(lambda c: c.post(
        "/api/v1/auth/login",
        json={"account": account, "password": password},
    ))
    assert r.status_code == 200, f"登录 {account} 失败: {r.status_code} {r.text}"
    return r.json()


@pytest.fixture
def admin(http):
    """管理员登录信息（token + user）"""
    return _login(http, ADMIN_ACCOUNT, ADMIN_PASSWORD)


@pytest.fixture
def user(http):
    """普通用户登录信息"""
    return _login(http, USER_ACCOUNT, USER_PASSWORD)


@pytest.fixture
def temp_user(http):
    """注册一个临时普通用户（随机后缀），yield (token, user_id, account)，teardown 清理。"""
    suffix = uuid.uuid4().hex[:8]
    account = f"pytest_{suffix}"
    password = "test123456"
    r = http(lambda c: c.post("/api/v1/auth/register", json={
        "account": account,
        "name": f"测试{suffix}",
        "password": password,
        "system_role": "普通成员",
    }))
    assert r.status_code == 200, f"注册临时用户失败: {r.status_code} {r.text}"
    user_id = r.json()["id"]
    login = _login(http, account, password)
    try:
        yield login["token"], user_id, account
    finally:
        purge_user(user_id)
