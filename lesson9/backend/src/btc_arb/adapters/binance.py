"""Binance 现货价 + 历史 K 线（用于年化波动率）。"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import httpx

from btc_arb.logging import get_logger

logger = get_logger(__name__)

BINANCE_BASE = "https://api.binance.com"
SYMBOL = "BTCUSDT"


class BinanceError(Exception):
    """Binance 调用失败。"""


class BinanceClient:
    """轻量 BTC 现货 + 波动率取数器；带 60s spot 缓存。"""

    def __init__(self, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
        self._spot_cache: tuple[float, datetime] | None = None
        self._spot_cache_ttl = 60  # 秒

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> BinanceClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def fetch_spot_price(self) -> float:
        """BTCUSDT 现货价，带 60s 进程内缓存。失败抛 BinanceError。"""
        now = datetime.now(timezone.utc)
        if self._spot_cache is not None:
            price, ts = self._spot_cache
            if (now - ts).total_seconds() < self._spot_cache_ttl:
                return price
        try:
            resp = await self._client.get(
                f"{BINANCE_BASE}/api/v3/ticker/price",
                params={"symbol": SYMBOL},
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise BinanceError(f"ticker/price failed: {e}") from e
        data = resp.json()
        try:
            price = float(data["price"])
        except (KeyError, ValueError, TypeError) as e:
            raise BinanceError(f"ticker/price malformed: {data}") from e
        self._spot_cache = (price, now)
        return price

    async def fetch_realized_volatility(self, days: int = 30) -> float:
        """从最近 N 天日 K 线算年化已实现波动率。失败抛 BinanceError。

        计算：log(close_i / close_{i-1}) 的样本标准差 × sqrt(365)
        """
        try:
            resp = await self._client.get(
                f"{BINANCE_BASE}/api/v3/klines",
                params={"symbol": SYMBOL, "interval": "1d", "limit": str(days + 1)},
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise BinanceError(f"klines failed: {e}") from e
        rows = resp.json()
        if not isinstance(rows, list) or len(rows) < 2:
            raise BinanceError(f"klines returned too few rows: {len(rows) if isinstance(rows, list) else 'non-list'}")
        # klines: [open_time, open, high, low, close, vol, close_time, ...]
        closes = []
        for r in rows:
            try:
                closes.append(float(r[4]))
            except (IndexError, ValueError, TypeError):
                continue
        if len(closes) < 2:
            raise BinanceError("not enough valid closes to compute vol")
        log_rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
        n = len(log_rets)
        mean = sum(log_rets) / n
        var = sum((r - mean) ** 2 for r in log_rets) / (n - 1) if n > 1 else 0.0
        daily_vol = math.sqrt(var)
        return daily_vol * math.sqrt(365.0)
