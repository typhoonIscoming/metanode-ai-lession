"""
最小回测引擎。

设计目标：
- 入口函数 run_backtest(strategy, ...) 接受一个策略 callable，返回结构化结果
- 不依赖第三方回测框架，纯 pandas/numpy 实现，便于阅读和教学
- 数据源：本目录的 prices.db ohlc 表（lesson3 已 seed）

策略 callable 约定：
    def strategy(df: pd.DataFrame) -> pd.Series
    输入：DataFrame，索引为 open_time，列至少含 open/high/low/close/volume
    输出：Series，索引同 df，值为 +1（满仓做多）/ 0（空仓）/ -1（满仓做空）

输出 dict 字段：
    sharpe                 年化夏普比（按日 K 线 ×sqrt(252)）
    max_drawdown           最大回撤（小数，例如 -0.18 = -18%）
    win_rate               日胜率（信号 != 0 的日子里，策略当日收益为正的比例）
    cumulative_return      累计收益（小数，1 + 累计收益曲线最末值 - 1）
    png_path               累计收益曲线 PNG 的绝对路径
    summary                中文文字总结，约 100-150 字
    rows                   参与回测的 K 线行数
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")  # headless 后端，避免在 WSL/CI 报 DISPLAY
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DB_PATH = Path(__file__).parent / "prices.db"
TRADING_DAYS_PER_YEAR = 252  # 年化常数；加密 24/7 实际 365，但为和股票约定对齐取 252


@dataclass
class BacktestResult:
    """结构化结果；run_backtest 返回 dict 形式以方便 JSON 序列化。"""

    sharpe: float
    max_drawdown: float
    win_rate: float
    cumulative_return: float
    png_path: str
    summary: str
    rows: int


def load_ohlc(symbol: str, interval: str, limit: int) -> pd.DataFrame:
    """从 prices.db 读取最近 limit 行该 symbol 的 OHLC，按时间升序返回。

    interval 当前不使用（lesson3 seed 只存了 1d；预留参数为后续多粒度做准备）。
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            "SELECT open_time, open, high, low, close, volume "
            "FROM ohlc WHERE symbol = ? "
            "ORDER BY open_time DESC LIMIT ?",
            conn,
            params=(symbol, limit),
        )
    finally:
        conn.close()
    if df.empty:
        raise ValueError(f"prices.db 没有 {symbol} 的数据；先跑 python seed_db.py")
    df["open_time"] = pd.to_datetime(df["open_time"], utc=True)
    df = df.set_index("open_time").sort_index()
    return df


def run_backtest(
    strategy: Callable[[pd.DataFrame], pd.Series],
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 30,
    out_dir: Path | None = None,
) -> dict:
    """跑一次回测并把结果落到 out_dir/cum_<symbol>.png；返回结果 dict。"""
    df = load_ohlc(symbol, interval, limit)

    # 信号 / 收益
    signal = strategy(df).reindex(df.index).fillna(0).clip(-1, 1)
    daily_return = df["close"].pct_change().fillna(0)
    # 策略当日收益 = 昨日信号 × 今日收益（避免 lookahead bias）
    strategy_return = signal.shift(1).fillna(0) * daily_return
    cumulative = (1 + strategy_return).cumprod()

    # 指标
    sharpe = _sharpe(strategy_return)
    max_drawdown = _max_drawdown(cumulative)
    win_rate = _win_rate(signal, strategy_return)
    cumulative_return = float(cumulative.iloc[-1] - 1)

    # 画图
    if out_dir is None:
        out_dir = Path(__file__).parent
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / f"cum_{symbol}.png"
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(cumulative.index, cumulative.values, label=f"{symbol} strategy", linewidth=2)
    ax.axhline(1.0, linestyle="--", color="gray", linewidth=0.8, label="basis 1.0")
    ax.set_title(f"Cumulative return — {symbol} ({len(df)} bars)")
    ax.set_ylabel("cumulative")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(png_path, dpi=120)
    plt.close(fig)

    summary = _summary(symbol, len(df), sharpe, max_drawdown, win_rate, cumulative_return)

    return BacktestResult(
        sharpe=sharpe,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        cumulative_return=cumulative_return,
        png_path=str(png_path),
        summary=summary,
        rows=len(df),
    ).__dict__


# --- 指标 ---


def _sharpe(returns: pd.Series) -> float:
    """年化夏普比；空数据或方差为 0 时返回 0.0。"""
    r = returns.dropna()
    if len(r) < 2 or r.std() == 0:
        return 0.0
    return float(r.mean() / r.std() * np.sqrt(TRADING_DAYS_PER_YEAR))


def _max_drawdown(cumulative: pd.Series) -> float:
    """最大回撤，返回负数（例如 -0.18 = -18%）；曲线为空返回 0。"""
    if cumulative.empty:
        return 0.0
    peak = cumulative.cummax()
    drawdown = cumulative / peak - 1
    return float(drawdown.min())


def _win_rate(signal: pd.Series, strategy_return: pd.Series) -> float:
    """信号非零的日子里，策略当日收益 > 0 的比例。"""
    mask = signal.shift(1).fillna(0) != 0
    if not mask.any():
        return 0.0
    return float((strategy_return[mask] > 0).mean())


def _summary(
    symbol: str,
    rows: int,
    sharpe: float,
    max_dd: float,
    win_rate: float,
    cum: float,
) -> str:
    """生成约 100-150 字的中文总结。"""
    direction = "上涨" if cum >= 0 else "下跌"
    pct = lambda x: f"{x * 100:.2f}%"  # noqa: E731 — 局部别名提升可读性
    return (
        f"{symbol} 在最近 {rows} 根 K 线上的回测结果：累计{direction} {pct(cum)}，"
        f"年化夏普 {sharpe:.2f}，最大回撤 {pct(max_dd)}，"
        f"信号触发日胜率 {pct(win_rate)}。"
        f"{'夏普 > 1 说明风险调整后收益尚可' if sharpe >= 1 else '夏普 < 1 说明该策略与简单持仓相比并无显著优势'}，"
        f"配合曲线图可看到回撤分布，建议结合更长历史数据复跑确认稳健性。"
    )


if __name__ == "__main__":
    # CLI 自测：跑一次"始终满仓做多"策略
    def buy_and_hold(df: pd.DataFrame) -> pd.Series:
        return pd.Series(1, index=df.index)

    res = run_backtest(buy_and_hold)
    print(res["summary"])
    print(f"PNG: {res['png_path']}")
