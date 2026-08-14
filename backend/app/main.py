"""首问责任平台 — FastAPI 入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .api.v1 import auth, me, people, contents, reviews, admin, departments, sessions
from .api.agui import sessions as agui_sessions, messages as agui_messages, events as agui_events
from .middleware.auth import AuthMiddleware
from .middleware.audit import AuditMiddleware
from .core.scheduler import lifespan

app = FastAPI(
    title="首问责任平台 API",
    description="First-Responsibility Platform Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — 开发模式：允许任意 localhost 端口
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 审计日志中间件：在 Auth 之前 add，使其在 Auth 之后（内层）执行，依赖 Auth 注入的 user_id
app.add_middleware(AuditMiddleware)

# JWT 鉴权中间件（解析 token → request.state.user_id / user_role）
app.add_middleware(AuthMiddleware)

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(me.router, prefix="/api/v1")
app.include_router(people.router, prefix="/api/v1")
app.include_router(contents.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")

# AGUI 收口路由（问答/反馈/会话，前缀 /api/agui，与 /api/v1 分开）
app.include_router(agui_sessions.router, prefix="/api/agui")
app.include_router(agui_messages.router, prefix="/api/agui")
app.include_router(agui_events.router, prefix="/api/agui")


@app.get("/")
def root():
    return {"service": "首问责任平台", "version": "0.1.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
