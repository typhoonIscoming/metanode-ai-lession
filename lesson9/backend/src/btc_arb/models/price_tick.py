"""price_tick：每次价格轮询一条；30 天后清理。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from btc_arb.db import Base


class PriceTick(Base):
    """单次轮询拿到的 YES 价快照。"""

    __tablename__ = "price_tick"
    __table_args__ = (
        CheckConstraint("p_yes BETWEEN 0 AND 1", name="ck_price_tick_p_yes_range"),
        Index("price_tick_market_fetched_idx", "market_id", "fetched_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    market_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("market.id", ondelete="CASCADE"),
        nullable=False,
    )
    p_yes: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    p_no: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    midpoint_source: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="clob_midpoint"
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
