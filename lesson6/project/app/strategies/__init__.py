"""quant-trader 策略库。

所有策略统一签名：def strategy(df: pd.DataFrame, **params) -> pd.Series
返回 Series ∈ {-1, 0, +1}（v1 实现的都是 0 / +1）。
"""

from app.strategies.bollinger import bollinger
from app.strategies.dual_ma import dual_ma
from app.strategies.macd import macd
from app.strategies.registry import STRATEGY_REGISTRY, StrategyEntry
from app.strategies.rsi import rsi

__all__ = [
    "STRATEGY_REGISTRY",
    "StrategyEntry",
    "bollinger",
    "dual_ma",
    "macd",
    "rsi",
]
