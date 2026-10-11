"""SQLModel 实体定义。所有时间字段都是 UTC ISO 字符串。"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import JSON, Column, Field, SQLModel


def utcnow_iso() -> str:
    """生成 UTC ISO 8601 时间戳，例如 '2026-05-17T08:00:00Z'。"""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class Exchange(StrEnum):
    paper = "paper"
    binance_testnet = "binance_testnet"


class BotStatus(StrEnum):
    stopped = "stopped"
    running = "running"
    errored = "errored"
    deleted = "deleted"


class OrderSide(StrEnum):
    buy = "buy"
    sell = "sell"


class OrderType(StrEnum):
    market = "market"


class OrderStatus(StrEnum):
    pending = "pending"
    filled = "filled"
    rejected = "rejected"


class TickStatus(StrEnum):
    success = "success"
    skipped = "skipped"
    errored = "errored"


class OHLC(SQLModel, table=True):
    __tablename__ = "ohlc"

    symbol: str = Field(primary_key=True)
    interval: str = Field(primary_key=True)
    open_time: str = Field(primary_key=True)  # UTC ISO
    open: float
    high: float
    low: float
    close: float
    volume: float


class Bot(SQLModel, table=True):
    __tablename__ = "bots"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    strategy_name: str
    strategy_params: dict = Field(default_factory=dict, sa_column=Column(JSON))
    symbol: str
    interval: str
    exchange: Exchange = Field(default=Exchange.paper)
    status: BotStatus = Field(default=BotStatus.stopped)
    initial_capital: float = Field(default=10000.0)
    created_at: str = Field(default_factory=utcnow_iso)
    updated_at: str = Field(default_factory=utcnow_iso)


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: int | None = Field(default=None, primary_key=True)
    bot_id: int = Field(index=True)
    side: OrderSide
    type: OrderType = Field(default=OrderType.market)
    quantity: float
    status: OrderStatus = Field(default=OrderStatus.pending)
    requested_at: str = Field(default_factory=utcnow_iso)


class Fill(SQLModel, table=True):
    __tablename__ = "fills"

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(index=True)
    bot_id: int = Field(index=True)
    price: float
    quantity: float
    fee: float = Field(default=0.0)
    filled_at: str = Field(default_factory=utcnow_iso)


class Position(SQLModel, table=True):
    __tablename__ = "positions"

    bot_id: int = Field(primary_key=True)
    cash: float
    base_qty: float = Field(default=0.0)
    avg_entry_price: float | None = Field(default=None)
    updated_at: str = Field(default_factory=utcnow_iso)


class PnLSnapshot(SQLModel, table=True):
    __tablename__ = "pnl_snapshots"

    id: int | None = Field(default=None, primary_key=True)
    bot_id: int = Field(index=True)
    snapshot_at: str = Field(default_factory=utcnow_iso, index=True)
    mark_price: float
    equity: float
    unrealized_pnl: float
    realized_pnl: float


class TickLog(SQLModel, table=True):
    __tablename__ = "tick_log"

    id: int | None = Field(default=None, primary_key=True)
    bot_id: int = Field(index=True)
    tick_at: str = Field(default_factory=utcnow_iso, index=True)
    status: TickStatus
    message: str = Field(default="", max_length=500)
