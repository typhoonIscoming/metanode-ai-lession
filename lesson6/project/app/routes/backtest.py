"""/backtest 表单 + 回测执行。

engine 通过 Depends(get_engine) 注入，测试时用 dependency_overrides 覆盖。
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.engine import Engine
from sqlmodel import Session

from app.backtest import run_backtest
from app.db import get_engine
from app.kline_fetcher import INTERVAL_SECONDS, ensure_range_in_db, iso_to_ts_ms
from app.strategies import STRATEGY_REGISTRY

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
_STATIC_DIR = Path("static")
_MAX_BARS = 200_000


def _normalize_datetime_local(s: str) -> str:
    """HTML5 datetime-local 是 'YYYY-MM-DDTHH:MM'（无 tz）。当 UTC 解释，补秒和 Z。"""
    if not s:
        return ""
    if len(s) == 16:  # YYYY-MM-DDTHH:MM
        s = s + ":00"
    if not s.endswith("Z") and "+" not in s:
        s = s + "Z"
    return s


def _estimate_bars(interval: str, start_iso: str, end_iso: str) -> int:
    start_ms = iso_to_ts_ms(start_iso)
    end_ms = iso_to_ts_ms(end_iso)
    step_ms = INTERVAL_SECONDS[interval] * 1000
    return max(0, (end_ms - start_ms) // step_ms + 1)


def _render_with_error(
    request: Request,
    error_msg: str,
    status_code: int = 400,
    **request_state,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "backtest.html",
        {
            "strategies": list(STRATEGY_REGISTRY.keys()),
            "result": None,
            "error_msg": error_msg,
            **request_state,
        },
        status_code=status_code,
    )


@router.get("/backtest", response_class=HTMLResponse)
async def backtest_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "backtest.html",
        {"strategies": list(STRATEGY_REGISTRY.keys()), "result": None},
    )


@router.post("/backtest", response_class=HTMLResponse)
async def backtest_run(
    request: Request,
    strategy_name: str = Form(...),
    symbol: str = Form("BTCUSDT"),
    interval: str = Form("1h"),
    limit: int = Form(100),
    params: str = Form("{}"),
    start_time: str = Form(""),
    end_time: str = Form(""),
    engine: Engine = Depends(get_engine),  # noqa: B008
) -> HTMLResponse:
    request_state = {
        "request_strategy": strategy_name,
        "request_symbol": symbol,
        "request_interval": interval,
        "request_limit": limit,
        "request_params": params,
        "request_start_time": start_time,
        "request_end_time": end_time,
    }

    entry = STRATEGY_REGISTRY.get(strategy_name)
    if entry is None:
        return _render_with_error(request, f"未知策略：{strategy_name}", **request_state)

    try:
        parsed = {**entry.defaults, **json.loads(params or "{}")}
    except json.JSONDecodeError:
        return _render_with_error(request, "参数 JSON 解析失败", **request_state)

    use_range = bool(start_time and end_time)
    start_iso: str | None = None
    end_iso: str | None = None
    if use_range:
        start_iso = _normalize_datetime_local(start_time)
        end_iso = _normalize_datetime_local(end_time)
        if start_iso >= end_iso:
            return _render_with_error(request, "起始时间不能晚于结束时间", **request_state)
        bars = _estimate_bars(interval, start_iso, end_iso)
        if bars > _MAX_BARS:
            return _render_with_error(
                request,
                f"时间范围过大（约 {bars} 根 K 线），最多支持 {_MAX_BARS} 根，请收窄",
                **request_state,
            )
        with Session(engine) as s:
            ensure_range_in_db(s, symbol, interval, start_iso, end_iso)

    try:
        result = run_backtest(
            entry.fn, symbol=symbol, interval=interval,
            limit=None if use_range else limit,
            out_dir=_STATIC_DIR, engine=engine,
            start_time=start_iso, end_time=end_iso,
            **parsed,
        )
    except ValueError as e:
        return _render_with_error(request, str(e), **request_state)

    png_path = Path(result["png_path"])
    static_png = _STATIC_DIR / png_path.name
    if png_path.resolve() != static_png.resolve():
        shutil.copy(png_path, static_png)
    result["png_name"] = png_path.name

    return templates.TemplateResponse(
        request,
        "backtest.html",
        {
            "strategies": list(STRATEGY_REGISTRY.keys()),
            "result": result,
            "request_strategy": strategy_name,
            "request_symbol": symbol,
            "request_interval": interval,
            "request_limit": limit,
            "request_params": params,
            "request_start_time": start_time,
            "request_end_time": end_time,
        },
    )
