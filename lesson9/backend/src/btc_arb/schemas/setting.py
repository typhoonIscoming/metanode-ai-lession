"""setting 路由响应 schema。

GET /settings 返回的字段顺序与 backend-PRD §5.4 对齐；
敏感字段（feishu_webhook_url / openai_api_key / web_search_api_key）以 mask 字符串返回，
前 6 / 后 4 字符保留、中间用 `***hidden***` 占位，长度 < 10 时整串 mask。
"""

from __future__ import annotations

from datetime import datetime

from btc_arb.schemas.common import AppBaseModel


class SettingView(AppBaseModel):
    """GET /api/v1/settings 响应体。"""

    entry_threshold: str
    debounce_minutes: int
    price_poll_minutes: int
    predict_ttl_hours: int
    discovery_keywords: list[str]
    discovery_max_days_to_resolve: int
    feishu_webhook_url: str | None
    openai_api_key: str | None
    openai_model: str
    web_search_provider: str
    web_search_api_key: str | None
    updated_at: datetime


def mask_secret(raw: str | None) -> str | None:
    """敏感字段统一 mask 策略：前 6 + `***hidden***` + 后 4；< 10 字符整串 mask。"""
    if raw is None or raw == "":
        return None
    if len(raw) < 10:
        return "***hidden***"
    return f"{raw[:6]}***hidden***{raw[-4:]}"
