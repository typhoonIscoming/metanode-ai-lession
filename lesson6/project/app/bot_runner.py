"""单 bot 的 tick 逻辑 + 仓位决策。

tick(session, bot_id, exchanges, kline_source) 在 session 当前事务里：
  1. （如有 kline_source）拉最新 K 线
  2. 读 OHLC 最近 N 根
  3. 跑策略 → signal
  4. decide_order → (side, qty)
  5. 下单（如 qty > 0）
  6. 写 pnl_snapshot
  7. 写 tick_log
任何异常 → bot.status=errored，tick_log.status=errored。
"""

from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import text
from sqlmodel import Session

from app.exchange.base import Exchange, OrderSide
from app.kline_source import KlineSource
from app.models import (
    Bot,
    BotStatus,
    PnLSnapshot,
    Position,
    TickLog,
    TickStatus,
    utcnow_iso,
)
from app.strategies import STRATEGY_REGISTRY

logger = logging.getLogger(__name__)

_OHLC_HISTORY_LIMIT = 200


def decide_order(
    latest_signal: int,
    position: Position,
    mark_price: float,
    fee_rate: float = 0.001,
) -> tuple[OrderSide, float]:
    """根据信号和当前仓位决定下单 side 和 qty；qty == 0 表示无动作。

    决策表：
      signal=+1  base_qty==0      → buy 全仓
      signal=+1  base_qty>0       → no-op
      signal= 0  base_qty>0       → sell 全部
      signal= 0  base_qty==0      → no-op
      signal=-1  *                → 降级为 signal=0（v1 无空头；caller 应写 warn 日志）
    """
    if latest_signal == -1:
        latest_signal = 0

    if latest_signal == 1 and position.base_qty == 0:
        qty = position.cash / (mark_price * (1.0 + fee_rate))
        return OrderSide.buy, qty
    if latest_signal == 0 and position.base_qty > 0:
        return OrderSide.sell, position.base_qty
    return OrderSide.buy, 0.0


def tick(
    session: Session,
    bot_id: int,
    exchanges: dict[str, Exchange],
    kline_source: KlineSource | None = None,
) -> None:
    """跑一次 tick；调用方传 kline_source（生产环境必传；测试可省）。

    出错时本函数 rollback 业务事务后单独写一条 tick_log。
    """
    bot = session.get(Bot, bot_id)
    if bot is None or bot.status != BotStatus.running:
        return

    try:
        if kline_source is not None:
            kline_source.ensure_latest_kline(session, bot.symbol, bot.interval)

        df = _load_history(session, bot.symbol, bot.interval, _OHLC_HISTORY_LIMIT)
        if df.empty or len(df) < 2:
            _write_log(session, bot_id, TickStatus.skipped, "insufficient OHLC")
            session.commit()
            return

        entry = STRATEGY_REGISTRY.get(bot.strategy_name)
        if entry is None:
            _write_log(session, bot_id, TickStatus.errored, f"unknown strategy: {bot.strategy_name}")
            bot.status = BotStatus.errored
            session.add(bot)
            session.commit()
            return

        signal = entry.fn(df, **bot.strategy_params)
        latest = int(signal.iloc[-1])
        mark_price = float(df["close"].iloc[-1])

        if latest == -1:
            logger.warning("bot_id=%s signal=-1 downgraded to 0 (no shorting in v1)", bot_id)
            latest = 0

        pos = session.get(Position, bot_id)
        side, qty = decide_order(latest, pos, mark_price=mark_price)
        if qty > 0:
            exchanges[bot.exchange.value].place_market_order(session, bot_id, side, qty, mark_price)

        _write_snapshot(session, bot_id, mark_price)
        _write_log(session, bot_id, TickStatus.success, f"signal={latest} qty={qty:.6f}")
        session.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("tick failed bot_id=%s", bot_id)
        session.rollback()
        _write_log(session, bot_id, TickStatus.errored, f"{type(exc).__name__}: {str(exc)[:400]}")
        bot = session.get(Bot, bot_id)
        if bot:
            bot.status = BotStatus.errored
            session.add(bot)
        session.commit()


def _load_history(session: Session, symbol: str, interval: str, limit: int) -> pd.DataFrame:
    """从 ohlc 表读取最近 limit 根 K 线，按时间升序返回 DataFrame。"""
    rows = session.exec(
        text(
            "SELECT open_time, open, high, low, close, volume "
            "FROM ohlc WHERE symbol = :symbol AND interval = :interval "
            "ORDER BY open_time DESC LIMIT :limit"
        ).bindparams(symbol=symbol, interval=interval, limit=limit)
    ).all()
    if not rows:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    df = pd.DataFrame(rows, columns=["open_time", "open", "high", "low", "close", "volume"])
    df["open_time"] = pd.to_datetime(df["open_time"], utc=True)
    return df.set_index("open_time").sort_index()


def _write_snapshot(session: Session, bot_id: int, mark_price: float) -> None:
    """计算并写入当前权益快照。"""
    pos = session.get(Position, bot_id)
    bot = session.get(Bot, bot_id)
    equity = pos.cash + pos.base_qty * mark_price
    avg = pos.avg_entry_price if pos.avg_entry_price is not None else mark_price
    unrealized = (mark_price - avg) * pos.base_qty if pos.base_qty else 0.0
    realized = equity - bot.initial_capital - unrealized
    session.add(PnLSnapshot(
        bot_id=bot_id, snapshot_at=utcnow_iso(),
        mark_price=mark_price, equity=equity,
        unrealized_pnl=unrealized, realized_pnl=realized,
    ))


def _write_log(session: Session, bot_id: int, status: TickStatus, message: str) -> None:
    """写入一条 tick 日志记录。"""
    session.add(TickLog(bot_id=bot_id, status=status, message=message[:500]))
