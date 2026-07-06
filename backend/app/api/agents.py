"""Agent 管理 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.agent_service import AgentService
from app.services.audit_service import AuditService
from app.schemas.agent import AgentCreate, AgentOut, AgentOnboardResponse, AgentDetailOut
from app.schemas.common import ApiResponse
from app.api.auth import verify_admin

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = AgentService(db)
    agents = await service.list_agents()
    return ApiResponse(data=[AgentOut.model_validate(a) for a in agents])


@router.post("")
async def create_agent(
    data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = AgentService(db)
    agent, app_secret, onboard_token, onboard_cmd = await service.create_agent(data)
    await AuditService(db).log("agent.create", "admin", agent.agent_name, f"type={agent.agent_type}")
    return ApiResponse(data=AgentOnboardResponse(
        agent=AgentOut.model_validate(agent),
        app_id=agent.app_id,
        app_secret=app_secret,
        onboard_command=onboard_cmd,
        onboard_token=onboard_token,
    ))


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = AgentService(db)
    agent = await service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    skills = await service.get_agent_installed_skills(agent_id)
    from app.services.compliance_service import ComplianceService
    compliance = await ComplianceService(db).check_compliance(agent_id)
    return ApiResponse(data=AgentDetailOut(
        **AgentOut.model_validate(agent).model_dump(),
        installed_skills=skills,
        compliance_status=compliance.status,
        missing_mandatory=compliance.missing_mandatory,
    ))


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = AgentService(db)
    agent = await service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    agent_name = agent.agent_name
    ok = await service.delete_agent(agent_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    await AuditService(db).log("agent.delete", "admin", agent_name)
    return ApiResponse(data={"deleted": True})


@router.post("/{agent_id}/regenerate-credential")
async def regenerate_credential(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    from app.utils.security import generate_app_credentials, hash_password
    service = AgentService(db)
    agent = await service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    app_id, app_secret = generate_app_credentials()
    agent.app_id = app_id
    agent.app_secret_hash = hash_password(app_secret)
    await db.commit()
    await AuditService(db).log("agent.regenerate", "admin", agent.agent_name)
    return ApiResponse(data={"app_id": app_id, "app_secret": app_secret})


@router.post("/{agent_id}/refresh-token")
async def refresh_onboard_token(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    """重新生成 Agent 的 onboard token（过期后刷新用）"""
    from app.services.agent_service import AgentService
    service = AgentService(db)
    try:
        onboard_token, onboard_cmd = await service.refresh_onboard_token(agent_id)
        await AuditService(db).log("agent.refresh_token", "admin", agent_id)
        return ApiResponse(data={
            "onboard_token": onboard_token,
            "onboard_command": onboard_cmd,
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
