"""最小回测引擎。

设计目标：
- 入口函数 run_backtest(strategy, ...) 接受一个策略 callable，返回结构化结果
- 不依赖第三方回测框架，纯 pandas/numpy 实现
- 数据源：quant.db 的 ohlc 表（多 symbol × 多 timeframe）

策略 callable 约定：
    def strategy(df: pd.DataFrame, **params) -> pd.Series
    输入：DataFrame，索引为 open_time（UTC tz-aware），列含 open/high/low/close/volume
    输出：Series，索引同 df，值 ∈ {-1, 0, +1}

输出 dict 字段：
    sharpe / max_drawdown / win_rate / cumulative_return / png_path / summary / rows
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless 后端
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import engine as default_engine

TRADING_PERIODS = {
    "1m": 365 * 24 * 60,
    "5m": 365 * 24 * 12,
    "15m": 365 * 24 * 4,
    "1h": 365 * 24,
    "4h": 365 * 6,
    "1d": 365,
}


@dataclass
class BacktestResult:
    sharpe: float
    max_drawdown: float
    win_rate: float
    cumulative_return: float
    png_path: str
    summary: str
    rows: int


def load_ohlc(
    symbol: str,
    interval: str,
    limit: int | None = None,
    engine: Engine | None = None,
    *,
    start_time: str | None = None,
    end_time: str | None = None,
) -> pd.DataFrame:
    """读 ohlc。

    两种模式：
    - 范围模式：start_time + end_time 都非空 → WHERE open_time BETWEEN ... AND ...
    - 行数模式：否则用 LIMIT N DESC，limit 必须非空
    优先级：范围模式 > 行数模式（同时提供时 limit 被忽略）
    """
    eng = engine or default_engine
    if start_time and end_time:
        query = text(
            "SELECT open_time, open, high, low, close, volume "
            "FROM ohlc WHERE symbol = :symbol AND interval = :interval "
            "AND open_time >= :start AND open_time <= :end "
            "ORDER BY open_time ASC"
        )
        sql_params = {"symbol": symbol, "interval": interval,
                      "start": start_time, "end": end_time}
    else:
        if limit is None:
            raise ValueError("load_ohlc 需要 limit 或 start_time+end_time")
        query = text(
            "SELECT open_time, open, high, low, close, volume "
            "FROM ohlc WHERE symbol = :symbol AND interval = :interval "
            "ORDER BY open_time DESC LIMIT :limit"
        )
        sql_params = {"symbol": symbol, "interval": interval, "limit": limit}

    with eng.connect() as conn:
        df = pd.read_sql_query(query, conn, params=sql_params)
    if df.empty:
        raise ValueError(
            f"ohlc 表里没有 {symbol} {interval} 在所选范围内的数据；"
            f"先跑 scripts/seed_db.py 或在 backtest 表单填合理的范围"
        )
    df["open_time"] = pd.to_datetime(df["open_time"], utc=True)
    df = df.set_index("open_time").sort_index()
    return df


def run_backtest(
    strategy: Callable[..., pd.Series],
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int | None = 30,
    out_dir: Path | None = None,
    engine: Engine | None = None,
    *,
    start_time: str | None = None,
    end_time: str | None = None,
    **strategy_params,
) -> dict:
    """跑一次回测，把累计曲线写到 out_dir/cum_<symbol>_<interval>.png；返回结果 dict。"""
    df = load_ohlc(
        symbol, interval, limit=limit, engine=engine,
        start_time=start_time, end_time=end_time,
    )

    signal = strategy(df, **strategy_params).reindex(df.index).fillna(0).clip(-1, 1)
    daily_return = df["close"].pct_change().fillna(0)
    strategy_return = signal.shift(1).fillna(0) * daily_return
    cumulative = (1 + strategy_return).cumprod()

    periods = TRADING_PERIODS.get(interval, 252)
    sharpe = _sharpe(strategy_return, periods=periods)
    max_drawdown = _max_drawdown(cumulative)
    win_rate = _win_rate(signal, strategy_return)
    cumulative_return = float(cumulative.iloc[-1] - 1)

    if out_dir is None:
        out_dir = Path(__file__).parent.parent
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if start_time and end_time:
        s_short = start_time[:10].replace("-", "")
        e_short = end_time[:10].replace("-", "")
        png_path = out_dir / f"cum_{symbol}_{interval}_{s_short}_{e_short}.png"
    else:
        png_path = out_dir / f"cum_{symbol}_{interval}.png"

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(cumulative.index, cumulative.values, label=f"{symbol} {interval}", linewidth=2)
    ax.axhline(1.0, linestyle="--", color="gray", linewidth=0.8, label="basis 1.0")
    ax.set_title(f"Cumulative return — {symbol} {interval} ({len(df)} bars)")
    ax.set_ylabel("cumulative")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(png_path, dpi=120)
    plt.close(fig)

    summary = _summary(symbol, interval, len(df), sharpe, max_drawdown, win_rate, cumulative_return)

    return BacktestResult(
        sharpe=sharpe, max_drawdown=max_drawdown, win_rate=win_rate,
        cumulative_return=cumulative_return, png_path=str(png_path),
        summary=summary, rows=len(df),
    ).__dict__


def _sharpe(returns: pd.Series, periods: int = 252) -> float:
    r = returns.dropna()
    if len(r) < 2 or r.std() == 0:
        return 0.0
    return float(r.mean() / r.std() * np.sqrt(periods))


def _max_drawdown(cumulative: pd.Series) -> float:
    if cumulative.empty:
        return 0.0
    peak = cumulative.cummax()
    drawdown = cumulative / peak - 1
    return float(drawdown.min())


def _win_rate(signal: pd.Series, strategy_return: pd.Series) -> float:
    mask = signal.shift(1).fillna(0) != 0
    if not mask.any():
        return 0.0
    return float((strategy_return[mask] > 0).mean())


def _summary(
    symbol: str, interval: str, rows: int,
    sharpe: float, max_dd: float, win_rate: float, cum: float,
) -> str:
    direction = "上涨" if cum >= 0 else "下跌"
    pct = lambda x: f"{x * 100:.2f}%"  # noqa: E731
    return (
        f"{symbol} {interval} 在最近 {rows} 根 K 线上的回测结果：累计{direction} {pct(cum)}，"
        f"年化夏普 {sharpe:.2f}，最大回撤 {pct(max_dd)}，"
        f"信号触发日胜率 {pct(win_rate)}。"
        f"{'夏普 > 1 说明风险调整后收益尚可' if sharpe >= 1 else '夏普 < 1 说明相对持有并无显著优势'}。"
    )


if __name__ == "__main__":
    # CLI 自测：跑一次"始终满仓做多"策略
    def buy_and_hold(df: pd.DataFrame) -> pd.Series:
        return pd.Series(1, index=df.index)

    res = run_backtest(buy_and_hold)
    print(res["summary"])
    print(f"PNG: {res['png_path']}")
