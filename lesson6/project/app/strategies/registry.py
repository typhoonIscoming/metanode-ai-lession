"""策略注册表：名字 → (callable, 默认参数)。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from app.strategies.bollinger import bollinger
from app.strategies.dual_ma import dual_ma
from app.strategies.macd import macd
from app.strategies.rsi import rsi


@dataclass(frozen=True)
class StrategyEntry:
    fn: Callable[..., pd.Series]
    defaults: dict


STRATEGY_REGISTRY: dict[str, StrategyEntry] = {
    "dual_ma":   StrategyEntry(fn=dual_ma,   defaults={"short_window": 7, "long_window": 14}),
    "rsi":       StrategyEntry(fn=rsi,       defaults={"period": 14, "oversold": 30, "overbought": 70}),
    "macd":      StrategyEntry(fn=macd,      defaults={"fast": 12, "slow": 26, "signal": 9}),
    "bollinger": StrategyEntry(fn=bollinger, defaults={"period": 20, "std": 2.0}),
}


STRATEGY_DESCRIPTIONS: dict[str, str] = {
    "dual_ma":   "双均线交叉：短均线上穿长均线时做多，下穿时清仓。趋势跟随。",
    "rsi":       "RSI 反转：相对强弱指数跌破超卖线做多，涨破超买线清仓。均值回归。",
    "macd":      "MACD 金叉：MACD 线上穿信号线做多，下穿清仓。中期趋势确认。",
    "bollinger": "布林带均值回归：收盘价跌破下轨做多，回到中轨清仓。震荡市策略。",
}
