"""Agent Hub 主应用"""

import os
import sys
from contextlib import asynccontextmanager

# 确保能找到 app 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db, init_wal_mode
from app.models.system_config import SystemConfig

# API 路由
from app.api import (
    auth_router, agents_router, skills_router,
    security_router, knowledge_router, compliance_router,
    dashboard_router, onboard_router, system_router,
    public_hub_router,
    agent_fallback_router,
    audit_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时初始化
    await init_db()
    await init_wal_mode()
    yield
    # 关闭时清理
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
