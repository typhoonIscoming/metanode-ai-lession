"""Binance Testnet REST 适配器。

只用 spot 现货 testnet（testnet.binance.vision）；v1 不接 futures。
"""

from __future__ import annotations

import hashlib
import hmac
import time
import urllib.parse

import httpx
from sqlmodel import Session

from app.config import settings
from app.exchange.base import Balance, OrderSide, OrderStatus
from app.models import Bot, Fill, Order, OrderType, Position


class BinanceTestnetExchange:
    name = "binance_testnet"

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.binance_testnet_api_key
        self.api_secret = api_secret or settings.binance_testnet_api_secret
        self.base_url = base_url or settings.binance_testnet_base_url
        if not self.api_key or not self.api_secret:
            raise RuntimeError("Binance Testnet API key / secret 未配置；填 .env 后再试")
        self._client = httpx.Client(base_url=self.base_url, timeout=15)

    def _sign(self, params: dict) -> str:
        qs = urllib.parse.urlencode(params)
        sig = hmac.new(self.api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
        return f"{qs}&signature={sig}"

    def _signed_request(self, method: str, path: str, params: dict) -> dict:
        params = {**params, "timestamp": int(time.time() * 1000)}
        body = self._sign(params)
        headers = {"X-MBX-APIKEY": self.api_key}
        if method == "GET":
            resp = self._client.get(f"{path}?{body}", headers=headers)
        elif method == "POST":
            resp = self._client.post(
                path,
                content=body,
                headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
            )
        else:
            raise ValueError(method)
        resp.raise_for_status()
        return resp.json()

    def get_balance(self, session: Session, bot_id: int) -> Balance:
        data = self._signed_request("GET", "/api/v3/account", {})
        cash = 0.0
        base = 0.0
        for b in data.get("balances", []):
            if b["asset"] == "USDT":
                cash = float(b["free"])
            elif b["asset"] == "BTC":
                base = float(b["free"])
        pos = session.get(Position, bot_id)
        avg = pos.avg_entry_price if pos else None
        return Balance(bot_id=bot_id, cash=cash, base_qty=base, avg_entry_price=avg)

    def place_market_order(
        self,
        session: Session,
        bot_id: int,
        side: OrderSide,
        qty: float,
        mark_price: float,
    ) -> Order:
        order = Order(
            bot_id=bot_id, side=side, type=OrderType.market,
            quantity=qty, status=OrderStatus.pending,
        )
        session.add(order)
        session.flush()
        try:
            bot = session.get(Bot, bot_id)
            data = self._signed_request("POST", "/api/v3/order", {
                "symbol": bot.symbol,
                "side": side.value.upper(),
                "type": "MARKET",
                "quantity": f"{qty:.6f}",
            })
            fills_data = data.get("fills", [])
            if not fills_data:
                order.status = OrderStatus.rejected
                session.add(order)
                return order
            total_qty = sum(float(f["qty"]) for f in fills_data)
            total_cost = sum(float(f["qty"]) * float(f["price"]) for f in fills_data)
            avg_price = total_cost / total_qty if total_qty else 0.0
            total_fee = sum(float(f["commission"]) for f in fills_data)

            order.status = OrderStatus.filled
            session.add(order)
            session.add(Fill(
                order_id=order.id, bot_id=bot_id,
                price=avg_price, quantity=total_qty, fee=total_fee,
            ))

            pos = session.get(Position, bot_id)
            if side == OrderSide.buy:
                pos.cash -= total_cost + total_fee
                new_qty = pos.base_qty + total_qty
                pos.avg_entry_price = (
                    avg_price if pos.base_qty == 0
                    else (pos.base_qty * (pos.avg_entry_price or 0) + total_cost) / new_qty
                )
                pos.base_qty = new_qty
            else:
                pos.cash += total_cost - total_fee
                pos.base_qty -= total_qty
                if pos.base_qty == 0:
                    pos.avg_entry_price = None
            session.add(pos)
        except httpx.HTTPError:
            order.status = OrderStatus.rejected
            session.add(order)
        return order
