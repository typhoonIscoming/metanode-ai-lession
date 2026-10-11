"""市场发现（v2）：每日只追 `bitcoin-above-on-{month}-{day}` 这一个 BTC 价格 event。

策略：
- target_date = today + N days (UTC)，N 默认 2（由 setting.discovery_max_days_to_resolve 控制）
- slug = bitcoin-above-on-{月份小写}-{日}
- /events?slug={slug} 拉 event + sub-markets
- 每个 sub-market 取 YES midpoint，挑最接近 0.5 的入库（套利信息量最高）

不再用通用 tag=bitcoin 扫，避免污染 MicroStrategy / 长期 strike 等无关市场。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_arb.adapters.polymarket import PolymarketClient
from btc_arb.logging import get_logger
from btc_arb.models.market import Market
from btc_arb.models.setting import Setting

logger = get_logger(__name__)


def target_event_slug(target_date) -> str:
    """`bitcoin-above-on-{月份小写}-{日}`（无零填充）。"""
    return f"bitcoin-above-on-{target_date.strftime('%B').lower()}-{target_date.day}"


async def discover_markets(session: AsyncSession) -> dict[str, int]:
    """每日 BTC discover：拉 today+N 那天的 BTC 价格 event，挑最接近 50% 的子市场入库。

    setting.discovery_max_days_to_resolve 在此处复用为「向后多少天」（默认 2）。
    """
    setting = (await session.execute(select(Setting).where(Setting.id == 1))).scalar_one()
    days_ahead = int(setting.discovery_max_days_to_resolve or 2)

    today = datetime.now(timezone.utc).date()
    target_date = today + timedelta(days=days_ahead)
    slug = target_event_slug(target_date)

    async with PolymarketClient() as client:
        chosen = await client.fetch_event_pick_closest_to_half(slug)

    if chosen is None:
        logger.warning("discovery.event_not_found", slug=slug, target_date=target_date.isoformat())
        return {"fetched": 0, "created": 0, "updated": 0, "skipped": 0, "target_slug": slug}

    now = datetime.now(timezone.utc)
    cid = chosen["condition_id"]
    existing = (
        await session.execute(select(Market).where(Market.condition_id == cid))
    ).scalar_one_or_none()

    created = updated = 0
    if existing is None:
        md = {
            "discovered_at": now.isoformat(),
            "event_slug": slug,
            "chosen_midpoint": chosen.get("chosen_midpoint"),
        }
        session.add(Market(
            condition_id=cid,
            slug=chosen.get("slug") or "",
            question=chosen.get("question") or "",
            description=chosen.get("description"),
            strike_price=chosen.get("strike_price"),
            direction=chosen.get("direction") or "above",
            resolve_at=chosen["resolve_at"],
            outcome_yes_token_id=chosen["outcome_yes_token_id"],
            outcome_no_token_id=chosen["outcome_no_token_id"],
            state="WATCHING",
            source="discovery",
            market_metadata=md,
        ))
        created = 1
    else:
        existing.question = chosen.get("question") or existing.question
        existing.description = chosen.get("description") or existing.description
        if chosen.get("strike_price"):
            existing.strike_price = chosen["strike_price"]
        # 更新 metadata 里的 chosen_midpoint 给前端展示
        md = dict(existing.market_metadata or {})
        md["chosen_midpoint"] = chosen.get("chosen_midpoint")
        existing.market_metadata = md
        updated = 1

    await session.commit()
    stats = {
        "fetched": 1,
        "created": created,
        "updated": updated,
        "skipped": 0,
        "target_slug": slug,
        "target_date": target_date.isoformat(),
        "chosen_question": chosen.get("question"),
    }
    logger.info("discovery.done", **stats)
    return stats
