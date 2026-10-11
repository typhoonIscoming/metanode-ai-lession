"""
示例策略，给学员当模板复制改写。
两个策略都满足 backtest.run_backtest 的 callable 签名。
"""

import pandas as pd


def buy_and_hold(df: pd.DataFrame) -> pd.Series:
    """始终满仓做多。基线策略，等价于直接持有 BTC。"""
    return pd.Series(1, index=df.index)


def ma_crossover_7(df: pd.DataFrame) -> pd.Series:
    """收盘价高于 7 日均线时做多，否则空仓。最简单的趋势跟踪示例。"""
    ma7 = df["close"].rolling(7).mean()
    # 注意：MA 在前 6 个 bar 上是 NaN，对应信号置 0（空仓）
    return (df["close"] > ma7).astype(int).fillna(0)
