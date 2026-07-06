"""Skill 相关 schema"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SkillListItem(BaseModel):
    """skills.list 返回项"""
    name: str
    version: str
    display_name: str | None = None
    description: str | None = None
    category: str | None = None
    scope: str = "private"
    security_status: str = "pending"
    security_risk_level: str = "none"
    is_mandatory: bool = False
    size_bytes: int = 0

    model_config = {"from_attributes": True}


class SkillListResponse(BaseModel):
    skills: list[SkillListItem]
    total: int


class SkillGetResponse(SkillListItem):
    """skills.get 返回"""
    files: list[dict] = []
    changelog: str | None = None
    assigned_at: datetime | None = None
    source: str = "local"
    source_url: str | None = None


class SkillFileItem(BaseModel):
    path: str
    content: str
    encoding: str = "utf-8"
    size_bytes: int = 0
    sha256: str = ""


class SkillDownloadResponse(BaseModel):
    """skills.download 返回"""
    skill: SkillListItem
    files: list[SkillFileItem]


class SkillUploadResponse(BaseModel):
    id: str
    skill_name: str
    version: str
    security_status: str
    security_risk_level: str
    message: str = ""


class SkillAssignRequest(BaseModel):
    agent_ids: list[str]


class SkillScopeUpdate(BaseModel):
    scope: str = "private"
    is_mandatory: bool = False


class SkillCreate(BaseModel):
    skill_name: str
    display_name: str | None = None
    description: str | None = None
    category: str | None = None
    version: str = "1.0.0"
    scope: str = "public"
    is_mandatory: bool = False
