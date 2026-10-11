"""通用 schemas：分页响应、错误响应。"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class AppBaseModel(BaseModel):
    """项目内所有 Pydantic 模型基类，统一 ORM 兼容与时间序列化策略。"""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        ser_json_timedelta="iso8601",
    )


class PaginatedResponse(AppBaseModel, Generic[T]):
    """统一分页响应：list 路由都用这个壳。"""

    items: list[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class ItemsResponse(AppBaseModel, Generic[T]):
    """无总数的简单 items 容器（如 price_ticks / predictions 这类按市场内嵌的子资源）。"""

    items: list[T] = Field(default_factory=list)


class ErrorBody(AppBaseModel):
    """`{error: {code, message, details}}` 的内层。"""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(AppBaseModel):
    """对外错误响应统一形态。"""

    error: ErrorBody
