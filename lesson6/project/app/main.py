"""FastAPI 入口。

启动时：
- init_db()：创建 SQLModel 表（幂等）
- 启动 APScheduler
- restore_running_bots：扫库重建 cron jobs
关闭时：scheduler.shutdown(wait=True)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app.bot_runner import tick
from app.config import settings
from app.db import engine, init_db
from app.exchange.binance_testnet import BinanceTestnetExchange
from app.exchange.paper import PaperExchange
from app.kline_source import KlineSource
from app.scheduler import restore_running_bots_on_startup

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


# 全局单例：每个进程一份
_exchanges: dict = {"paper": PaperExchange(fee_rate=0.001)}
# Binance testnet 适配器需要 key；缺失时不注册，避免启动失败
if settings.binance_testnet_api_key and settings.binance_testnet_api_secret:
    _exchanges["binance_testnet"] = BinanceTestnetExchange()
_kline_source = KlineSource()


def _on_tick(bot_id: int) -> None:
    """APScheduler 触发回调；开 session，调 bot_runner.tick。"""
    with Session(engine) as session:
        tick(session, bot_id, exchanges=_exchanges, kline_source=_kline_source)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    jobstore = SQLAlchemyJobStore(url=settings.quant_db_url)
    scheduler = AsyncIOScheduler(jobstores={"default": jobstore})
    app.state.scheduler = scheduler
    with Session(engine) as session:
        restore_running_bots_on_startup(scheduler, session, _on_tick)
    scheduler.start()
    logger.info("scheduler started")
    yield
    scheduler.shutdown(wait=True)
    logger.info("scheduler stopped")


app = FastAPI(title="quant-trader", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


from app.routes.backtest import router as backtest_router  # noqa: E402
from app.routes.bots import router as bots_router  # noqa: E402
from app.routes.strategies import router as strategies_router  # noqa: E402

app.include_router(backtest_router)
app.include_router(bots_router)
app.include_router(strategies_router)
