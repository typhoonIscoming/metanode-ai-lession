"""通知：扫所有未推送 SignalEvent，渲染飞书卡片并发送，标记 pushed。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_arb.adapters.binance import BinanceClient, BinanceError
from btc_arb.adapters.feishu import FeishuClient, render_signal_card
from btc_arb.logging import get_logger
from btc_arb.models.market import Market
from btc_arb.models.setting import Setting
from btc_arb.models.signal_event import SignalEvent

logger = get_logger(__name__)


async def push_unpushed_signals(session: AsyncSession) -> dict[str, int]:
    """扫 feishu_pushed = false 的事件，依次推送。返回统计。"""
    setting = (await session.execute(select(Setting).where(Setting.id == 1))).scalar_one()
    webhook_url = setting.feishu_webhook_url  # 可能为 None → dry-run

    unpushed = (
        await session.execute(
            select(SignalEvent)
            .where(SignalEvent.feishu_pushed.is_(False))
            .order_by(SignalEvent.occurred_at.asc())
            .limit(50)
        )
    ).scalars().all()

    if not unpushed:
        return {"pending": 0, "pushed": 0, "failed": 0, "dry_run": 0}

    # 取一次 spot 用于卡片显示（失败给 None，不影响推送）
    spot: float | None = None
    try:
        async with BinanceClient() as bc:
            spot = await bc.fetch_spot_price()
    except BinanceError:
        pass

    pushed = failed = dry_run = 0
    async with FeishuClient(webhook_url) as fc:
        for ev in unpushed:
            market = (
                await session.execute(select(Market).where(Market.id == ev.market_id))
            ).scalar_one_or_none()
            if market is None:
                ev.feishu_pushed = True  # 标 pushed 防止反复
                ev.feishu_error = "market not found"
                continue
            md = market.market_metadata or {}
            card = render_signal_card(
                kind=ev.kind,
                question=market.question,
                slug=market.slug,
                p_ai=float(ev.p_ai_at_event),
                p_mkt=float(ev.p_mkt_at_event),
                gap=float(ev.gap),
                spot_price=spot,
                resolve_at_iso=market.resolve_at.astimezone(timezone.utc).isoformat(),
                event_slug=md.get("event_slug"),
                is_demo=bool(md.get("demo")),
            )
            try:
                result = await fc.push_card(card)
                ev.feishu_pushed = True
                ev.feishu_push_at = datetime.now(timezone.utc)
                if result.get("dry_run"):
                    dry_run += 1
                else:
                    pushed += 1
            except Exception as e:  # noqa: BLE001
                ev.feishu_retry_count = (ev.feishu_retry_count or 0) + 1
                ev.feishu_error = str(e)[:500]
                failed += 1

    await session.commit()
    stats = {"pending": len(unpushed), "pushed": pushed, "failed": failed, "dry_run": dry_run}
    logger.info("notification.done", **stats)
    return stats
