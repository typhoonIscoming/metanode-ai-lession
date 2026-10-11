"""Binance kline 分页拉取 + UPSERT 进 ohlc 表的可复用底层。

供 /backtest 自定义时间段使用；KlineSource（live tick 路径）不变。
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import httpx
from sqlmodel import Session, select

from app.models import OHLC

BINANCE_BASE = "https://api.binance.com"

INTERVAL_SECONDS: dict[str, int] = {
    "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "2h": 7200, "4h": 14400, "6h": 21600, "8h": 28800, "12h": 43200,
    "1d": 86400, "3d": 259200, "1w": 604800,
}


def fetch_range(symbol: str, interval: str, start_ts_ms: int, end_ts_ms: int) -> list[dict]:
    """Binance public klines 按 1000-bar 分页拉 [start, end] 区间。"""
    rows: list[dict] = []
    cursor = start_ts_ms
    interval_ms = INTERVAL_SECONDS[interval] * 1000
    while cursor <= end_ts_ms:
        resp = httpx.get(
            f"{BINANCE_BASE}/api/v3/klines",
            params={
                "symbol": symbol, "interval": interval,
                "startTime": cursor, "endTime": end_ts_ms, "limit": 1000,
            },
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        for r in batch:
            ts = datetime.fromtimestamp(int(r[0]) / 1000, tz=UTC)
            rows.append({
                "open_time": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": float(r[1]), "high": float(r[2]), "low": float(r[3]),
                "close": float(r[4]), "volume": float(r[5]),
            })
        last_open_ms = int(batch[-1][0])
        cursor = last_open_ms + interval_ms
        if len(batch) < 1000:
            break
    return rows


def ensure_range_in_db(
    session: Session,
    symbol: str,
    interval: str,
    start_iso: str,
    end_iso: str,
    fetcher: Callable[[str, str, int, int], list[dict]] = fetch_range,
) -> int:
    """确保 [start_iso, end_iso] 内 ohlc 表全覆盖；返回新增/更新的 bar 数。

    算法：
      1. 查 DB 中该范围已有 open_time 集合
      2. 按 interval 步长枚举期望的 open_time 集合
      3. diff 出 missing；按连续段分块
      4. 每块调 fetcher 拉补；UPSERT 进 ohlc
    """
    interval_sec = INTERVAL_SECONDS[interval]
    step_ms = interval_sec * 1000
    start_ts = iso_to_ts_ms(start_iso)
    end_ts = iso_to_ts_ms(end_iso)

    existing_iso_rows = session.exec(
        select(OHLC.open_time).where(
            OHLC.symbol == symbol,
            OHLC.interval == interval,
            OHLC.open_time >= start_iso,
            OHLC.open_time <= end_iso,
        )
    ).all()
    existing_ts = {iso_to_ts_ms(t) for t in existing_iso_rows}

    aligned_start = (start_ts // step_ms) * step_ms
    expected = set(range(aligned_start, end_ts + 1, step_ms))
    missing = sorted(expected - existing_ts)
    if not missing:
        return 0

    # 按连续区段分块（连续 = 相邻差恰为一个 step）
    chunks: list[tuple[int, int]] = []
    chunk_start = missing[0]
    prev = missing[0]
    for ts in missing[1:]:
        if ts - prev > step_ms:
            chunks.append((chunk_start, prev))
            chunk_start = ts
        prev = ts
    chunks.append((chunk_start, prev))

    upserted = 0
    for c_start, c_end in chunks:
        rows = fetcher(symbol, interval, c_start, c_end)
        for row in rows:
            existing = session.get(OHLC, (symbol, interval, row["open_time"]))
            if existing is None:
                session.add(OHLC(symbol=symbol, interval=interval, **row))
            else:
                for k, v in row.items():
                    if k != "open_time":
                        setattr(existing, k, v)
                session.add(existing)
            upserted += 1
        session.commit()
    return upserted


def iso_to_ts_ms(iso: str) -> int:
    """'2025-01-01T00:00:00Z' or '2025-01-01T00:00:00+00:00' → ms since epoch."""
    s = iso.replace("Z", "+00:00")
    return int(datetime.fromisoformat(s).timestamp() * 1000)
