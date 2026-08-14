"""JWT 鉴权中间件：解析 Authorization 头，注入 request.state.user_id / user_role"""
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.security import decode_token

# 无需鉴权的路径（前缀匹配）
_PUBLIC_PREFIX = ("/health", "/docs", "/redoc", "/openapi.json")
_PUBLIC_EXACT = {"/", "/api/v1/auth/login", "/api/v1/auth/register"}


class AuthMiddleware(BaseHTTPMiddleware):
    """从 Authorization: Bearer <token> 解析用户身份，写入 request.state。

    get_current_user / require_admin 依赖这里注入的 user_id / user_role。
    """

    async def dispatch(self, request, call_next):
        path = request.url.path
        is_public = path in _PUBLIC_EXACT or path.startswith(_PUBLIC_PREFIX)
        if not is_public:
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                try:
                    payload = decode_token(auth[7:])
                    request.state.user_id = payload.get("sub")
                    request.state.user_role = payload.get("role", "")
                except Exception:
                    # 解析失败时不注入，由 get_current_user 抛出 401
                    pass
        return await call_next(request)
