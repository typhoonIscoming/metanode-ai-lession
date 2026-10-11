"""验证 ensure_range_in_db 的 diff + 分块 + UPSERT 行为。

fetch_range 单测略——它是薄包装的 HTTP 调用，不在 v1.2 覆盖范围。
"""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.kline_fetcher import ensure_range_in_db, iso_to_ts_ms
from app.models import OHLC


@pytest.fixture
def session(tmp_path):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        yield s


def _stub_factory(rows_per_call):
    """构造一个 stub fetcher，按调用顺序返回预设的 rows 列表。"""
    calls = []

    def stub(symbol, interval, start_ts_ms, end_ts_ms):
        calls.append((symbol, interval, start_ts_ms, end_ts_ms))
        return rows_per_call.pop(0) if rows_per_call else []

    stub.calls = calls
    return stub


def _row(open_time_iso: str, close: float = 100.0) -> dict:
    return {
        "open_time": open_time_iso,
        "open": close, "high": close + 1, "low": close - 1,
        "close": close, "volume": 1000.0,
    }


def test_ensure_range_with_empty_db_inserts_all(session):
    rows = [_row("2025-01-01T00:00:00Z", 100),
            _row("2025-01-01T01:00:00Z", 101),
            _row("2025-01-01T02:00:00Z", 102)]
    stub = _stub_factory([rows])

    n = ensure_range_in_db(
        session, "BTCUSDT", "1h",
        "2025-01-01T00:00:00Z", "2025-01-01T02:00:00Z",
        fetcher=stub,
    )
    assert n == 3
    assert len(stub.calls) == 1
    db_rows = session.exec(select(OHLC).where(OHLC.symbol == "BTCUSDT")).all()
    assert len(db_rows) == 3


def test_ensure_range_skips_existing(session):
    # DB 预置 2025-01-01T01:00:00Z 一条；范围要 00/01/02 三条
    session.add(OHLC(symbol="BTCUSDT", interval="1h",
                     open_time="2025-01-01T01:00:00Z",
                     open=200, high=201, low=199, close=200, volume=500))
    session.commit()

    # stub fetcher 应该被调 2 次（00:00 一段，02:00 一段，因为 01:00 已存在打断了连续区段）
    stub = _stub_factory([
        [_row("2025-01-01T00:00:00Z", 100)],
        [_row("2025-01-01T02:00:00Z", 102)],
    ])
    n = ensure_range_in_db(
        session, "BTCUSDT", "1h",
        "2025-01-01T00:00:00Z", "2025-01-01T02:00:00Z",
        fetcher=stub,
    )
    assert n == 2
    assert len(stub.calls) == 2
    rows = session.exec(select(OHLC).where(OHLC.symbol == "BTCUSDT").order_by(OHLC.open_time)).all()
    assert len(rows) == 3
    # 已有那条 close=200 没被改
    middle = next(r for r in rows if r.open_time == "2025-01-01T01:00:00Z")
    assert middle.close == 200


def test_ensure_range_all_present_does_not_call_fetcher(session):
    for hour in range(3):
        session.add(OHLC(symbol="BTCUSDT", interval="1h",
                         open_time=f"2025-01-01T0{hour}:00:00Z",
                         open=100, high=101, low=99, close=100, volume=500))
    session.commit()

    stub = _stub_factory([])
    n = ensure_range_in_db(
        session, "BTCUSDT", "1h",
        "2025-01-01T00:00:00Z", "2025-01-01T02:00:00Z",
        fetcher=stub,
    )
    assert n == 0
    assert stub.calls == []


def test_iso_to_ts_ms_round_trip():
    ts = iso_to_ts_ms("2025-01-01T00:00:00Z")
    assert ts == 1735689600000  # 2025-01-01 00:00 UTC in ms
