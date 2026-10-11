"""APScheduler 配置：4 个周期 job + JobRun 落表。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from btc_arb.db import get_session_factory
from btc_arb.logging import get_logger
from btc_arb.models.job_run import JobRun
from btc_arb.services.discovery import discover_markets
from btc_arb.services.notification import push_unpushed_signals
from btc_arb.services.prediction import predict_all_active
from btc_arb.services.price_monitor import poll_active_markets
from btc_arb.services.signal_engine import evaluate_all_active

logger = get_logger(__name__)


_scheduler: AsyncIOScheduler | None = None


async def _run_job(job_name: str, func: Callable[[AsyncSession], Awaitable[dict[str, Any]]]) -> None:
    """通用 job 包装器：开 session、跑业务、写 job_run 记录。"""
    factory = get_session_factory()
    started = datetime.now(timezone.utc)
    async with factory() as session:
        run = JobRun(job_name=job_name, status="running", started_at=started)
        session.add(run)
        await session.commit()
        await session.refresh(run)
        run_id = run.id

    try:
        async with factory() as session:
            stats = await func(session)
        async with factory() as session:
            run_db = await session.get(JobRun, run_id)
            if run_db:
                run_db.status = "success"
                run_db.finished_at = datetime.now(timezone.utc)
                run_db.stats = stats or {}
                await session.commit()
        logger.info("job.success", job=job_name, **(stats or {}))
    except Exception as e:  # noqa: BLE001
        async with factory() as session:
            run_db = await session.get(JobRun, run_id)
            if run_db:
                run_db.status = "failed"
                run_db.finished_at = datetime.now(timezone.utc)
                run_db.error = str(e)[:500]
                await session.commit()
        logger.error("job.failed", job=job_name, error=str(e))


async def _job_discover() -> None:
    await _run_job("discover_markets", discover_markets)


async def _job_predict() -> None:
    await _run_job("predict_all_active", predict_all_active)


async def _job_price_poll() -> None:
    await _run_job("poll_active_markets", poll_active_markets)


async def _job_signal_and_notify() -> None:
    # 信号引擎 + 通知串行（同一 tick 内决策完立刻推）
    await _run_job("evaluate_signals", evaluate_all_active)
    await _run_job("push_notifications", push_unpushed_signals)


def start_scheduler() -> AsyncIOScheduler:
    """构造并启动 scheduler；调用方负责在 lifespan 结束时 shutdown。"""
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    sched = AsyncIOScheduler(timezone="UTC")

    # 每日 00:30 UTC 拉一次 BTC 每日价格 event（target = today+N）
    # 该 event 一天只发一次，无需 hourly
    sched.add_job(_job_discover, CronTrigger(hour=0, minute=30), id="discover", replace_existing=True)
    # 启动后立即跑一次发现，避免冷启动空数据
    sched.add_job(_job_discover, "date", id="discover_bootstrap", replace_existing=True)
    # 预测：每 30 分钟跑（内部按 TTL 跳过新鲜的）
    sched.add_job(_job_predict, IntervalTrigger(minutes=30), id="predict", replace_existing=True)
    # 价格轮询：每 5 分钟一轮
    sched.add_job(_job_price_poll, IntervalTrigger(minutes=5), id="price_poll", replace_existing=True)
    # 信号引擎 + 通知：每 5 分钟，与价格轮询错峰（jitter）
    sched.add_job(
        _job_signal_and_notify, IntervalTrigger(minutes=5, jitter=10),
        id="signal_notify", replace_existing=True,
    )

    sched.start()
    _scheduler = sched
    logger.info("scheduler.started", jobs=[j.id for j in sched.get_jobs()])
    return sched


async def stop_scheduler() -> None:
    """优雅停止 scheduler；幂等。"""
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("scheduler.stopped")


def get_scheduler() -> AsyncIOScheduler | None:
    """供路由查询当前 scheduler 状态。"""
    return _scheduler
