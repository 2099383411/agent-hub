"""工具发现模型"""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Tool(Base):
    __tablename__ = "tool"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String(64))
    tool_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tool_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    agent = relationship("Agent", back_populates="tools")
