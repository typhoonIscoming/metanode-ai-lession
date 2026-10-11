"""数据契约模型定义。

本模块定义后端 -> 前端的数据传输对象（DTO），所有时间字段统一使用
UTC 毫秒级 epoch 时间戳（`int(time.time() * 1000)`）。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TokenSnapshot(BaseModel):
    """单个交易对的快照数据。

    字段说明：
    - symbol: 交易对名称，如 BTCUSDT
    - baseAsset: 基础资产代码，如 BTC（从 symbol 去掉末尾 USDT 得到，前端 UI 显示用）
    - price: 当前最新价（USDT 计价）
    - quoteVolume: 24h 计价货币成交量（USDT），作为热力图色块大小的依据
    - priceChangeRate: 相邻两次抓取之间的瞬时变化率（小数，如 0.001 表示 +0.1%）
      首次抓取或上次没有该 symbol 时为 None
    - priceChangePercent: Binance 提供的 24h 涨跌幅（百分数，如 1.23 表示 +1.23%）
    """

    symbol: str = Field(..., description="交易对名称，如 BTCUSDT")
    baseAsset: str = Field(..., description="基础资产代码，如 BTC")
    price: float = Field(..., description="当前最新价（USDT 计价）")
    quoteVolume: float = Field(
        ...,
        description="24h 计价货币成交量（USDT），用于排序与色块大小",
    )
    priceChangeRate: float | None = Field(
        default=None,
        description="相邻两次抓取之间的瞬时变化率，首次为 None",
    )
    priceChangePercent: float = Field(
        ...,
        description="Binance 24h 涨跌幅，百分数",
    )


class SnapshotResponse(BaseModel):
    """一次完整抓取的快照响应。

    字段说明：
    - fetchedAt: 本次抓取完成的 UTC 毫秒时间戳
    - previousFetchedAt: 上一次抓取的 UTC 毫秒时间戳，首次为 None
    - tokens: 按 quoteVolume 降序排列的 token 快照列表（最多 100 个）
    """

    fetchedAt: int = Field(..., description="本次抓取完成时间，UTC 毫秒 epoch")
    previousFetchedAt: int | None = Field(
        default=None,
        description="上一次抓取完成时间，UTC 毫秒 epoch；首次为 None",
    )
    tokens: list[TokenSnapshot] = Field(
        default_factory=list,
        description="按 24h 成交量降序排列的交易对快照列表（最多 100）",
    )
