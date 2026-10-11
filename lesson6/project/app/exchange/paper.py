"""内存撮合：以传入的 mark_price 立即成交。

不维护任何独立状态——所有数据都落在 positions / orders / fills 表里。
"""

from __future__ import annotations

from sqlmodel import Session

from app.exchange.base import Balance, OrderSide, OrderStatus
from app.models import Fill, Order, OrderType, Position


class PaperExchange:
    name = "paper"

    def __init__(self, fee_rate: float = 0.001) -> None:
        self.fee_rate = fee_rate

    def place_market_order(
        self,
        session: Session,
        bot_id: int,
        side: OrderSide,
        qty: float,
        mark_price: float,
    ) -> Order:
        pos = session.get(Position, bot_id)
        if pos is None:
            raise ValueError(f"Position 不存在 bot_id={bot_id}；启动 bot 时应已初始化")

        order = Order(bot_id=bot_id, side=side, type=OrderType.market, quantity=qty, status=OrderStatus.pending)
        session.add(order)
        session.flush()

        notional = qty * mark_price
        fee = notional * self.fee_rate

        if side == OrderSide.buy:
            if pos.cash < notional + fee:
                order.status = OrderStatus.rejected
                session.add(order)
                return order
            new_qty = pos.base_qty + qty
            if pos.base_qty == 0:
                new_avg = mark_price
            else:
                new_avg = (pos.base_qty * pos.avg_entry_price + qty * mark_price) / new_qty
            pos.cash -= notional + fee
            pos.base_qty = new_qty
            pos.avg_entry_price = new_avg

        else:  # sell
            if pos.base_qty < qty:
                order.status = OrderStatus.rejected
                session.add(order)
                return order
            new_qty = pos.base_qty - qty
            pos.cash += notional - fee
            pos.base_qty = new_qty
            pos.avg_entry_price = None if new_qty == 0 else pos.avg_entry_price

        order.status = OrderStatus.filled
        session.add(order)
        session.add(Fill(order_id=order.id, bot_id=bot_id, price=mark_price, quantity=qty, fee=fee))
        session.add(pos)
        return order

    def get_balance(self, session: Session, bot_id: int) -> Balance:
        pos = session.get(Position, bot_id)
        if pos is None:
            return Balance(bot_id=bot_id, cash=0.0, base_qty=0.0, avg_entry_price=None)
        return Balance(bot_id=bot_id, cash=pos.cash, base_qty=pos.base_qty, avg_entry_price=pos.avg_entry_price)
