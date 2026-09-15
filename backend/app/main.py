"""首问责任平台 — FastAPI 入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .api.v1 import auth, me, people, contents, reviews, admin, departments, sessions
from .api.v1 import agui_proxy
from .middleware.auth import AuthMiddleware

app = FastAPI(
    title="首问责任平台 API",
    description="First-Responsibility Platform Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# JWT 认证中间件(integration 分支补全:注入 request.state.user_id/user_role)
app.add_middleware(AuthMiddleware)

# CORS — 开发模式：允许任意 localhost 端口
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(me.router, prefix="/api/v1")
app.include_router(people.router, prefix="/api/v1")
app.include_router(contents.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(agui_proxy.router, prefix="/api/v1")  # AGUI 事件代理 → agent-service


@app.get("/")
def root():
    return {"service": "首问责任平台", "version": "0.1.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
