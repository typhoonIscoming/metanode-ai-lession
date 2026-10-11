"""验证 7 张表能创建、能插入、能查询。"""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import (
    OHLC,
    Bot,
    BotStatus,
    Exchange,
    Fill,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)


@pytest.fixture
def engine(tmp_path):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    return eng


def test_create_all_tables(engine):
    expected = {"ohlc", "bots", "orders", "fills", "positions", "pnl_snapshots", "tick_log"}
    assert expected.issubset(set(SQLModel.metadata.tables.keys()))


def test_insert_and_query_ohlc(engine):
    with Session(engine) as s:
        s.add(OHLC(
            symbol="BTCUSDT", interval="1h", open_time="2026-05-17T00:00:00Z",
            open=100.0, high=110.0, low=95.0, close=105.0, volume=1000.0,
        ))
        s.commit()
        rows = s.exec(select(OHLC)).all()
        assert len(rows) == 1
        assert rows[0].close == 105.0


def test_insert_bot(engine):
    with Session(engine) as s:
        bot = Bot(
            name="ma-btc-1h",
            strategy_name="dual_ma",
            strategy_params={"short_window": 7, "long_window": 14},
            symbol="BTCUSDT",
            interval="1h",
            exchange=Exchange.paper,
            status=BotStatus.stopped,
            initial_capital=10000.0,
        )
        s.add(bot)
        s.commit()
        s.refresh(bot)
        assert bot.id is not None
        assert bot.strategy_params == {"short_window": 7, "long_window": 14}


def test_position_one_row_per_bot(engine):
    with Session(engine) as s:
        s.add(Position(bot_id=1, cash=10000.0, base_qty=0.0, avg_entry_price=None))
        s.commit()
        pos = s.get(Position, 1)
        assert pos.cash == 10000.0


def test_order_fill_relation(engine):
    with Session(engine) as s:
        order = Order(
            bot_id=1, side=OrderSide.buy, type=OrderType.market,
            quantity=0.5, status=OrderStatus.filled,
        )
        s.add(order)
        s.commit()
        s.refresh(order)
        s.add(Fill(order_id=order.id, bot_id=1, price=100.0, quantity=0.5, fee=0.05))
        s.commit()
        fills = s.exec(select(Fill).where(Fill.order_id == order.id)).all()
        assert len(fills) == 1
        assert fills[0].quantity == 0.5
