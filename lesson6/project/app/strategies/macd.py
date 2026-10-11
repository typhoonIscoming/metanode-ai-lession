"""MACD 策略：MACD 线上穿 signal 线做多，下穿平仓。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.Series:
    if len(df) < slow + signal:
        return pd.Series(0, index=df.index)

    close = df["close"].shift(1)
    ema_fast = close.ewm(span=fast, adjust=False, min_periods=fast).mean()
    ema_slow = close.ewm(span=slow, adjust=False, min_periods=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()

    cross_up = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
    cross_dn = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))

    sig = pd.Series(np.nan, index=df.index)
    sig[cross_up] = 1.0
    sig[cross_dn] = 0.0
    sig = sig.ffill().fillna(0).astype(int)
    return sig
