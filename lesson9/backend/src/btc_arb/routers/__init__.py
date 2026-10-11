"""FastAPI 路由聚合。

Phase 0 全部为 stub：
- GET list → 空容器
- GET single → 404
- POST/PUT 写路径 → 422 NOT_IMPLEMENTED
- GET /healthz、GET /settings 是真实实现（healthz 在本任务，settings 在 B-02 之后）
"""

from __future__ import annotations

from fastapi import APIRouter

from btc_arb.routers import (
    health,
    markets,
    predict,
    scheduler,
    signals,
)
from btc_arb.routers import (
    settings as settings_router,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(markets.router)
api_router.include_router(predict.router)
api_router.include_router(signals.router)
api_router.include_router(settings_router.router)
api_router.include_router(scheduler.router)

__all__ = ["api_router"]
