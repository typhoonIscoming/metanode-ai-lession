"""验证 ensure_latest_kline 的缓存 + UPSERT 行为。"""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.kline_source import KlineSource
from app.models import OHLC


class _StubBinance:
    """伪 Binance：固定返回 1 根 kline。"""

    def __init__(self, ohlc_row: dict) -> None:
        self.row = ohlc_row
        self.calls = 0

    def fetch(self, symbol: str, interval: str, limit: int) -> list[dict]:
        self.calls += 1
        return [self.row]


@pytest.fixture
def session(tmp_path):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        yield s


def test_ensure_latest_writes_row(session):
    stub = _StubBinance({
        "open_time": "2026-05-17T08:00:00Z",
        "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000.0,
    })
    ks = KlineSource(fetcher=stub.fetch, cache_ttl=30.0)
    ks.ensure_latest_kline(session, "BTCUSDT", "1h")
    rows = session.exec(select(OHLC).where(OHLC.symbol == "BTCUSDT")).all()
    assert len(rows) == 1
    assert rows[0].close == 105.0
    assert stub.calls == 1


def test_cache_skips_within_ttl(session):
    stub = _StubBinance({
        "open_time": "2026-05-17T08:00:00Z",
        "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000.0,
    })
    ks = KlineSource(fetcher=stub.fetch, cache_ttl=60.0)
    ks.ensure_latest_kline(session, "BTCUSDT", "1h")
    ks.ensure_latest_kline(session, "BTCUSDT", "1h")
    assert stub.calls == 1


def test_cache_per_symbol_interval(session):
    stub = _StubBinance({
        "open_time": "2026-05-17T08:00:00Z",
        "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000.0,
    })
    ks = KlineSource(fetcher=stub.fetch, cache_ttl=60.0)
    ks.ensure_latest_kline(session, "BTCUSDT", "1h")
    ks.ensure_latest_kline(session, "ETHUSDT", "1h")
    ks.ensure_latest_kline(session, "BTCUSDT", "5m")
    assert stub.calls == 3


def test_upsert_overwrites(session):
    stub_v1 = _StubBinance({
        "open_time": "2026-05-17T08:00:00Z",
        "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000.0,
    })
    ks1 = KlineSource(fetcher=stub_v1.fetch, cache_ttl=0.0)
    ks1.ensure_latest_kline(session, "BTCUSDT", "1h")

    stub_v2 = _StubBinance({
        "open_time": "2026-05-17T08:00:00Z",
        "open": 100.0, "high": 120.0, "low": 95.0, "close": 115.0, "volume": 2000.0,
    })
    ks2 = KlineSource(fetcher=stub_v2.fetch, cache_ttl=0.0)
    ks2.ensure_latest_kline(session, "BTCUSDT", "1h")

    rows = session.exec(select(OHLC).where(OHLC.symbol == "BTCUSDT")).all()
    assert len(rows) == 1
    assert rows[0].close == 115.0
