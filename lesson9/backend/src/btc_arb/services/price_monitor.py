"""价格监控：每轮对所有 active 市场拉 YES midpoint，落 price_tick。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_arb.adapters.polymarket import PolymarketClient
from btc_arb.logging import get_logger
from btc_arb.models.market import Market
from btc_arb.models.price_tick import PriceTick

logger = get_logger(__name__)


async def poll_active_markets(session: AsyncSession) -> dict[str, int]:
    """对所有非 EXPIRED 市场拉一次中价，落 tick。返回统计。"""
    markets = (
        await session.execute(select(Market).where(Market.state != "EXPIRED"))
    ).scalars().all()

    if not markets:
        return {"considered": 0, "polled": 0, "failed": 0}

    polled = failed = 0
    async with PolymarketClient() as client:
        for m in markets:
            p_yes = await client.fetch_midpoint(m.outcome_yes_token_id)
            if p_yes is None:
                failed += 1
                continue
            session.add(PriceTick(market_id=m.id, p_yes=p_yes, p_no=1.0 - p_yes))
            polled += 1

    await session.commit()
    stats = {"considered": len(markets), "polled": polled, "failed": failed}
    logger.info("price_monitor.done", **stats)
    return stats
