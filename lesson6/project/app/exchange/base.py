"""Exchange 接口与共用 DTO。

接口约定：
- 所有方法接受一个开启的 SQLModel Session，方法内部不开/不关 session（由调用者管事务）
- place_market_order 立即返回 Order；filled / rejected 在同一调用内决定
- mark_price 是"参考价"——paper 用它直接 fill，testnet 也传给 binance 作为参考但实际成交价由交易所给出
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlmodel import Session

# 复用 models.OrderSide / OrderStatus 避免重复定义
from app.models import Order, OrderSide, OrderStatus


@dataclass
class Balance:
    bot_id: int
    cash: float
    base_qty: float
    avg_entry_price: float | None


class Exchange(Protocol):
    name: str  # "paper" | "binance_testnet"

    def place_market_order(
        self,
        session: Session,
        bot_id: int,
        side: OrderSide,
        qty: float,
        mark_price: float,
    ) -> Order: ...

    def get_balance(self, session: Session, bot_id: int) -> Balance: ...


__all__ = ["Balance", "Exchange", "Order", "OrderSide", "OrderStatus"]
