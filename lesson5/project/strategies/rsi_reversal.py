"""
RSI 反转策略。

逻辑：
- 计算 14 周期 RSI（默认；Wilder EWMA 平滑，alpha = 1/period）
- RSI 自下穿越 oversold（默认 30）→ 信号 +1（做多）
- RSI 自上穿越 overbought（默认 70）→ 信号 0（空仓，本策略 long-only）
- 其他时刻持仓维持（ffill）

防 lookahead：close 先 shift(1) 再算 diff —— 让"今日 RSI"实际是"截至昨日"的 RSI。
与 backtest.run_backtest 内部 signal.shift(1) 共同构成两层防护，结构与 dual_ma 完全对称。

实现按 openspec/changes/add-rsi-strategy/{specs/strategies/spec,design}.md 落地。
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _rsi(close: pd.Series, period: int) -> pd.Series:
    """Wilder RSI。返回索引同 close 的 Series；前若干根（EWM burn-in）为 NaN。"""
    # shift(1) 放在 diff 之前 —— 等价于"截至昨日"的价格变化
    delta = close.shift(1).diff()
    # 拆分正向（涨幅）与负向（跌幅），都用非负数表示
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    # Wilder 平滑等价于 α = 1/period 的 EWMA；adjust=False 与 TradingView/Binance 同源
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    # avg_loss == 0（极端单边）时用 NaN 替换避免除零；下游 cross 判断对 NaN 天然返回 False
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def rsi_reversal(
    df: pd.DataFrame,
    period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0,
) -> pd.Series:
    """RSI 反转策略。返回索引同 df 的整数 Series，取值 ∈ {0, +1}。

    数据不足（行数 < period + 1）时直接全 0，避免 EWM 全 NaN 让下游抛错。
    """
    if len(df) < period + 1:
        # 行数不足以让 EWM 起步，统一返回空仓
        return pd.Series(0, index=df.index, dtype=int)

    rsi = _rsi(df["close"], period)
    rsi_prev = rsi.shift(1)

    # 穿越事件：只在事件那一根 K 线给定 +1 / 0；其他时刻 NaN，后面 ffill 维持
    cross_up = (rsi > oversold) & (rsi_prev <= oversold)
    cross_dn = (rsi < overbought) & (rsi_prev >= overbought)

    sig = pd.Series(np.nan, index=df.index)
    sig[cross_up] = 1.0
    sig[cross_dn] = 0.0
    # ffill 维持仓位；fillna(0) 让起始期（RSI 还是 NaN）保持空仓
    sig = sig.ffill().fillna(0).astype(int)
    return sig


if __name__ == "__main__":
    # 自测：仿 dual_ma 末尾结构，跑一次默认参数回测
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from backtest import run_backtest

    res = run_backtest(rsi_reversal)
    print(res["summary"])
