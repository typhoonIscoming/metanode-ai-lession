"""Binance Testnet 实测：需要环境变量里有 testnet 凭证才跑，否则全部 skip。"""

from __future__ import annotations

import os

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.exchange.base import OrderSide
from app.exchange.binance_testnet import BinanceTestnetExchange
from app.models import Bot, BotStatus, Position
from app.models import Exchange as ExchangeEnum

REQUIRES_TESTNET = pytest.mark.skipif(
    not os.environ.get("BINANCE_TESTNET_API_KEY"),
    reason="set BINANCE_TESTNET_API_KEY / SECRET to run testnet smoke tests",
)


@pytest.fixture
def session(tmp_path):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        bot = Bot(
            name="testnet-smoke", strategy_name="dual_ma", strategy_params={},
            symbol="BTCUSDT", interval="1h", exchange=ExchangeEnum.binance_testnet,
            status=BotStatus.stopped, initial_capital=0.0,
        )
        s.add(bot)
        s.commit()
        s.refresh(bot)
        s.add(Position(bot_id=bot.id, cash=0.0, base_qty=0.0, avg_entry_price=None))
        s.commit()
        yield s, bot.id


@REQUIRES_TESTNET
def test_testnet_get_balance(session):
    s, bot_id = session
    ex = BinanceTestnetExchange()
    bal = ex.get_balance(s, bot_id)
    assert bal.cash >= 0


@REQUIRES_TESTNET
def test_testnet_place_tiny_buy_and_sell(session):
    s, bot_id = session
    ex = BinanceTestnetExchange()
    buy = ex.place_market_order(s, bot_id, OrderSide.buy, qty=0.001, mark_price=0.0)
    assert buy.status.value in {"filled", "rejected"}
    if buy.status.value == "filled":
        sell = ex.place_market_order(s, bot_id, OrderSide.sell, qty=0.001, mark_price=0.0)
        assert sell.status.value in {"filled", "rejected"}
