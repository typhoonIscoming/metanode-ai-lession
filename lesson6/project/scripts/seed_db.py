"""一次性脚本：从 Binance public REST 拉 K 线，写入 quant.db 的 ohlc 表。

默认拉：BTCUSDT + ETHUSDT，interval ∈ {1h, 1d}。可改 SYMBOLS / INTERVALS / LIMIT。
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

import httpx
from sqlmodel import Session, SQLModel

from app.db import engine
from app.models import OHLC

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
INTERVALS = ["1h", "1d"]
LIMIT = 200


def fetch(symbol: str, interval: str, limit: int) -> list[dict]:
    resp = httpx.get(
        "https://api.binance.com/api/v3/klines",
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


def main() -> int:
    SQLModel.metadata.create_all(engine)
    total = 0
    with Session(engine) as s:
        for symbol in SYMBOLS:
            for interval in INTERVALS:
                rows = fetch(symbol, interval, LIMIT)
                for row in rows:
                    existing = s.get(OHLC, (symbol, interval, row["open_time"]))
                    if existing is None:
                        s.add(OHLC(symbol=symbol, interval=interval, **row))
                    else:
                        for k, v in row.items():
                            if k != "open_time":
                                setattr(existing, k, v)
                        s.add(existing)
                s.commit()
                print(f"[seed] {symbol} {interval}: {len(rows)} rows", file=sys.stderr)
                total += len(rows)
    print(f"[seed] done, total {total} rows", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
