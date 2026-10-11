"""共享测试 fixture。后续 task 持续扩。"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def ohlc_fixture() -> pd.DataFrame:
    """200 根确定性 OHLC，给策略 / 回测测试用。

    用 seed=42 的几何布朗运动生成，确保结果可重现。
    """
    np.random.seed(42)
    n = 200
    rets = np.random.normal(0.0005, 0.02, n)
    close = 100.0 * np.exp(np.cumsum(rets))
    high_noise = np.abs(np.random.normal(0, 0.005, n))
    low_noise = np.abs(np.random.normal(0, 0.005, n))
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) * (1 + high_noise)
    low = np.minimum(open_, close) * (1 - low_noise)
    volume = np.random.lognormal(15, 1, n)
    idx = pd.date_range("2025-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=idx,
    )
