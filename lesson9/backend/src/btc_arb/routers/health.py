"""健康检查路由。

`/healthz` 当前仅做进程存活与 DB ping；
`/readyz` 在 B-04 之后接入外部依赖并发探测。
"""

from __future__ import annotations

from fastapi import APIRouter

from btc_arb import __version__
from btc_arb.db import ping
from btc_arb.logging import get_logger
from btc_arb.schemas.health import HealthzResponse

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthzResponse)
async def healthz() -> HealthzResponse:
    """轻量健康检查：进程活着 + DB 可达即 ok。"""
    db_status = "ok"
    try:
        await ping()
    except Exception as exc:  # noqa: BLE001 — healthz 不能因外部异常崩
        logger.warning("healthz.db_ping_failed", error=str(exc))
        db_status = f"fail: {type(exc).__name__}"
    return HealthzResponse(
        status="ok" if db_status == "ok" else "degraded",
        db=db_status,
        version=f"{__version__}-skeleton",
    )
