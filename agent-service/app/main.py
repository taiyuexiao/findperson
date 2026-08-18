"""FastAPI 入口。

当前(模块 01)仅提供 /health;后续模块依次挂载 /agent/chat(SSE)等路由。
"""
import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.agui.router import router as agui_router
from app.api_agent import router as agent_router
from app.config import get_settings
from app.core.db import close_pool, init_pool

app = FastAPI(title="首问责任平台 Agent-OKF-RAG V1", version="0.2.0")

# CORS:前端 Vite dev(localhost/127.0.0.1:5173-5174)跨域调 AGUI 必须放行
_cors = os.getenv(
    "AGENT_CORS_ORIGINS",
    "http://localhost:5173,http://localhost:5174,"
    "http://127.0.0.1:5173,http://127.0.0.1:5174",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)
app.include_router(agui_router)


@app.on_event("startup")
async def _startup() -> None:
    """应用启动:初始化 DB 连接池 + publish_events 消费轮询。"""
    await init_pool()
    from app.rag.event_consumer import run_event_consumer
    app.state.publish_event_stop = asyncio.Event()
    app.state.publish_event_task = asyncio.create_task(
        run_event_consumer(app.state.publish_event_stop))


@app.on_event("shutdown")
async def _shutdown() -> None:
    if getattr(app.state, "publish_event_stop", None):
        app.state.publish_event_stop.set()
    if getattr(app.state, "publish_event_task", None):
        app.state.publish_event_task.cancel()
    await close_pool()


@app.get("/metrics")
async def prometheus_metrics() -> Response:
    """Prometheus 文本格式指标(§15.2)。"""
    from app.core.observability import get_metrics
    return Response(content=get_metrics().render_prometheus(), media_type="text/plain")


@app.get("/health")
async def health() -> dict:
    """健康检查。"""
    settings = get_settings()
    return {
        "status": "ok",
        "service": "shouwenzeren-agent",
        "version": "0.1.0",
        "llm_mock": settings.llm_use_mock,
        "embedding_mock": settings.embedding_use_mock,
    }
