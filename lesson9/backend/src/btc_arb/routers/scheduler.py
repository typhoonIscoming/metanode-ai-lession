"""APScheduler 观测路由（real impl）。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_arb.db import get_session
from btc_arb.models.job_run import JobRun
from btc_arb.schemas.common import ItemsResponse
from btc_arb.scheduler import get_scheduler

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("/jobs", response_model=ItemsResponse[dict])
async def list_jobs() -> ItemsResponse[dict]:
    """已注册 job 列表与下一次触发时间。"""
    sched = get_scheduler()
    if sched is None:
        return ItemsResponse[dict](items=[])
    items: list[dict[str, Any]] = []
    for j in sched.get_jobs():
        # 与 frontend Zod SchedulerJobSchema 对齐：name / trigger / next_run_at
        items.append({
            "name": j.id,
            "trigger": str(j.trigger),
            "next_run_at": j.next_run_time.isoformat() if j.next_run_time else None,
        })
    return ItemsResponse[dict](items=items)


@router.get("/runs", response_model=ItemsResponse[dict])
async def list_runs(
    job_name: str | None = None,
    job_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> ItemsResponse[dict]:
    stmt = select(JobRun)
    if job_name:
        stmt = stmt.where(JobRun.job_name == job_name)
    if job_status:
        stmt = stmt.where(JobRun.status == job_status)
    stmt = stmt.order_by(JobRun.started_at.desc()).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return ItemsResponse[dict](items=[
        {
            "id": r.id,
            "job_name": r.job_name,
            "status": r.status,
            "started_at": r.started_at.isoformat(),
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "stats": r.stats,
            "error": r.error,
        }
        for r in rows
    ])


@router.post("/trigger", status_code=status.HTTP_200_OK)
async def trigger_job(body: dict[str, Any]) -> dict[str, Any]:
    """手动触发 job（demo 场景下用得到）。body: {"job_id": "discover" | "predict" | "price_poll" | "signal_notify"}"""
    sched = get_scheduler()
    if sched is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="scheduler not started")
    job_id = body.get("job_id")
    if not job_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="job_id required")
    job = sched.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"job not found: {job_id}")
    # APScheduler 不直接 trigger，但可以重新 schedule 一个 date job 立刻跑
    from datetime import datetime, timedelta, timezone
    sched.add_job(
        job.func, "date",
        run_date=datetime.now(timezone.utc) + timedelta(seconds=1),
        id=f"{job_id}_manual_{int(datetime.now(timezone.utc).timestamp())}",
    )
    return {"triggered": job_id}
