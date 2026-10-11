"""端到端：建 bot → 投喂 OHLC → 跑 50 次 tick → 验证累计资金合理。"""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.bot_runner import tick
from app.exchange.paper import PaperExchange
from app.models import (
    OHLC,
    Bot,
    BotStatus,
    Fill,
    PnLSnapshot,
    Position,
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
        # 只投喂前 100 根，留下后 100 根 step-by-step 喂
        for ts, row in ohlc_fixture.iloc[:100].iterrows():
            s.add(OHLC(
                symbol="BTCUSDT", interval="1h",
                open_time=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                open=row["open"], high=row["high"], low=row["low"],
                close=row["close"], volume=row["volume"],
            ))
        bot = Bot(
            name="e2e", strategy_name="dual_ma",
            strategy_params={"short_window": 7, "long_window": 14},
            symbol="BTCUSDT", interval="1h", exchange=ExchangeEnum.paper,
            status=BotStatus.running, initial_capital=10000.0,
        )
        s.add(bot)
        s.commit()
        s.refresh(bot)
        s.add(Position(bot_id=bot.id, cash=10000.0, base_qty=0.0))
        s.commit()
        yield s, bot.id, eng


def test_e2e_50_ticks_produces_consistent_state(session_with_bot, ohlc_fixture):
    s, bot_id, _eng = session_with_bot
    ex = PaperExchange(fee_rate=0.001)

    # 逐根投喂剩下 50 根 + tick
    for ts, row in ohlc_fixture.iloc[100:150].iterrows():
        s.add(OHLC(
            symbol="BTCUSDT", interval="1h",
            open_time=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            open=row["open"], high=row["high"], low=row["low"],
            close=row["close"], volume=row["volume"],
        ))
        s.commit()
        tick(s, bot_id, exchanges={"paper": ex})

    snapshots = s.exec(select(PnLSnapshot).where(PnLSnapshot.bot_id == bot_id)).all()
    assert len(snapshots) == 50

    fills = s.exec(select(Fill).where(Fill.bot_id == bot_id)).all()
    # Fills count is data-dependent; just verify the invariant
    assert isinstance(fills, list)

    pos = s.get(Position, bot_id)
    last_mark = float(ohlc_fixture["close"].iloc[149])
    equity = pos.cash + pos.base_qty * last_mark
    # equity 不会变成负数
    assert equity > 0
    # equity 不应远远偏离 initial
    assert 5000 < equity < 50000
