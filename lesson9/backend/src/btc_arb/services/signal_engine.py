"""信号引擎：纯函数 `decide_transition()` + 编排 `evaluate_all_active()`。

状态机：
  WATCHING ──gap > +threshold──> ENTERED_LONG  (kind=ENTRY_LONG)
  WATCHING ──gap < -threshold──> ENTERED_SHORT (kind=ENTRY_SHORT)
  ENTERED_LONG  ──gap < +ε──> WATCHING (kind=EXIT_LONG)
  ENTERED_SHORT ──gap > -ε──> WATCHING (kind=EXIT_SHORT)
  *             ──now > resolve_at──> EXPIRED (kind=EXPIRED)

去抖：last_state_change_at 之后 < debounce_minutes 内不触发非 EXPIRED 跃迁
ε（退出滞回带）：0.001
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_arb.logging import get_logger
from btc_arb.models.market import Market
from btc_arb.models.prediction import Prediction
from btc_arb.models.price_tick import PriceTick
from btc_arb.models.setting import Setting
from btc_arb.models.signal_event import SignalEvent

logger = get_logger(__name__)

EPSILON = 0.001


@dataclass(frozen=True)
class Transition:
    """状态跃迁结果（None kind 表示不跃迁）。"""

    from_state: str
    to_state: str
    kind: str | None  # ENTRY_LONG / ENTRY_SHORT / EXIT_LONG / EXIT_SHORT / EXPIRED / None


def decide_transition(
    *,
    current_state: str,
    p_ai: float,
    p_mkt: float,
    entry_threshold: float,
    resolve_at: datetime,
    last_state_change_at: datetime,
    debounce_minutes: int,
    now: datetime,
) -> Transition:
    """纯函数：根据当前状态 + 价差 + 时间约束，决定要不要跃迁。"""
    # 1. EXPIRED 优先（不受去抖约束）
    if now >= resolve_at and current_state != "EXPIRED":
        return Transition(current_state, "EXPIRED", "EXPIRED")
    if current_state == "EXPIRED":
        return Transition("EXPIRED", "EXPIRED", None)

    # 2. 去抖：上次状态变更到现在不足 debounce_minutes，禁止非 EXPIRED 跃迁
    debounce_active = (now - last_state_change_at) < timedelta(minutes=debounce_minutes)

    gap = p_ai - p_mkt

    if current_state == "WATCHING":
        if debounce_active:
            return Transition("WATCHING", "WATCHING", None)
        if gap > entry_threshold:
            return Transition("WATCHING", "ENTERED_LONG", "ENTRY_LONG")
        if gap < -entry_threshold:
            return Transition("WATCHING", "ENTERED_SHORT", "ENTRY_SHORT")
        return Transition("WATCHING", "WATCHING", None)

    if current_state == "ENTERED_LONG":
        # 退出条件：gap 收回到 +ε 内（即不再值得做多）
        if gap < EPSILON:
            return Transition("ENTERED_LONG", "WATCHING", "EXIT_LONG")
        return Transition("ENTERED_LONG", "ENTERED_LONG", None)

    if current_state == "ENTERED_SHORT":
        if gap > -EPSILON:
            return Transition("ENTERED_SHORT", "WATCHING", "EXIT_SHORT")
        return Transition("ENTERED_SHORT", "ENTERED_SHORT", None)

    # 未知状态：no-op
    return Transition(current_state, current_state, None)


async def evaluate_all_active(session: AsyncSession) -> dict[str, int]:
    """遍历所有非 EXPIRED 市场，按最新 prediction + 最新 tick 跑一次决策。"""
    setting = (await session.execute(select(Setting).where(Setting.id == 1))).scalar_one()
    entry_threshold = float(setting.entry_threshold)
    debounce_minutes = int(setting.debounce_minutes)
    now = datetime.now(timezone.utc)

    markets = (
        await session.execute(select(Market).where(Market.state != "EXPIRED"))
    ).scalars().all()

    if not markets:
        return {"considered": 0, "transitioned": 0, "skipped_no_data": 0}

    transitioned = skipped = 0

    for m in markets:
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

        if last_pred is None or last_tick is None:
            # EXPIRED 边界仍要检查（即使无 pred/tick）
            if now >= m.resolve_at:
                m.state = "EXPIRED"
                m.last_state_change_at = now
                transitioned += 1
                continue
            skipped += 1
            continue

        t = decide_transition(
            current_state=m.state,
            p_ai=float(last_pred.p_ai),
            p_mkt=float(last_tick.p_yes),
            entry_threshold=entry_threshold,
            resolve_at=m.resolve_at,
            last_state_change_at=m.last_state_change_at,
            debounce_minutes=debounce_minutes,
            now=now,
        )
        if t.kind is None:
            continue

        # 跃迁 + 写 signal_event（同事务）
        m.state = t.to_state
        m.last_state_change_at = now
        session.add(SignalEvent(
            market_id=m.id,
            prediction_id=last_pred.id,
            kind=t.kind,
            from_state=t.from_state,
            to_state=t.to_state,
            p_ai_at_event=float(last_pred.p_ai),
            p_mkt_at_event=float(last_tick.p_yes),
            gap=float(last_pred.p_ai) - float(last_tick.p_yes),
        ))
        transitioned += 1

    await session.commit()
    stats = {
        "considered": len(markets),
        "transitioned": transitioned,
        "skipped_no_data": skipped,
    }
    logger.info("signal_engine.done", **stats)
    return stats
