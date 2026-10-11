"""
双均线交叉策略。

短均线（默认 7 日）上穿长均线（默认 14 日）→ 信号 +1（做多）；
短均线下穿长均线 → 信号 0（空仓，不做空）；
其他时刻维持上一日信号。

实现按 openspec/changes/add-dual-ma-strategy/{specs,design}.md 落地。
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def dual_ma(
    df: pd.DataFrame,
    short_window: int = 7,
    long_window: int = 14,
) -> pd.Series:
    """双均线交叉信号。返回 Series，值 ∈ {0, +1}。

    防 lookahead：均线先 shift(1) 再比较，确保信号只基于昨日及以前。
    """
    if len(df) < long_window:
        # 数据不足以形成长均线，全程空仓
        return pd.Series(0, index=df.index)

    # shift(1) 后再 rolling，等价于"截至昨日"的均线
    ma_short = df["close"].shift(1).rolling(short_window).mean()
    ma_long = df["close"].shift(1).rolling(long_window).mean()

    ma_short_prev = ma_short.shift(1)
    ma_long_prev = ma_long.shift(1)

    cross_up = (ma_short > ma_long) & (ma_short_prev <= ma_long_prev)
    cross_dn = (ma_short < ma_long) & (ma_short_prev >= ma_long_prev)

    # 在交叉点写入信号；其他位置 NaN
    sig = pd.Series(np.nan, index=df.index)
    sig[cross_up] = 1.0
    sig[cross_dn] = 0.0
    # 前向填充 = 持仓维持；起始空仓
    sig = sig.ffill().fillna(0).astype(int)
    return sig


if __name__ == "__main__":
    # 自测：按 tasks.md §3
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from backtest import run_backtest

    res = run_backtest(dual_ma)
    print(res["summary"])
