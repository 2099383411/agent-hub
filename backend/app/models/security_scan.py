"""安全扫描模型"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SecurityScan(Base):
    __tablename__ = "security_scan"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skill.id"), index=True)
    scan_type: Mapped[str] = mapped_column(String(16))  # static / sandbox / threat_model
    risk_level: Mapped[str] = mapped_column(String(16), default="none")
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending / running / completed / failed
    findings: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    skill = relationship("Skill", back_populates="security_scans")
