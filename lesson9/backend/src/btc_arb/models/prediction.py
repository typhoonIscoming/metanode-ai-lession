"""prediction：每个市场的 AI 预测历史。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from btc_arb.db import Base


class Prediction(Base):
    """单次预测结果：量化 + LLM 调整的合成 P(YES) 与解释。"""

    __tablename__ = "prediction"
    __table_args__ = (
        CheckConstraint("p_ai BETWEEN 0 AND 1", name="ck_prediction_p_ai_range"),
        CheckConstraint("p_quant BETWEEN 0 AND 1", name="ck_prediction_p_quant_range"),
        CheckConstraint(
            "llm_confidence IN ('low','medium','high') OR llm_confidence IS NULL",
            name="ck_prediction_confidence",
        ),
        Index("prediction_market_created_idx", "market_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    market_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("market.id", ondelete="CASCADE"),
        nullable=False,
    )
    p_ai: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    p_quant: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    llm_adjustment: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    llm_confidence: Mapped[str | None] = mapped_column(String(8), nullable=True)
    llm_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    news_sources: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    spot_price: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    realized_vol: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
