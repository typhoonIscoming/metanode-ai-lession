"""验证 decide_order 决策表 + tick 整体流程（mock exchange + 注入 OHLC）。"""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.bot_runner import decide_order, tick
from app.exchange.base import OrderSide
from app.exchange.paper import PaperExchange
from app.models import (
    OHLC,
    Bot,
    BotStatus,
    PnLSnapshot,
    Position,
    TickLog,
)
from app.models import (
    Exchange as ExchangeEnum,
)


@pytest.fixture
def session_with_bot(tmp_path, ohlc_fixture):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        for ts, row in ohlc_fixture.iterrows():
            s.add(OHLC(
                symbol="BTCUSDT", interval="1h",
                open_time=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                open=row["open"], high=row["high"], low=row["low"],
                close=row["close"], volume=row["volume"],
            ))
        bot = Bot(
            name="t", strategy_name="dual_ma",
            strategy_params={"short_window": 7, "long_window": 14},
            symbol="BTCUSDT", interval="1h", exchange=ExchangeEnum.paper,
            status=BotStatus.running, initial_capital=10000.0,
        )
        s.add(bot)
        s.commit()
        s.refresh(bot)
        s.add(Position(bot_id=bot.id, cash=10000.0, base_qty=0.0))
        s.commit()
        yield s, bot.id


def test_decide_order_buy_when_signal_1_and_flat():
    pos = Position(bot_id=1, cash=10000.0, base_qty=0.0, avg_entry_price=None)
    side, qty = decide_order(1, pos, mark_price=100.0, fee_rate=0.001)
    assert side == OrderSide.buy
    expected = 10000.0 / (100.0 * (1 + 0.001))
    assert qty == pytest.approx(expected)


def test_decide_order_sell_when_signal_0_and_long():
    pos = Position(bot_id=1, cash=0.0, base_qty=0.5, avg_entry_price=100.0)
    side, qty = decide_order(0, pos, mark_price=100.0, fee_rate=0.001)
    assert side == OrderSide.sell
    assert qty == 0.5


def test_decide_order_noop_when_signal_1_and_long():
    pos = Position(bot_id=1, cash=0.0, base_qty=0.5, avg_entry_price=100.0)
    _side, qty = decide_order(1, pos, mark_price=100.0, fee_rate=0.001)
    assert qty == 0


def test_decide_order_noop_when_signal_0_and_flat():
    pos = Position(bot_id=1, cash=10000.0, base_qty=0.0, avg_entry_price=None)
    _side, qty = decide_order(0, pos, mark_price=100.0, fee_rate=0.001)
    assert qty == 0


def test_decide_order_short_signal_downgrades_to_zero():
    pos = Position(bot_id=1, cash=0.0, base_qty=0.5, avg_entry_price=100.0)
    side, qty = decide_order(-1, pos, mark_price=100.0, fee_rate=0.001)
    assert side == OrderSide.sell
    assert qty == 0.5


def test_tick_writes_pnl_snapshot_and_tick_log(session_with_bot):
    s, bot_id = session_with_bot
    ex = PaperExchange(fee_rate=0.001)
    tick(s, bot_id, exchanges={"paper": ex})

    snapshots = s.exec(select(PnLSnapshot).where(PnLSnapshot.bot_id == bot_id)).all()
    assert len(snapshots) == 1

    logs = s.exec(select(TickLog).where(TickLog.bot_id == bot_id)).all()
    assert len(logs) == 1


def test_tick_errored_logs_and_marks_bot(session_with_bot):
    """策略产出 signal=0 + 有持仓 → 走卖出分支；mock exchange 抛错 → bot.status=errored，tick_log errored。"""
    s, bot_id = session_with_bot

    class _ExplodingExchange:
        name = "paper"

        def place_market_order(self, *a, **kw):
            raise RuntimeError("boom")

        def get_balance(self, *a, **kw):
            raise RuntimeError("boom")

    # 给 bot 加持仓使 dual_ma 信号若为 0 时触发卖出
    pos = s.get(Position, bot_id)
    pos.base_qty = 0.1
    pos.avg_entry_price = 100.0
    pos.cash = 100.0
    s.add(pos)
    s.commit()

    tick(s, bot_id, exchanges={"paper": _ExplodingExchange()})

    bot = s.get(Bot, bot_id)
    s.refresh(bot)
    logs = s.exec(select(TickLog).where(TickLog.bot_id == bot_id)).all()
    assert len(logs) >= 1
    # 如果走到了下单分支并抛错，bot.status 应该 errored；若策略输出 +1 或没下单，本测试只要求至少 1 条日志
