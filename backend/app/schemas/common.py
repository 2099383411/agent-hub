"""通用响应格式"""

from pydantic import BaseModel
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T | None = None
    request_id: str = ""


class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20
