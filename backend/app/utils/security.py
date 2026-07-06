"""安全工具：密码哈希、JWT、签名、凭证生成"""

import hashlib
import hmac
import uuid
import time
import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_jwt_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def generate_app_credentials() -> tuple[str, str]:
    """生成 AppID 和 AppSecret"""
    app_id = f"qw_{uuid.uuid4().hex[:12]}"
    app_secret = secrets.token_hex(24)
    return app_id, app_secret


def generate_onboard_token() -> tuple[str, datetime]:
    """生成一次性 onboard token"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.onboard_token_expire_minutes)
    return token, expires_at


def verify_mcp_signature(app_id: str, timestamp: str, nonce: str, signature: str, app_secret: str) -> bool:
    """验证 MCP 握手签名"""
    try:
        ts = int(timestamp)
        now = time.time()
        if abs(now - ts) > 300:  # ±5 分钟
            return False
    except (ValueError, TypeError):
        return False

    message = f"{app_id}\nGET\n/mcp/sse\n{timestamp}\n{nonce}"
    expected = hmac.new(app_secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def generate_mcp_signature(app_id: str, app_secret: str) -> tuple[str, str, str]:
    """生成 MCP 签名（用于测试/客户端）"""
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(8)
    message = f"{app_id}\nGET\n/mcp/sse\n{timestamp}\n{nonce}"
    signature = hmac.new(app_secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return timestamp, nonce, signature


def verify_onboard_token(token: str, stored_token: str | None, expires_at: datetime | None) -> bool:
    """验证 onboard token"""
    if not stored_token or not expires_at:
        return False
    if not hmac.compare_digest(token, stored_token):
        return False
    if datetime.now(timezone.utc) > expires_at:
        return False
    return True
