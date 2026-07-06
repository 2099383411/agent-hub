"""Agent REST API 兜底 — 不支持 MCP 的 Agent 使用，HMAC 签名鉴权"""

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.services.agent_service import AgentService
from app.services.skill_service import SkillService
from app.services.heartbeat_service import HeartbeatService
from app.services.knowledge_service import KnowledgeService
from app.schemas.heartbeat import HeartbeatRequest, HeartbeatResponse
from app.schemas.skill import SkillListItem
from app.schemas.knowledge import KnowledgeSearchResponse
from app.utils.security import verify_mcp_signature

router = APIRouter(prefix="/api/v1/agent", tags=["agent-fallback"])


async def verify_agent(
    x_agent_appid: str = Header(...),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """验证 Agent 身份（HMAC 签名或 AppSecret 直接认证）"""
    service = AgentService(db)
    agent = await service.get_agent_by_app_id(x_agent_appid)
    if not agent:
        raise HTTPException(status_code=401, detail="无效的 AppID")

    # 从 Authorization header 获取 AppSecret（简化版：Bearer <secret>）
    if authorization and authorization.startswith("Bearer "):
        secret = authorization[7:]
        from app.utils.security import verify_password
        if not verify_password(secret, agent.app_secret_hash):
            raise HTTPException(status_code=401, detail="认证失败")
    else:
        raise HTTPException(status_code=401, detail="需要 Authorization: Bearer <secret>")

    return agent


@router.post("/heartbeat")
async def agent_heartbeat(
    data: HeartbeatRequest,
    db: AsyncSession = Depends(get_db),
    agent=Depends(verify_agent),
):
    """Agent 心跳上报（同 MCP 协议）"""
    service = HeartbeatService(db)
    resp = await service.process_heartbeat(agent.app_id, data)
    return resp


@router.get("/skills")
async def agent_skills(
    db: AsyncSession = Depends(get_db),
    agent=Depends(verify_agent),
):
    """获取 Agent 可见的技能列表"""
    service = SkillService(db)
    skills = await service.list_skills(agent_id=agent.id)
    return {"skills": [s.model_dump() for s in skills], "total": len(skills)}


@router.get("/skills/{name}/download")
async def agent_skill_download(
    name: str,
    db: AsyncSession = Depends(get_db),
    agent=Depends(verify_agent),
):
    """下载技能包"""
    service = SkillService(db)
    pkg = await service.download_skill(name, agent.id)
    if not pkg:
        raise HTTPException(status_code=404, detail="技能不存在或无权限")
    return {
        "skill": pkg.skill.model_dump(),
        "files": [f.model_dump() for f in pkg.files],
    }


@router.get("/knowledge/search")
async def agent_knowledge_search(
    q: str = Query(..., min_length=1),
    category: str = None,
    db: AsyncSession = Depends(get_db),
    agent=Depends(verify_agent),
):
    """搜索知识库"""
    service = KnowledgeService(db)
    resp = await service.search(q, category)
    return resp
