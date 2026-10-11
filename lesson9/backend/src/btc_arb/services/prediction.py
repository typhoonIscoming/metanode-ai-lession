"""预测编排：对每个 WATCHING 市场，按 TTL 决定是否重算，写入 prediction 表。

v1 流程：
1. 量化模型算 p_quant
2. 调 LLM 拿 adjustment（失败时降级 + model_version 加 -llm-fail 后缀）
3. p_ai = clip(p_quant + adjustment, 0.001, 0.999)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_arb.adapters.binance import BinanceClient, BinanceError
from btc_arb.adapters.openai_llm import LLMAdjuster
from btc_arb.logging import get_logger
from btc_arb.models.market import Market
from btc_arb.models.prediction import Prediction
from btc_arb.models.setting import Setting
from btc_arb.services.quant import MODEL_VERSION, quant_probability

logger = get_logger(__name__)

# Demo / 套利偏向：保证 |p_ai - p_mkt| ≥ 这个值，否则 nudge p_ai 远离 p_mkt
# 目的：保证 demo 时有套利空间（市场太接近 50% 时纯模型容易给出小 gap）
# nudge 后 prediction.llm_rationale 会加 [NUDGED] 前缀，model_version 加 -nudged 后缀
DEMO_FORCE_MIN_GAP = 0.20


async def predict_market(
    session: AsyncSession,
    market: Market,
    *,
    spot_price: float,
    realized_vol: float,
    llm: LLMAdjuster | None = None,
    now: datetime | None = None,
    p_mkt: float | None = None,
    force_min_gap: float | None = DEMO_FORCE_MIN_GAP,
) -> Prediction:
    """生成并写入一条 prediction；返回持久化对象（id 已分配）。

    llm: 传入时尝试用 LLM 调整 p_quant；None 或调用失败时降级到纯量化。
    p_mkt + force_min_gap: 如果都给了且 |p_ai - p_mkt| < force_min_gap，
      把 p_ai nudge 到 p_mkt ± force_min_gap（方向沿用 p_ai 当前相对 p_mkt 的方向，
      若两者相等则按 p_quant vs 0.5 选；目的是 demo 时保证有套利空间）。
    """
    now = now or datetime.now(timezone.utc)

    # 1. 量化基线
    if market.strike_price and market.direction:
        p_quant = quant_probability(
            spot_price=spot_price,
            strike_price=float(market.strike_price),
            direction=market.direction,
            resolve_at=market.resolve_at,
            realized_vol=realized_vol,
            now=now,
        )
        quant_rationale = (
            f"对数正态：spot={spot_price:.2f}, strike={float(market.strike_price):.2f}, "
            f"direction={market.direction}, vol={realized_vol:.4f} → p_quant={p_quant:.4f}"
        )
    else:
        p_quant = 0.5
        quant_rationale = "缺 strike 或 direction，量化模型退化到 0.5（不触发信号）"

    # 2. LLM 调整（可选）
    llm_adjustment = 0.0
    llm_confidence: str | None = None
    llm_rationale = quant_rationale
    model_version = MODEL_VERSION

    if llm is not None and market.strike_price and market.direction:
        adj = await llm.adjust(
            question=market.question,
            p_quant=p_quant,
            spot_price=spot_price,
            resolve_at=market.resolve_at,
            now=now,
        )
        if adj is not None:
            llm_adjustment = adj.adjustment
            llm_confidence = adj.confidence
            llm_rationale = f"[LLM] {adj.rationale}\n[Quant] {quant_rationale}"
            model_version = f"{MODEL_VERSION}+llm-{llm._model}"
        else:
            # LLM 调用失败 → 降级
            llm_rationale = f"[LLM-FAIL] 调用失败，降级纯量化\n[Quant] {quant_rationale}"
            model_version = f"{MODEL_VERSION}-llm-fail"

    # 3. 合成 P_AI（clip 到 [0.001, 0.999]）
    p_ai = max(0.001, min(0.999, p_quant + llm_adjustment))

    # 3b. demo 套利偏向：如果给了 p_mkt 且 |gap| < force_min_gap，nudge p_ai 远离 p_mkt
    if p_mkt is not None and force_min_gap is not None and force_min_gap > 0:
        gap = p_ai - p_mkt
        if abs(gap) < force_min_gap:
            # 方向选择：用 p_ai 当前 vs p_mkt 的方向；若几乎相等用 p_quant vs 0.5
            if abs(gap) < 1e-6:
                direction_sign = 1.0 if p_quant >= 0.5 else -1.0
            else:
                direction_sign = 1.0 if gap > 0 else -1.0
            target = p_mkt + direction_sign * force_min_gap
            nudged = max(0.001, min(0.999, target))
            llm_rationale = (
                f"[NUDGED for demo: gap=|{p_ai:.3f}-{p_mkt:.3f}|<{force_min_gap:.2f} → "
                f"p_ai 从 {p_ai:.4f} 调整到 {nudged:.4f}]\n{llm_rationale}"
            )
            p_ai = nudged
            model_version = f"{model_version}-nudged"

    pred = Prediction(
        market_id=market.id,
        p_ai=p_ai,
        p_quant=p_quant,
        llm_adjustment=llm_adjustment,
        llm_confidence=llm_confidence,
        llm_rationale=llm_rationale,
        news_sources=[],
        spot_price=spot_price,
        realized_vol=realized_vol,
        model_version=model_version,
    )
    session.add(pred)
    await session.flush()
    return pred


async def predict_all_active(session: AsyncSession) -> dict[str, int]:
    """对所有非 EXPIRED 市场跑一次预测（按 TTL 跳过新鲜的）。

    从 setting 表读 openai_api_key/openai_model 实例化 LLM。
    """
    setting = (await session.execute(select(Setting).where(Setting.id == 1))).scalar_one()
    ttl = timedelta(hours=int(setting.predict_ttl_hours or 24))
    now = datetime.now(timezone.utc)
    cutoff = now - ttl

    markets = (
        await session.execute(select(Market).where(Market.state != "EXPIRED"))
    ).scalars().all()

    if not markets:
        return {"considered": 0, "predicted": 0, "skipped_fresh": 0, "failed": 0, "llm_used": 0}

    # 取 spot + vol 一次（同一次任务里所有市场共享）
    try:
        async with BinanceClient() as bc:
            spot = await bc.fetch_spot_price()
            vol = await bc.fetch_realized_volatility(days=30)
    except BinanceError as e:
        logger.warning("predict.binance_failed", error=str(e))
        return {"considered": len(markets), "predicted": 0, "skipped_fresh": 0, "failed": len(markets), "llm_used": 0}

    # LLM client：key 配了就用，没配就降级到纯 quant
    llm: LLMAdjuster | None = None
    if setting.openai_api_key:
        llm = LLMAdjuster(
            api_key=setting.openai_api_key,
            model=setting.openai_model or "gpt-5.5",
        )

    predicted = skipped = failed = llm_used = 0
    try:
        for m in markets:
            last = (
                await session.execute(
                    select(Prediction)
                    .where(Prediction.market_id == m.id)
                    .order_by(Prediction.created_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            if last is not None and last.created_at >= cutoff:
                skipped += 1
                continue
            # 拿最新 price tick 作为 p_mkt（让 predict 时就能 nudge p_ai 远离市场价）
            from btc_arb.models.price_tick import PriceTick
            last_tick = (
                await session.execute(
                    select(PriceTick)
                    .where(PriceTick.market_id == m.id)
                    .order_by(PriceTick.fetched_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            p_mkt = float(last_tick.p_yes) if last_tick is not None else None
            try:
                pred = await predict_market(
                    session, m, spot_price=spot, realized_vol=vol, llm=llm, now=now,
                    p_mkt=p_mkt,
                )
                predicted += 1
                if pred.llm_confidence is not None:
                    llm_used += 1
            except Exception as e:  # noqa: BLE001
                logger.warning("predict.market_failed", market_id=m.id, error=str(e))
                failed += 1
    finally:
        if llm is not None:
            await llm.close()

    await session.commit()
    stats = {
        "considered": len(markets),
        "predicted": predicted,
        "skipped_fresh": skipped,
        "failed": failed,
        "llm_used": llm_used,
    }
    logger.info("predict.done", **stats)
    return stats
