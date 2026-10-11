"""一次性 demo：跑通 discovery → predict → price_poll → signal → notify 完整闭环。

用法（需要 DB 已起 + alembic 迁移已跑）：
    python scripts/demo_run_once.py [--seed]

--seed: 额外插入一个"必定触发信号"的合成市场（strike 远高于现价，方向 above → P(AI) 极低
        但 demo 时市场价 0.5 → gap ≈ -0.5 触发 ENTRY_SHORT）

不带 --seed 时只跑真实 Polymarket 数据。
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from btc_arb.db import get_session_factory
from btc_arb.models.market import Market
from btc_arb.models.price_tick import PriceTick
from btc_arb.services.discovery import discover_markets
from btc_arb.services.notification import push_unpushed_signals
from btc_arb.services.prediction import predict_all_active
from btc_arb.services.price_monitor import poll_active_markets
from btc_arb.services.signal_engine import evaluate_all_active


async def seed_demo_market() -> None:
    """插入一个合成市场，必定触发信号（用于不依赖真实 Polymarket 也能演示）。"""
    factory = get_session_factory()
    async with factory() as session:
        existing = (
            await session.execute(
                select(Market).where(Market.condition_id == "demo-synthetic-001")
            )
        ).scalar_one_or_none()
        # 一个极大 strike（5M USD）的 above 市场 → P(AI 量化) 必然 ≈ 0
        # last_state_change_at 设到去抖窗口之外（30 分钟前），保证 demo 能立刻产生信号
        past = datetime.now(timezone.utc) - timedelta(minutes=30)
        if existing:
            # 已存在：把 state 重置到 WATCHING 并把 last_state_change_at 拉回过去
            existing.state = "WATCHING"
            existing.last_state_change_at = past
            await session.commit()
            market_id = existing.id
            print(f"[seed] demo market 已存在 (id={market_id})，state 重置为 WATCHING，去抖窗口已重置")
        else:
            m = Market(
                condition_id="demo-synthetic-001",
                slug="demo-btc-5m",
                question="[DEMO] Will BTC reach $5,000,000 by end of year?",
                description="合成 demo 市场。本市场不存在于真实 Polymarket，仅用于演示信号闭环。",
                strike_price=5_000_000.0,
                direction="above",
                resolve_at=datetime.now(timezone.utc) + timedelta(days=60),
                outcome_yes_token_id="demo_yes_token_001",
                outcome_no_token_id="demo_no_token_001",
                state="WATCHING",
                source="manual",
                last_state_change_at=past,
                market_metadata={"demo": True},
            )
            session.add(m)
            await session.commit()
            await session.refresh(m)
            market_id = m.id
            print(f"[seed] 创建 demo market id={market_id} strike=$5,000,000 above")

        # 给 demo market 灌一个合成 price_tick：YES 中价 0.5（说明市场认为「BTC 涨到 5M」概率 50%）
        # AI 算出来会接近 0.001，gap = 0.001 - 0.5 = -0.499 → 触发 ENTRY_SHORT
        session.add(PriceTick(market_id=market_id, p_yes=0.5, p_no=0.5))
        await session.commit()
        print(f"[seed] 给 demo market 注入 1 条 price_tick (p_yes=0.5)")


async def main(seed: bool) -> None:
    print("=" * 60)
    print("BTC 套利信号 demo · 一次性跑通完整闭环")
    print("=" * 60)

    factory = get_session_factory()

    # 1. 真实 Polymarket 发现
    print("\n[1/5] discover_markets（拉真实 Polymarket BTC 市场）...")
    try:
        async with factory() as session:
            stats = await discover_markets(session)
        print(f"     {stats}")
    except Exception as e:
        print(f"     ⚠️ discovery 失败: {type(e).__name__}: {e}")

    # 2. 可选：插入合成 demo 市场
    if seed:
        print("\n[seed] 插入合成 demo 市场（保证有信号可演示）...")
        await seed_demo_market()

    # 3. 预测（拉 spot + vol，对所有 WATCHING 市场算 P(AI)）
    print("\n[2/5] predict_all_active（量化对数正态模型）...")
    try:
        async with factory() as session:
            stats = await predict_all_active(session)
        print(f"     {stats}")
    except Exception as e:
        print(f"     ⚠️ predict 失败: {type(e).__name__}: {e}")

    # 4. 价格轮询（拉真实 CLOB midpoint；demo 合成市场会失败因为 token 不存在）
    print("\n[3/5] poll_active_markets（拉 Polymarket CLOB midpoint）...")
    try:
        async with factory() as session:
            stats = await poll_active_markets(session)
        print(f"     {stats}")
    except Exception as e:
        print(f"     ⚠️ price poll 失败: {type(e).__name__}: {e}")

    # 5. 信号引擎
    print("\n[4/5] evaluate_all_active（信号状态机）...")
    try:
        async with factory() as session:
            stats = await evaluate_all_active(session)
        print(f"     {stats}")
    except Exception as e:
        print(f"     ⚠️ signal engine 失败: {type(e).__name__}: {e}")

    # 6. 推送（飞书 webhook 未配 → dry_run 打印到日志）
    print("\n[5/5] push_unpushed_signals（飞书推送）...")
    try:
        async with factory() as session:
            stats = await push_unpushed_signals(session)
        print(f"     {stats}")
    except Exception as e:
        print(f"     ⚠️ notification 失败: {type(e).__name__}: {e}")

    # 汇总：列出所有产生的信号
    print("\n" + "=" * 60)
    print("最终状态汇总")
    print("=" * 60)
    from btc_arb.models.signal_event import SignalEvent
    async with factory() as session:
        markets = (await session.execute(select(Market))).scalars().all()
        signals = (
            await session.execute(
                select(SignalEvent).order_by(SignalEvent.occurred_at.desc()).limit(20)
            )
        ).scalars().all()
    print(f"market 表共 {len(markets)} 行：")
    for m in markets[:10]:
        print(f"  [{m.id}] state={m.state} {m.question[:60]}")
    print(f"\nsignal_event 表最近 {len(signals)} 条：")
    for s in signals:
        print(
            f"  [{s.id}] kind={s.kind} gap={float(s.gap):+.4f} "
            f"p_ai={float(s.p_ai_at_event):.3f} p_mkt={float(s.p_mkt_at_event):.3f} "
            f"pushed={s.feishu_pushed}"
        )

    print(
        "\n演示完成。如果要看真实飞书推送，编辑 setting.feishu_webhook_url 后重跑：\n"
        '  docker compose exec db psql -U btc_arb -c "UPDATE setting SET feishu_webhook_url=\'<your_webhook>\' WHERE id=1"\n'
        "  python scripts/demo_run_once.py"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seed", action="store_true",
        help="额外插入合成 demo 市场（保证至少有一条信号产生）",
    )
    args = parser.parse_args()
    asyncio.run(main(seed=args.seed))
