"""signal_event：状态机跃迁触发的信号事件，含飞书推送状态。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from btc_arb.db import Base


class SignalEvent(Base):
    """一次状态跃迁对应一行；推送结果也写在这条记录上。"""

    __tablename__ = "signal_event"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('ENTRY_LONG','ENTRY_SHORT','EXIT_LONG','EXIT_SHORT','EXPIRED')",
            name="ck_signal_event_kind",
        ),
        Index("signal_event_market_occurred_idx", "market_id", "occurred_at"),
        Index(
            "signal_event_unpushed_idx",
            "occurred_at",
            postgresql_where=("feishu_pushed = false"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    market_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("market.id", ondelete="CASCADE"),
        nullable=False,
    )
    prediction_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("prediction.id"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    from_state: Mapped[str] = mapped_column(String(16), nullable=False)
    to_state: Mapped[str] = mapped_column(String(16), nullable=False)
    p_ai_at_event: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    p_mkt_at_event: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    gap: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    feishu_pushed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    feishu_push_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    feishu_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    feishu_retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
