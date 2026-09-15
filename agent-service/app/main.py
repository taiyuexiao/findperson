"""FastAPI 入口。

当前(模块 01)仅提供 /health;后续模块依次挂载 /agent/chat(SSE)等路由。
"""
from fastapi import FastAPI
from fastapi.responses import Response

from app.agui.router import router as agui_router
from app.api_agent import router as agent_router
from app.config import get_settings
from app.core.db import close_pool, init_pool

app = FastAPI(title="首问责任平台 Agent-OKF-RAG V1", version="0.2.0")
app.include_router(agent_router)
app.include_router(agui_router)


@app.on_event("startup")
async def _startup() -> None:
    """应用启动:初始化 DB 连接池。"""
    await init_pool()


@app.on_event("shutdown")
async def _shutdown() -> None:
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
