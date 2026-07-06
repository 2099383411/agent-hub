"""一键接入 API"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.onboard_service import OnboardService
from app.services.agent_service import AgentService
from app.schemas.common import ApiResponse
from app.utils.security import verify_onboard_token
from app.config import get_public_url

router = APIRouter(prefix="/api/v1/onboard", tags=["onboard"])


@router.get("/claim")
async def claim_token_get(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """一键接入：返回 bash 脚本（使用中台对外地址，而非 request hostname）"""
    hub_addr = get_public_url()
    service = OnboardService(db)
    script = await service.generate_script(token, hub_addr)
    if not script:
        raise HTTPException(status_code=401, detail="token 无效或已过期")
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(script, media_type="text/plain")


@router.post("/claim")
async def claim_token_post(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """消耗 token，返回 AppID 和 AppSecret"""
    service = OnboardService(db)
    result = await service.claim_token(token)
    if not result:
        raise HTTPException(status_code=401, detail="token 无效或已过期")
    # 重新生成 app_secret
    from app.utils.security import generate_app_credentials
    app_id, app_secret = generate_app_credentials()
    agent_service = AgentService(db)
    agent = await agent_service.get_agent_by_app_id(result["app_id"])
    if agent:
        agent.app_id = app_id
        from app.utils.security import hash_password
        agent.app_secret_hash = hash_password(app_secret)
        await db.commit()
        result["app_id"] = app_id
        result["app_secret"] = app_secret
    return ApiResponse(data=result)
