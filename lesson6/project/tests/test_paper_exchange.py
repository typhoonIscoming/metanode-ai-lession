"""验证 PaperExchange 行为：买入扣现金、卖出加现金、不足时 reject。"""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.exchange.base import OrderSide
from app.exchange.paper import PaperExchange
from app.models import Bot, BotStatus, OrderStatus, Position
from app.models import Exchange as ExchangeEnum


@pytest.fixture
def session(tmp_path):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        bot = Bot(
            name="t", strategy_name="dual_ma", strategy_params={},
            symbol="BTCUSDT", interval="1h", exchange=ExchangeEnum.paper,
            status=BotStatus.stopped, initial_capital=10000.0,
        )
        s.add(bot)
        s.commit()
        s.refresh(bot)
        s.add(Position(bot_id=bot.id, cash=10000.0, base_qty=0.0, avg_entry_price=None))
        s.commit()
        yield s, bot.id


def test_paper_buy_at_mark_price(session):
    s, bot_id = session
    ex = PaperExchange(fee_rate=0.001)
    order = ex.place_market_order(s, bot_id, OrderSide.buy, qty=0.1, mark_price=1000.0)
    assert order.status == OrderStatus.filled
    pos = s.get(Position, bot_id)
    assert pos.base_qty == 0.1
    assert pos.cash == pytest.approx(10000.0 - 100.0 - 0.1)
    assert pos.avg_entry_price == pytest.approx(1000.0)


def test_paper_sell_realizes_cash(session):
    s, bot_id = session
    ex = PaperExchange(fee_rate=0.001)
    ex.place_market_order(s, bot_id, OrderSide.buy, qty=0.1, mark_price=1000.0)
    ex.place_market_order(s, bot_id, OrderSide.sell, qty=0.1, mark_price=1100.0)
    pos = s.get(Position, bot_id)
    assert pos.base_qty == 0.0
    assert pos.avg_entry_price is None
    assert pos.cash == pytest.approx(10000.0 - 100.1 + 109.89)


def test_paper_insufficient_cash_rejected(session):
    s, bot_id = session
    ex = PaperExchange(fee_rate=0.001)
    order = ex.place_market_order(s, bot_id, OrderSide.buy, qty=100.0, mark_price=1000.0)
    assert order.status == OrderStatus.rejected
    pos = s.get(Position, bot_id)
    assert pos.base_qty == 0.0
    assert pos.cash == 10000.0


def test_paper_sell_more_than_held_rejected(session):
    s, bot_id = session
    ex = PaperExchange(fee_rate=0.001)
    order = ex.place_market_order(s, bot_id, OrderSide.sell, qty=0.5, mark_price=1000.0)
    assert order.status == OrderStatus.rejected
    pos = s.get(Position, bot_id)
    assert pos.base_qty == 0.0
