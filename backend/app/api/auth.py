"""认证相关路由"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.utils.security import hash_password, verify_password, create_jwt_token, decode_jwt_token
from app.models.system_config import SystemConfig
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
security_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """管理员登录"""
    # 首次登录：初始化密码
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.config_key == "admin_password")
    )
    config = result.scalar_one_or_none()

    if not config:
        # 首次初始化
        config = SystemConfig(
            config_key="admin_password",
            config_value=hash_password(settings.admin_password),
            description="管理员密码哈希",
        )
        db.add(config)
        await db.commit()

    if not verify_password(req.password, config.config_value):
        raise HTTPException(status_code=401, detail="密码错误")

    token = create_jwt_token({"sub": "admin", "role": "admin"})
    return LoginResponse(
        token=token,
        expires_in=settings.jwt_expire_minutes * 60,
    )


async def verify_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    """验证管理员 JWT"""
    if not credentials:
        raise HTTPException(status_code=401, detail="需要登录")
    payload = decode_jwt_token(credentials.credentials)
    if not payload or payload.get("sub") != "admin":
        raise HTTPException(status_code=401, detail="无效的 token")
    return payload
