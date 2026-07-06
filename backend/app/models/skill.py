"""Skill 模型"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class SkillScope(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class SecurityStatus(str, enum.Enum):
    PENDING = "pending"
    SCANNING = "scanning"
    PASSED = "passed"
    WARNING = "warning"
    BLOCKED = "blocked"


class RiskLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class SkillSource(str, enum.Enum):
    LOCAL = "local"
    CLAWHUB = "clawhub"
    SKILLHUB = "skillhub"
    UPLOAD = "upload"


class Skill(Base):
    __tablename__ = "skill"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    scope: Mapped[str] = mapped_column(String(16), default=SkillScope.PRIVATE.value, index=True)
    source: Mapped[str] = mapped_column(String(32), default=SkillSource.LOCAL.value)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    security_status: Mapped[str] = mapped_column(String(16), default=SecurityStatus.PENDING.value)
    security_risk_level: Mapped[str] = mapped_column(String(16), default=RiskLevel.NONE.value)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_mandatory: Mapped[int] = mapped_column(default=0)
    is_blocked: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[int] = mapped_column(default=1)
    is_deleted: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    agent_skills = relationship("AgentSkill", back_populates="skill", lazy="selectin")
    security_scans = relationship("SecurityScan", back_populates="skill", lazy="selectin")
