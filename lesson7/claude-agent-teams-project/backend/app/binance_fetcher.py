"""Binance 24h 行情抓取器。

职责：
1. 调用 Binance 公开接口 `/api/v3/ticker/24hr` 获取全市场行情
2. 过滤出以 USDT 结尾的现货交易对，排除杠杆代币（UP/DOWN/BULL/BEAR）
3. 按 24h 计价货币成交量（quoteVolume）降序，取前 100
4. 维护内存中的上一次价格快照，计算相邻两次抓取之间的瞬时变化率
5. 返回 `SnapshotResponse`，附带本次/上次抓取的 UTC 毫秒时间戳

字段映射（Binance -> 契约）：
- symbol -> symbol
- symbol[:-4] -> baseAsset（去掉末尾 USDT，供前端 UI 显示）
- lastPrice -> price
- quoteVolume -> quoteVolume（24h USDT 成交额，作为色块大小依据）
- priceChangePercent -> priceChangePercent
- 相邻两次抓取价差/上次价 -> priceChangeRate
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from .models import SnapshotResponse, TokenSnapshot

# Binance 现货 24h 行情接口
BINANCE_24HR_URL = "https://api.binance.com/api/v3/ticker/24hr"

# 抓取超时（秒）
FETCH_TIMEOUT = 10.0

# 仅保留 quoteVolume 前 N 个交易对
TOP_N = 100

# 杠杆 / 衍生代币后缀（紧邻 USDT 出现，如 BTCUPUSDT / BTCDOWNUSDT）
LEVERAGED_SUFFIXES = ("UPUSDT", "DOWNUSDT", "BULLUSDT", "BEARUSDT")


def _is_eligible_symbol(symbol: str) -> bool:
    """判断 symbol 是否为「以 USDT 结尾的非杠杆现货」。

    规则：
    - 必须以 `USDT` 结尾
    - 不能以 `UPUSDT` / `DOWNUSDT` / `BULLUSDT` / `BEARUSDT` 结尾（杠杆代币）
    """
    if not symbol.endswith("USDT"):
        return False
    if symbol.endswith(LEVERAGED_SUFFIXES):
        return False
    return True


class BinanceFetcher:
    """Binance 行情抓取器。

    每次调用 `fetch()` 会：
    1. 拉取最新行情
    2. 与内部 `_last_snapshot`（上次的 symbol -> price 映射）对比，算变化率
    3. 用本次价格更新 `_last_snapshot`，并记录本次抓取时间为下一次的 previousFetchedAt
    """

    def __init__(self) -> None:
        # 上一次抓取的价格快照，键为 symbol，值为价格（float）
        self._last_snapshot: dict[str, float] = {}
        # 上一次抓取完成的 UTC 毫秒时间戳，首次为 None
        self._last_fetched_at: int | None = None

    @staticmethod
    def _now_ms() -> int:
        """返回当前 UTC 毫秒时间戳。"""
        return int(time.time() * 1000)

    async def fetch(self) -> SnapshotResponse:
        """抓取一次行情，返回 SnapshotResponse。

        遇到网络错误会向上抛出，由调用方（scheduler）决定是否重试。
        """
        # 1. 发起异步 HTTP 请求
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT) as client:
            resp = await client.get(BINANCE_24HR_URL)
            resp.raise_for_status()
            payload: list[dict[str, Any]] = resp.json()

        # 2. 过滤 + 排序 + 截断前 100
        eligible: list[dict[str, Any]] = [
            item for item in payload if _is_eligible_symbol(item.get("symbol", ""))
        ]
        # quoteVolume 是字符串形式的数字，需要先转 float 再排序
        eligible.sort(key=lambda x: float(x.get("quoteVolume", 0.0)), reverse=True)
        top_items = eligible[:TOP_N]

        # 3. 记录本次抓取时间，并构造 TokenSnapshot 列表
        fetched_at = self._now_ms()
        new_last_snapshot: dict[str, float] = {}
        tokens: list[TokenSnapshot] = []

        for item in top_items:
            symbol = item["symbol"]
            # baseAsset：去掉末尾 USDT 即可（前面已过滤过非 USDT 后缀）
            base_asset = symbol[:-4]
            price = float(item.get("lastPrice", 0.0))
            quote_volume = float(item.get("quoteVolume", 0.0))
            price_change_percent = float(item.get("priceChangePercent", 0.0))

            # 计算相邻两次抓取间的瞬时变化率
            # 首次抓取或上次没有该 symbol 时为 None
            prev_price = self._last_snapshot.get(symbol)
            if prev_price is not None and prev_price > 0:
                price_change_rate: float | None = (price - prev_price) / prev_price
            else:
                price_change_rate = None

            tokens.append(
                TokenSnapshot(
                    symbol=symbol,
                    baseAsset=base_asset,
                    price=price,
                    quoteVolume=quote_volume,
                    priceChangeRate=price_change_rate,
                    priceChangePercent=price_change_percent,
                )
            )
            new_last_snapshot[symbol] = price

        # 4. 组装响应，把当前作为下一次的 previousFetchedAt
        response = SnapshotResponse(
            fetchedAt=fetched_at,
            previousFetchedAt=self._last_fetched_at,
            tokens=tokens,
        )

        # 5. 更新内部状态（在最后才更新，避免抛异常时污染快照）
        self._last_snapshot = new_last_snapshot
        self._last_fetched_at = fetched_at

        return response
