"""Agent Hub 配置管理"""

import os
import socket
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用
    app_name: str = "Agent Hub"
    app_version: str = "2.3.0"
    debug: bool = False

    # 服务端口
    host: str = "0.0.0.0"
    port: int = 8200

    # 数据库
    database_url: str = "sqlite+aiosqlite:///app/data/agent_hub.db"

    # 密钥
    secret_key: str = "change-me-in-production"
    admin_password: str = "admin123"

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 小时

    # 技能存储
    skills_dir: str = "/app/skills/installed"
    staging_dir: str = "/app/skills/staging"
    max_skill_size_mb: int = 10

    # 心跳超时（分钟）
    heartbeat_timeout_minutes: int = 5

    # 一键接入 token 有效期（分钟）
    onboard_token_expire_minutes: int = 5

    # 中台公网地址（Agent 用来连接中台的地址，不配置则自动检测）
    # 例如：http://192.168.1.100:8200
    public_url: str = ""

    # CORS
    cors_origins: list[str] = ["*"]

    model_config = {"env_file": ".env", "env_prefix": "HUB_"}


settings = Settings()


def get_public_url() -> str:
    """获取中台对外可访问地址

    优先级：配置 > 环境变量 HUB_PUBLIC_URL > 自动检测 IP > 兜底
    """
    if settings.public_url:
        return settings.public_url.rstrip("/")

    env_url = os.environ.get("HUB_PUBLIC_URL")
    if env_url:
        return env_url.rstrip("/")

    # 自动检测本机 IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return f"http://{ip}:8200"
    except Exception:
        pass

    # 尝试主机名
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return f"http://{ip}:8200"
    except Exception:
        return "http://localhost:8200"
