"""Agent 模型"""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class AgentType(str, enum.Enum):
    QWENPAW = "qwenpaw"
    EVOLCLAW = "evolclaw"
    HERMES = "hermes"
    CLAUDE_CODE = "claude_code"
    CODEX = "codex"
    GENERIC = "generic"


class AgentStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class Agent(Base):
    __tablename__ = "agent"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    agent_type: Mapped[str] = mapped_column(String(32), default=AgentType.GENERIC.value, index=True)
    app_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    app_secret_hash: Mapped[str] = mapped_column(String(128))
    onboard_token: Mapped[str | None] = mapped_column(String(128), nullable=True)
    onboard_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default=AgentStatus.OFFLINE.value)
    host_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    agent_skills = relationship("AgentSkill", back_populates="agent", lazy="selectin")
    compliance_checks = relationship("ComplianceCheck", back_populates="agent", lazy="selectin")
    tools = relationship("Tool", back_populates="agent", lazy="selectin")
