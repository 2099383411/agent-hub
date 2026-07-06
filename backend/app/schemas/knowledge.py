"""知识库 schema"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class KnowledgeSearchResult(BaseModel):
    id: str
    title: str
    category: str | None = None
    snippet: str = ""
    relevance: float = 0.0
    updated_at: datetime | None = None


class KnowledgeSearchResponse(BaseModel):
    results: list[KnowledgeSearchResult]
    total: int


class KnowledgeGetResponse(BaseModel):
    id: str
    title: str
    content: str
    category: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class KnowledgeCreate(BaseModel):
    title: str
    content: str
    category: str | None = None


class KnowledgeUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None


class OnboardingResponse(BaseModel):
    version: int = 1
    content: str = ""
    updated_at: str = ""
