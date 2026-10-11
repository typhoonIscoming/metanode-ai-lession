"""验证 4 个策略在 fixture OHLC 上产出预期 signal。"""

from __future__ import annotations

import pandas as pd
import pytest

from app.strategies import STRATEGY_REGISTRY, bollinger, dual_ma, macd, rsi


def _assert_signal_invariants(sig: pd.Series, df: pd.DataFrame) -> None:
    assert isinstance(sig, pd.Series)
    assert sig.index.equals(df.index)
    assert set(sig.dropna().unique()).issubset({-1, 0, 1})


def test_dual_ma_signal_invariants(ohlc_fixture):
    sig = dual_ma(ohlc_fixture, short_window=7, long_window=14)
    _assert_signal_invariants(sig, ohlc_fixture)
    assert (sig.iloc[:14] == 0).all()


def test_rsi_signal_invariants(ohlc_fixture):
    sig = rsi(ohlc_fixture, period=14, oversold=30, overbought=70)
    _assert_signal_invariants(sig, ohlc_fixture)
    assert (sig.iloc[:14] == 0).all()


def test_macd_signal_invariants(ohlc_fixture):
    sig = macd(ohlc_fixture, fast=12, slow=26, signal=9)
    _assert_signal_invariants(sig, ohlc_fixture)
    assert (sig.iloc[: 26 + 9] == 0).all()


def test_bollinger_signal_invariants(ohlc_fixture):
    sig = bollinger(ohlc_fixture, period=20, std=2.0)
    _assert_signal_invariants(sig, ohlc_fixture)
    assert (sig.iloc[:20] == 0).all()


def test_registry_has_four_strategies():
    assert set(STRATEGY_REGISTRY.keys()) == {"dual_ma", "rsi", "macd", "bollinger"}
    for _name, entry in STRATEGY_REGISTRY.items():
        assert callable(entry.fn)
        assert isinstance(entry.defaults, dict)


def test_registry_dual_ma_defaults():
    e = STRATEGY_REGISTRY["dual_ma"]
    assert e.defaults == {"short_window": 7, "long_window": 14}


@pytest.mark.parametrize("name", ["dual_ma", "rsi", "macd", "bollinger"])
def test_registry_strategy_runs_with_defaults(ohlc_fixture, name):
    e = STRATEGY_REGISTRY[name]
    sig = e.fn(ohlc_fixture, **e.defaults)
    _assert_signal_invariants(sig, ohlc_fixture)
