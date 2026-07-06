"""Agent Hub 主应用"""

import os
import sys
import asyncio
from contextlib import asynccontextmanager

# 确保能找到 app 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, init_wal_mode, seed_default_skills, async_session
from app.services.agent_service import AgentService

# API 路由
from app.api import (
    auth_router, agents_router, skills_router,
    security_router, knowledge_router, compliance_router,
    dashboard_router, onboard_router, system_router,
    public_hub_router,
    agent_fallback_router,
    audit_router,
)


async def offline_check_loop():
    """每分钟检查并标记超时离线的 Agent"""
    while True:
        try:
            async with async_session() as db:
                service = AgentService(db)
                await service.mark_offline()
        except Exception:
            pass  # 忽略单次检查异常，下轮继续
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时初始化
    await init_db()
    await init_wal_mode()
    await seed_default_skills()

    # 启动后台离线检查
    task = asyncio.create_task(offline_check_loop())
    print("✅ Agent 离线检查后台任务已启动")

    yield

    # 关闭时清理
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(agents_router)
app.include_router(skills_router)
app.include_router(security_router)
app.include_router(knowledge_router)
app.include_router(compliance_router)
app.include_router(dashboard_router)
app.include_router(onboard_router)
app.include_router(system_router)
app.include_router(public_hub_router)
app.include_router(audit_router)
app.include_router(agent_fallback_router)

# 挂载 MCP SSE 端点
from app.mcp import mcp_app
app.mount("/mcp", mcp_app.http_app(transport="sse"))


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
