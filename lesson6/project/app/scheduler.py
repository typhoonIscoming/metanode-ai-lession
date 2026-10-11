"""APScheduler 包装：把 bot 注册成 CronTrigger 任务。

调用方提供 on_tick(bot_id) 回调；scheduler 触发时调它。
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select

from app.models import Bot, BotStatus

logger = logging.getLogger(__name__)


_INTERVAL_CRON: dict[str, dict] = {
    "1m":  {"minute": "*",     "second": 5},
    "5m":  {"minute": "*/5",   "second": 5},
    "15m": {"minute": "*/15",  "second": 5},
    "1h":  {"minute": 0,       "second": 5},
}


def _build_cron_kwargs(interval: str) -> dict:
    if interval not in _INTERVAL_CRON:
        raise ValueError(f"unsupported interval: {interval}")
    return _INTERVAL_CRON[interval]


def add_bot_job(
    scheduler: AsyncIOScheduler,
    bot: Bot,
    on_tick: Callable[[int], None],
) -> None:
    """注册 bot 的 cron job；同 id 已存在则替换。"""
    job_id = f"bot-{bot.id}"
    trigger = CronTrigger(**_build_cron_kwargs(bot.interval))
    scheduler.add_job(
        on_tick,
        trigger=trigger,
        id=job_id,
        kwargs={"bot_id": bot.id},
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    logger.info("scheduler: added bot %s (%s)", bot.id, bot.interval)


def remove_bot_job(scheduler: AsyncIOScheduler, bot_id: int) -> None:
    job_id = f"bot-{bot_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info("scheduler: removed bot %s", bot_id)


def restore_running_bots_on_startup(
    scheduler: AsyncIOScheduler,
    session: Session,
    on_tick: Callable[[int], None],
) -> None:
    """启动时扫库，给所有 status=running 的 bot 重建 job。"""
    bots = session.exec(select(Bot).where(Bot.status == BotStatus.running)).all()
    for bot in bots:
        add_bot_job(scheduler, bot, on_tick)
    logger.info("scheduler: restored %d running bot(s) on startup", len(bots))
