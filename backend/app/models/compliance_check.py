"""合规检查模型"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ComplianceCheck(Base):
    __tablename__ = "compliance_check"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent.id"), index=True)
    status: Mapped[str] = mapped_column(String(16))  # compliant / non_compliant
    missing_skills: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    checked_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    agent = relationship("Agent", back_populates="compliance_checks")
