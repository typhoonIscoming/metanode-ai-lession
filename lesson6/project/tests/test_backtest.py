"""验证 run_backtest 在 stub OHLC 上的指标，及 shift(1) 防 lookahead。"""

from __future__ import annotations

import pandas as pd
import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.backtest import _max_drawdown, _sharpe, run_backtest
from app.models import OHLC


@pytest.fixture
def db_with_ohlc(tmp_path, ohlc_fixture):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        for ts, row in ohlc_fixture.iterrows():
            s.add(OHLC(
                symbol="BTCUSDT", interval="1h",
                open_time=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                open=row["open"], high=row["high"], low=row["low"],
                close=row["close"], volume=row["volume"],
            ))
        s.commit()
    return eng


def _buy_and_hold(df: pd.DataFrame) -> pd.Series:
    return pd.Series(1, index=df.index)


def test_run_backtest_buy_and_hold(db_with_ohlc, tmp_path):
    res = run_backtest(
        _buy_and_hold, symbol="BTCUSDT", interval="1h", limit=200,
        out_dir=tmp_path, engine=db_with_ohlc,
    )
    assert isinstance(res, dict)
    assert "sharpe" in res and "max_drawdown" in res and "win_rate" in res
    assert "cumulative_return" in res and "png_path" in res and "summary" in res
    assert res["rows"] == 200
    assert abs(res["cumulative_return"]) > 0


def test_sharpe_zero_when_zero_variance():
    flat = pd.Series([0.0] * 30)
    assert _sharpe(flat) == 0.0


def test_max_drawdown_monotonic_increasing():
    rising = pd.Series([1, 1.1, 1.2, 1.3, 1.4])
    assert _max_drawdown(rising) == 0.0


def test_max_drawdown_negative_after_peak():
    cumulative = pd.Series([1.0, 1.2, 0.8])
    assert pytest.approx(_max_drawdown(cumulative), rel=1e-6) == -1 / 3


def test_load_ohlc_by_range(db_with_ohlc):
    from app.backtest import load_ohlc
    # ohlc_fixture 第 0 根是 2025-01-01T00:00:00Z，hourly 200 根
    df = load_ohlc(
        "BTCUSDT", "1h", engine=db_with_ohlc,
        start_time="2025-01-01T01:00:00Z",
        end_time="2025-01-01T03:00:00Z",
    )
    # 范围内 3 根：01/02/03
    assert len(df) == 3
    times = [t.strftime("%Y-%m-%dT%H:%M:%SZ") for t in df.index]
    assert times == ["2025-01-01T01:00:00Z", "2025-01-01T02:00:00Z", "2025-01-01T03:00:00Z"]


def test_load_ohlc_range_overrides_limit(db_with_ohlc):
    from app.backtest import load_ohlc
    # 同时给 limit 和 range：以 range 为准
    df = load_ohlc(
        "BTCUSDT", "1h", limit=999, engine=db_with_ohlc,
        start_time="2025-01-01T00:00:00Z",
        end_time="2025-01-01T01:00:00Z",
    )
    assert len(df) == 2  # 00 和 01 两根，不是 999
