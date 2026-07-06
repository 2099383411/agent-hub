"""Agent-Skill 关联模型"""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AgentSkillStatus:
    PENDING = "pending"
    INSTALLED = "installed"
    OUTDATED = "outdated"
    REJECTED = "rejected"


class AgentSkill(Base):
    __tablename__ = "agent_skill"
    __table_args__ = (UniqueConstraint("agent_id", "skill_id", name="uk_agent_skill"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent.id"), index=True)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skill.id"), index=True)
    status: Mapped[str] = mapped_column(String(16), default=AgentSkillStatus.PENDING)
    installed_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    installed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    agent = relationship("Agent", back_populates="agent_skills")
    skill = relationship("Skill", back_populates="agent_skills")
