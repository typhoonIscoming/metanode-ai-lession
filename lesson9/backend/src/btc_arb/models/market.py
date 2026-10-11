"""market：被监控的 Polymarket 二元市场。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from btc_arb.db import Base


class Market(Base):
    """单个被监控市场（含状态机当前状态）。"""

    __tablename__ = "market"
    __table_args__ = (
        UniqueConstraint("condition_id", name="uq_market_condition_id"),
        CheckConstraint(
            "direction IN ('above','below')",
            name="ck_market_direction",
        ),
        CheckConstraint(
            "state IN ('WATCHING','ENTERED_LONG','ENTERED_SHORT','EXPIRED')",
            name="ck_market_state",
        ),
        CheckConstraint(
            "source IN ('discovery','manual')",
            name="ck_market_source",
        ),
        Index("market_state_active_idx", "state", postgresql_where=("state <> 'EXPIRED'")),
        Index("market_resolve_at_idx", "resolve_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    condition_id: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    strike_price: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    direction: Mapped[str | None] = mapped_column(String(8), nullable=True)
    resolve_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    outcome_yes_token_id: Mapped[str] = mapped_column(Text, nullable=False)
    outcome_no_token_id: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="WATCHING"
    )
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    market_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_state_change_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
