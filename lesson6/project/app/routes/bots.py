"""/bots 列表、创建、详情、启停。

Session 通过 Depends(get_session) 注入；测试用 dependency_overrides 替换。
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.db import get_session
from app.models import (
    Bot,
    BotStatus,
    Fill,
    PnLSnapshot,
    Position,
    TickLog,
)
from app.models import (
    Exchange as ExchangeEnum,
)
from app.strategies import STRATEGY_REGISTRY

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/bots")


@router.get("/bots", response_class=HTMLResponse)
async def bots_list(
    request: Request,
    session: Session = Depends(get_session),  # noqa: B008
) -> HTMLResponse:
    bots = session.exec(select(Bot).where(Bot.status != BotStatus.deleted).order_by(Bot.id)).all()
    positions = {p.bot_id: p for p in session.exec(select(Position)).all()}
    return templates.TemplateResponse(
        request,
        "bots_list.html",
        {"bots": bots, "strategies": list(STRATEGY_REGISTRY.keys()), "positions": positions},
    )


@router.get("/bots/partial", response_class=HTMLResponse)
async def bots_table_partial(
    request: Request,
    session: Session = Depends(get_session),  # noqa: B008
) -> HTMLResponse:
    bots = session.exec(select(Bot).where(Bot.status != BotStatus.deleted).order_by(Bot.id)).all()
    positions = {p.bot_id: p for p in session.exec(select(Position)).all()}
    return templates.TemplateResponse(request, "partials/bots_table.html", {"bots": bots, "positions": positions})


@router.post("/bots")
async def bots_create(
    name: str = Form(...),
    strategy_name: str = Form(...),
    symbol: str = Form("BTCUSDT"),
    interval: str = Form("1h"),
    exchange: str = Form("paper"),
    initial_capital: float = Form(10000.0),
    params: str = Form("{}"),
    session: Session = Depends(get_session),  # noqa: B008
) -> RedirectResponse:
    if strategy_name not in STRATEGY_REGISTRY:
        raise HTTPException(400, f"unknown strategy: {strategy_name}")
    try:
        parsed = json.loads(params or "{}")
    except json.JSONDecodeError as e:
        raise HTTPException(400, "params must be valid JSON") from e

    bot = Bot(
        name=name, strategy_name=strategy_name,
        strategy_params={**STRATEGY_REGISTRY[strategy_name].defaults, **parsed},
        symbol=symbol, interval=interval,
        exchange=ExchangeEnum(exchange),
        status=BotStatus.stopped, initial_capital=initial_capital,
    )
    session.add(bot)
    session.commit()
    session.refresh(bot)
    session.add(Position(bot_id=bot.id, cash=initial_capital, base_qty=0.0))
    session.commit()
    return RedirectResponse(url=f"/bots/{bot.id}", status_code=303)


@router.get("/bots/{bot_id}", response_class=HTMLResponse)
async def bot_detail(
    request: Request,
    bot_id: int,
    session: Session = Depends(get_session),  # noqa: B008
) -> HTMLResponse:
    bot = session.get(Bot, bot_id)
    if bot is None:
        raise HTTPException(404, "bot not found")
    position = session.get(Position, bot_id)
    fills = session.exec(
        select(Fill).where(Fill.bot_id == bot_id).order_by(Fill.filled_at.desc()).limit(20)
    ).all()
    tick_logs = session.exec(
        select(TickLog).where(TickLog.bot_id == bot_id).order_by(TickLog.tick_at.desc()).limit(20)
    ).all()
    snapshots = session.exec(
        select(PnLSnapshot)
        .where(PnLSnapshot.bot_id == bot_id)
        .order_by(PnLSnapshot.snapshot_at)
        .limit(200)
    ).all()
    equity_png_name = _render_equity_png(bot_id, snapshots)
    latest_equity = snapshots[-1].equity if snapshots else None
    pct_change = (
        (latest_equity - bot.initial_capital) / bot.initial_capital * 100
        if latest_equity is not None and bot.initial_capital
        else None
    )
    return templates.TemplateResponse(
        request,
        "bot_detail.html",
        {
            "bot": bot,
            "position": position,
            "fills": fills,
            "tick_logs": tick_logs,
            "equity_png_name": equity_png_name,
            "latest_equity": latest_equity,
            "pct_change": pct_change,
        },
    )


@router.post("/bots/{bot_id}/start")
async def bot_start(
    request: Request,
    bot_id: int,
    session: Session = Depends(get_session),  # noqa: B008
) -> HTMLResponse:
    scheduler = request.app.state.scheduler
    from app.main import _on_tick
    from app.scheduler import add_bot_job

    bot = session.get(Bot, bot_id)
    if bot is None:
        raise HTTPException(404)
    bot.status = BotStatus.running
    session.add(bot)
    session.commit()
    session.refresh(bot)
    add_bot_job(scheduler, bot, _on_tick)
    if not _is_htmx(request):
        return RedirectResponse(url=f"/bots/{bot_id}", status_code=303)
    bots = session.exec(select(Bot).where(Bot.status != BotStatus.deleted).order_by(Bot.id)).all()
    positions = {p.bot_id: p for p in session.exec(select(Position)).all()}
    return templates.TemplateResponse(request, "partials/bots_table.html", {"bots": bots, "positions": positions})


@router.post("/bots/{bot_id}/stop")
async def bot_stop(
    request: Request,
    bot_id: int,
    session: Session = Depends(get_session),  # noqa: B008
) -> HTMLResponse:
    scheduler = request.app.state.scheduler
    from app.scheduler import remove_bot_job

    bot = session.get(Bot, bot_id)
    if bot is None:
        raise HTTPException(404)
    bot.status = BotStatus.stopped
    session.add(bot)
    session.commit()
    remove_bot_job(scheduler, bot_id)
    if not _is_htmx(request):
        return RedirectResponse(url=f"/bots/{bot_id}", status_code=303)
    bots = session.exec(select(Bot).where(Bot.status != BotStatus.deleted).order_by(Bot.id)).all()
    positions = {p.bot_id: p for p in session.exec(select(Position)).all()}
    return templates.TemplateResponse(request, "partials/bots_table.html", {"bots": bots, "positions": positions})


@router.delete("/bots/{bot_id}")
async def bot_delete(
    request: Request,
    bot_id: int,
    session: Session = Depends(get_session),  # noqa: B008
) -> HTMLResponse:
    scheduler = request.app.state.scheduler
    from app.scheduler import remove_bot_job

    bot = session.get(Bot, bot_id)
    if bot is None:
        raise HTTPException(404)
    bot.status = BotStatus.deleted
    session.add(bot)
    session.commit()
    remove_bot_job(scheduler, bot_id)
    if not _is_htmx(request):
        return RedirectResponse(url="/bots", status_code=303)
    bots = session.exec(select(Bot).where(Bot.status != BotStatus.deleted).order_by(Bot.id)).all()
    positions = {p.bot_id: p for p in session.exec(select(Position)).all()}
    return templates.TemplateResponse(request, "partials/bots_table.html", {"bots": bots, "positions": positions})


def _is_htmx(request: Request) -> bool:
    """HTMX always sends 'HX-Request: true' header."""
    return request.headers.get("hx-request", "").lower() == "true"


def _render_equity_png(bot_id: int, snapshots: list) -> str | None:
    """画 equity 曲线写到 static/equity_<bot_id>.png；snapshots 为空返回 None。"""
    if not snapshots:
        return None
    import matplotlib

    matplotlib.use("Agg")
    from pathlib import Path

    import matplotlib.pyplot as plt

    static_dir = Path("static")
    static_dir.mkdir(parents=True, exist_ok=True)
    png_name = f"equity_{bot_id}.png"
    png_path = static_dir / png_name

    xs = list(range(len(snapshots)))
    ys = [s.equity for s in snapshots]

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(xs, ys, color="#2563eb", linewidth=2)
    ax.axhline(ys[0], linestyle="--", color="#94a3b8", linewidth=0.8, label="起点")
    ax.fill_between(xs, ys, ys[0], where=[y >= ys[0] for y in ys], color="#fee2e2", alpha=0.5)
    ax.fill_between(xs, ys, ys[0], where=[y < ys[0] for y in ys], color="#dcfce7", alpha=0.5)
    ax.set_title(f"Equity curve — bot {bot_id}")
    ax.set_xlabel("snapshot #")
    ax.set_ylabel("equity")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(png_path, dpi=120)
    plt.close(fig)
    return png_name
