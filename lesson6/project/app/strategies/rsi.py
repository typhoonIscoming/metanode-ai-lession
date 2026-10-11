"""RSI 策略：超卖（RSI < oversold）做多，超买（RSI > overbought）平仓。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(
    df: pd.DataFrame,
    period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0,
) -> pd.Series:
    if len(df) < period + 1:
        return pd.Series(0, index=df.index)

    close = df["close"].shift(1)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_value = 100 - 100 / (1 + rs)

    sig = pd.Series(np.nan, index=df.index)
    sig[rsi_value < oversold] = 1.0
    sig[rsi_value > overbought] = 0.0
    sig = sig.ffill().fillna(0).astype(int)
    return sig
