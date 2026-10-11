"""K 线数据源：默认实现走 Binance public REST，可注入 fetcher 测试。

ensure_latest_kline(symbol, interval) 保证 ohlc 表里有该 (symbol, interval) 的最新一根 bar。
带 30s in-memory TTL，避免同分钟多 bot 重复拉。
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime

import httpx
from sqlmodel import Session

from app.models import OHLC

BINANCE_BASE = "https://api.binance.com"


def _binance_fetch(symbol: str, interval: str, limit: int) -> list[dict]:
    """默认 fetcher：拉 Binance public klines。"""
    resp = httpx.get(
        f"{BINANCE_BASE}/api/v3/klines",
        params={"symbol": symbol, "interval": interval, "limit": limit},
        timeout=15,
    )
    resp.raise_for_status()
    rows = []
    for r in resp.json():
        ts = datetime.fromtimestamp(int(r[0]) / 1000, tz=UTC)
        rows.append({
            "open_time": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open": float(r[1]), "high": float(r[2]), "low": float(r[3]),
            "close": float(r[4]), "volume": float(r[5]),
        })
    return rows


class KlineSource:
    def __init__(
        self,
        fetcher: Callable[[str, str, int], list[dict]] = _binance_fetch,
        cache_ttl: float = 30.0,
        history_limit: int = 200,
    ) -> None:
        self.fetcher = fetcher
        self.cache_ttl = cache_ttl
        self.history_limit = history_limit
        self._last_fetch: dict[tuple[str, str], float] = {}

    def ensure_latest_kline(self, session: Session, symbol: str, interval: str) -> None:
        key = (symbol, interval)
        now = time.monotonic()
        if key in self._last_fetch and (now - self._last_fetch[key]) < self.cache_ttl:
            return
        rows = self.fetcher(symbol, interval, self.history_limit)
        for row in rows:
            self._upsert(session, symbol, interval, row)
        session.commit()
        self._last_fetch[key] = now

    @staticmethod
    def _upsert(session: Session, symbol: str, interval: str, row: dict) -> None:
        existing = session.get(OHLC, (symbol, interval, row["open_time"]))
        if existing is None:
            session.add(OHLC(symbol=symbol, interval=interval, **row))
        else:
            existing.open = row["open"]
            existing.high = row["high"]
            existing.low = row["low"]
            existing.close = row["close"]
            existing.volume = row["volume"]
            session.add(existing)
