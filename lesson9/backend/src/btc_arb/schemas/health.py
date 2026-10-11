"""健康检查响应。"""

from __future__ import annotations

from btc_arb.schemas.common import AppBaseModel


class HealthzResponse(AppBaseModel):
    """`/api/v1/healthz` 返回体。"""

    status: str = "ok"
    db: str = "ok"
    version: str
