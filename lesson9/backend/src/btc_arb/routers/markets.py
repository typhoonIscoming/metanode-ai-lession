"""市场路由（real impl，v1 简化版，与 frontend Zod schema 对齐）。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_arb.db import get_session
from btc_arb.models.market import Market
from btc_arb.models.prediction import Prediction
from btc_arb.models.price_tick import PriceTick
from btc_arb.schemas.common import ItemsResponse, PaginatedResponse

router = APIRouter(prefix="/markets", tags=["markets"])


async def _build_market_dict(
    m: Market,
    session: AsyncSession,
    *,
    include_detail: bool = False,
) -> dict[str, Any]:
    """ORM → dict，含 latest_prediction / latest_price / gap（与 Zod MarketSchema 对齐）。"""
    last_pred = (
        await session.execute(
            select(Prediction)
            .where(Prediction.market_id == m.id)
            .order_by(Prediction.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    last_tick = (
        await session.execute(
            select(PriceTick)
            .where(PriceTick.market_id == m.id)
            .order_by(PriceTick.fetched_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    latest_prediction = (
        {
            "p_ai": f"{float(last_pred.p_ai):.4f}",
            "model_version": last_pred.model_version,
            "created_at": last_pred.created_at.isoformat(),
        }
        if last_pred
        else None
    )
    latest_price = (
        {
            "p_yes": f"{float(last_tick.p_yes):.4f}",
            "fetched_at": last_tick.fetched_at.isoformat(),
        }
        if last_tick
        else None
    )
    gap = (
        f"{float(last_pred.p_ai) - float(last_tick.p_yes):.4f}"
        if last_pred and last_tick
        else None
    )

    result: dict[str, Any] = {
        "id": m.id,
        "condition_id": m.condition_id,
        "slug": m.slug,
        "question": m.question,
        "description": m.description,
        "strike_price": f"{float(m.strike_price):.8f}" if m.strike_price is not None else None,
        "direction": m.direction,
        "resolve_at": m.resolve_at.isoformat(),
        "state": m.state,
        "source": m.source,
        "created_at": m.created_at.isoformat(),
        "last_state_change_at": m.last_state_change_at.isoformat(),
        "latest_prediction": latest_prediction,
        "latest_price": latest_price,
        "gap": gap,
    }
    if include_detail:
        result["metadata"] = m.market_metadata or {}
        result["outcome_yes_token_id"] = m.outcome_yes_token_id
        result["outcome_no_token_id"] = m.outcome_no_token_id
    return result


@router.get("", response_model=PaginatedResponse[dict])
async def list_markets(
    state: str | None = None,
    source: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[dict]:
    """列出被监控市场，支持 state/source 筛选。"""
    stmt = select(Market)
    count_stmt = select(func.count(Market.id))
    if state:
        stmt = stmt.where(Market.state == state)
        count_stmt = count_stmt.where(Market.state == state)
    if source:
        stmt = stmt.where(Market.source == source)
        count_stmt = count_stmt.where(Market.source == source)
    stmt = stmt.order_by(Market.resolve_at.asc()).limit(limit).offset(offset)

    rows = (await session.execute(stmt)).scalars().all()
    total = (await session.execute(count_stmt)).scalar_one()
    items = [await _build_market_dict(m, session) for m in rows]
    return PaginatedResponse[dict](
        items=items,
        total=int(total),
        page=(offset // limit) + 1,
        page_size=limit,
    )


@router.get("/{market_id}")
async def get_market(
    market_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    m = await session.get(Market, market_id)
    if m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="market not found")
    return await _build_market_dict(m, session, include_detail=True)


@router.post("", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
async def add_market(body: dict[str, Any]) -> dict[str, Any]:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="manual add disabled in v1; markets are discovered automatically",
    )


@router.delete("/{market_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_market(market_id: int):
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="delete not supported in v1",
    )


@router.get("/{market_id}/price_ticks", response_model=ItemsResponse[dict])
async def get_price_ticks(
    market_id: int,
    limit: int = Query(default=200, ge=1, le=2000),
    session: AsyncSession = Depends(get_session),
) -> ItemsResponse[dict]:
    rows = (
        await session.execute(
            select(PriceTick)
            .where(PriceTick.market_id == market_id)
            .order_by(PriceTick.fetched_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return ItemsResponse[dict](items=[
        {
            "id": t.id,
            "p_yes": f"{float(t.p_yes):.4f}",
            "p_no": f"{float(t.p_no):.4f}" if t.p_no is not None else None,
            "midpoint_source": t.midpoint_source,
            "fetched_at": t.fetched_at.isoformat(),
        }
        for t in rows
    ])


@router.get("/{market_id}/predictions", response_model=ItemsResponse[dict])
async def get_predictions(
    market_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> ItemsResponse[dict]:
    rows = (
        await session.execute(
            select(Prediction)
            .where(Prediction.market_id == market_id)
            .order_by(Prediction.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return ItemsResponse[dict](items=[
        {
            "id": p.id,
            "p_ai": f"{float(p.p_ai):.4f}",
            "p_quant": f"{float(p.p_quant):.4f}",
            "llm_adjustment": f"{float(p.llm_adjustment):.4f}",
            "llm_confidence": p.llm_confidence,
            "llm_rationale": p.llm_rationale,
            "news_sources": p.news_sources or [],
            "spot_price": f"{float(p.spot_price):.8f}" if p.spot_price is not None else None,
            "realized_vol": f"{float(p.realized_vol):.6f}" if p.realized_vol is not None else None,
            "model_version": p.model_version,
            "created_at": p.created_at.isoformat(),
        }
        for p in rows
    ])


@router.post("/{market_id}/repredict", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
async def repredict(market_id: int) -> dict[str, Any]:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="manual repredict not supported in v1; runs on scheduler",
    )
