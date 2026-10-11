"""
project/strategies/

每个策略一个文件，顶层导出与文件同名的函数。
所有策略遵循 .cursor/rules/strategy-conventions.mdc 的签名约束。
"""

from .dual_ma import dual_ma
from .rsi_reversal import rsi_reversal

__all__ = ["dual_ma", "rsi_reversal"]
