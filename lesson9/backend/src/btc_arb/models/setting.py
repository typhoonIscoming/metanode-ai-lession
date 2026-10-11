"""setting：全局配置单行表（id 强制为 1）。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ARRAY, CheckConstraint, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from btc_arb.db import Base


class Setting(Base):
    """全局运行时配置；所有业务参数都从此处读，运行期可 PATCH 改。"""

    __tablename__ = "setting"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_setting_singleton"),
        CheckConstraint("debounce_minutes >= 1", name="ck_setting_debounce_min"),
        CheckConstraint("price_poll_minutes >= 1", name="ck_setting_poll_min"),
        CheckConstraint("predict_ttl_hours >= 1", name="ck_setting_ttl_min"),
        CheckConstraint(
            "web_search_provider IN ('tavily','exa','brave','openai')",
            name="ck_setting_web_search_provider",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, server_default="1")
    entry_threshold: Mapped[float] = mapped_column(
        Numeric(4, 3), nullable=False, server_default="0.150"
    )
    debounce_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="10")
    price_poll_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    predict_ttl_hours: Mapped[int] = mapped_column(Integer, nullable=False, server_default="24")
    discovery_keywords: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{bitcoin,btc}"
    )
    discovery_max_days_to_resolve: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="30"
    )
    feishu_webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    openai_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    openai_model: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default="gpt-5"
    )
    web_search_provider: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="tavily"
    )
    web_search_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
