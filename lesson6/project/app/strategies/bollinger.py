"""Bollinger 均值回归：close 跌破下轨做多，回到中轨平仓。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def bollinger(
    df: pd.DataFrame,
    period: int = 20,
    std: float = 2.0,
) -> pd.Series:
    if len(df) < period:
        return pd.Series(0, index=df.index)

    close = df["close"].shift(1)
    mid = close.rolling(period, min_periods=period).mean()
    sd = close.rolling(period, min_periods=period).std()
    lower = mid - std * sd

    sig = pd.Series(np.nan, index=df.index)
    sig[close < lower] = 1.0
    sig[close >= mid] = 0.0
    sig = sig.ffill().fillna(0).astype(int)
    return sig
