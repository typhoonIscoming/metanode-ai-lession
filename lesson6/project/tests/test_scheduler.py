"""验证 scheduler 的 add/remove/restore 状态副作用。

不验真实定时触发（APScheduler 自己的事，不重复测）。
"""

from __future__ import annotations

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import Session, SQLModel, create_engine

from app.models import Bot, BotStatus
from app.models import Exchange as ExchangeEnum
from app.scheduler import (
    _build_cron_kwargs,
    add_bot_job,
    remove_bot_job,
    restore_running_bots_on_startup,
)


@pytest.fixture
def session(tmp_path):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        yield s


@pytest.fixture
def scheduler():
    sched = AsyncIOScheduler()
    yield sched
    if sched.running:
        sched.shutdown(wait=False)


def test_cron_kwargs_for_each_interval():
    assert _build_cron_kwargs("1m") == {"minute": "*", "second": 5}
    assert _build_cron_kwargs("5m") == {"minute": "*/5", "second": 5}
    assert _build_cron_kwargs("15m") == {"minute": "*/15", "second": 5}
    assert _build_cron_kwargs("1h") == {"minute": 0, "second": 5}


def test_cron_kwargs_rejects_unknown_interval():
    with pytest.raises(ValueError):
        _build_cron_kwargs("99m")


def test_add_and_remove_bot_job(scheduler, session):
    bot = Bot(
        id=1, name="t", strategy_name="dual_ma", strategy_params={},
        symbol="BTCUSDT", interval="1h", exchange=ExchangeEnum.paper,
        status=BotStatus.running, initial_capital=10000.0,
    )
    add_bot_job(scheduler, bot, on_tick=lambda bot_id: None)
    assert scheduler.get_job(f"bot-{bot.id}") is not None

    remove_bot_job(scheduler, bot.id)
    assert scheduler.get_job(f"bot-{bot.id}") is None


def test_restore_running_bots(scheduler, session):
    bot1 = Bot(name="a", strategy_name="dual_ma", strategy_params={},
               symbol="BTCUSDT", interval="1h", exchange=ExchangeEnum.paper,
               status=BotStatus.running, initial_capital=10000.0)
    bot2 = Bot(name="b", strategy_name="dual_ma", strategy_params={},
               symbol="ETHUSDT", interval="5m", exchange=ExchangeEnum.paper,
               status=BotStatus.stopped, initial_capital=5000.0)
    session.add(bot1)
    session.add(bot2)
    session.commit()
    session.refresh(bot1)
    session.refresh(bot2)

    restore_running_bots_on_startup(scheduler, session, on_tick=lambda bot_id: None)

    assert scheduler.get_job(f"bot-{bot1.id}") is not None
    assert scheduler.get_job(f"bot-{bot2.id}") is None
