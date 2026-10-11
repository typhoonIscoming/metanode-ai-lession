"""信号事件路由（real impl，与 frontend Zod 对齐：嵌套 market/prediction + Decimal string）。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from btc_arb.db import get_session
from btc_arb.models.market import Market
from btc_arb.models.prediction import Prediction
from btc_arb.models.signal_event import SignalEvent
from btc_arb.schemas.common import PaginatedResponse

router = APIRouter(prefix="/signals", tags=["signals"])


def _serialize_event(ev: SignalEvent, market: Market | None, prediction: Prediction | None) -> dict[str, Any]:
    """SignalEvent + 关联 Market + Prediction → 与 frontend Zod 对齐的 dict。"""
    return {
        "id": ev.id,
        "market": {
            "id": market.id if market else ev.market_id,
            "question": market.question if market else "",
            "slug": market.slug if market else "",
        },
        "prediction": {
            "p_ai": f"{float(prediction.p_ai):.4f}" if prediction else "0.0000",
            "model_version": prediction.model_version if prediction else "unknown",
        },
        "kind": ev.kind,
        "from_state": ev.from_state,
        "to_state": ev.to_state,
        "p_ai_at_event": f"{float(ev.p_ai_at_event):.4f}",
        "p_mkt_at_event": f"{float(ev.p_mkt_at_event):.4f}",
        "gap": f"{float(ev.gap):.4f}",
        "feishu_pushed": ev.feishu_pushed,
        "feishu_push_at": ev.feishu_push_at.isoformat() if ev.feishu_push_at else None,
        "feishu_error": ev.feishu_error,
        "feishu_retry_count": ev.feishu_retry_count,
        "occurred_at": ev.occurred_at.isoformat(),
    }


@router.get("", response_model=PaginatedResponse[dict])
async def list_signals(
    kind: str | None = None,
    market_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[dict]:
    stmt = select(SignalEvent)
    count_stmt = select(func.count(SignalEvent.id))
    if kind:
        stmt = stmt.where(SignalEvent.kind == kind)
        count_stmt = count_stmt.where(SignalEvent.kind == kind)
    if market_id is not None:
        stmt = stmt.where(SignalEvent.market_id == market_id)
        count_stmt = count_stmt.where(SignalEvent.market_id == market_id)
    stmt = stmt.order_by(SignalEvent.occurred_at.desc()).limit(limit)

    events = (await session.execute(stmt)).scalars().all()

    # 一次性把所有相关 market/prediction 拉出来（N+1 → 2 次查询）
    market_ids = {e.market_id for e in events}
    pred_ids = {e.prediction_id for e in events}
    markets = {
        m.id: m for m in (
            await session.execute(select(Market).where(Market.id.in_(market_ids)))
        ).scalars().all()
    } if market_ids else {}
    preds = {
        p.id: p for p in (
            await session.execute(select(Prediction).where(Prediction.id.in_(pred_ids)))
        ).scalars().all()
    } if pred_ids else {}

    total = (await session.execute(count_stmt)).scalar_one()
    return PaginatedResponse[dict](
        items=[
            _serialize_event(ev, markets.get(ev.market_id), preds.get(ev.prediction_id))
            for ev in events
        ],
        total=int(total),
        page=1,
        page_size=limit,
    )


@router.get("/{signal_id}")
async def get_signal(
    signal_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    ev = await session.get(SignalEvent, signal_id)
    if ev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="signal not found")
    market = await session.get(Market, ev.market_id)
    prediction = await session.get(Prediction, ev.prediction_id)
    return _serialize_event(ev, market, prediction)
