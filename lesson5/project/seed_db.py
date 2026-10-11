"""
一次性脚本：从 Binance 公共 API 拉历史日 K 线，写入 ./prices.db 的 ohlc 表。

为什么要这一步：lesson1 作业落库的 prices 表只有点价，无法演示"过去 30 天最高/最低/均价"
这类典型 SQL 查询。本脚本补一个 ohlc 表，数据足够 lesson3-7 各种分析场景。

数据源：https://api.binance.com/api/v3/klines（公共，无需 API Key）
默认拉取：BTCUSDT、ETHUSDT 各 365 天的 1d K 线（足够 RSI 反转策略遇上真正的超卖事件）。
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

DB_PATH = Path(__file__).parent / "prices.db"
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
INTERVAL = "1d"
LIMIT = 365  # 最近 365 根日线（够 rsi_reversal 触发 oversold 反弹信号；详见 web 诊断）


def fetch_klines(symbol: str, interval: str, limit: int) -> list[tuple]:
    """从 Binance 拉 K 线。返回行列表：(symbol, open_time_iso, open, high, low, close, volume)"""
    resp = requests.get(
        "https://api.binance.com/api/v3/klines",
        params={"symbol": symbol, "interval": interval, "limit": limit},
        timeout=15,
    )
    resp.raise_for_status()
    rows = []
    for row in resp.json():
        # row[0] 是 open_time 的毫秒级 UTC 时间戳
        ts_ms = int(row[0])
        open_time = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        rows.append((
            symbol,
            open_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            float(row[1]),  # open
            float(row[2]),  # high
            float(row[3]),  # low
            float(row[4]),  # close
            float(row[5]),  # volume
        ))
    return rows


def init_schema(conn: sqlite3.Connection) -> None:
    """建表（幂等）"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ohlc (
            symbol TEXT NOT NULL,
            open_time TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL,
            PRIMARY KEY (symbol, open_time)
        )
        """
    )


def main() -> int:
    conn = sqlite3.connect(DB_PATH)
    init_schema(conn)
    total = 0
    for symbol in SYMBOLS:
        rows = fetch_klines(symbol, INTERVAL, LIMIT)
        # 用 INSERT OR REPLACE 避免重复跑时报主键冲突
        conn.executemany(
            "INSERT OR REPLACE INTO ohlc VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        total += len(rows)
        print(f"[seed] {symbol}: 写入 {len(rows)} 行", file=sys.stderr)
    conn.commit()
    conn.close()
    print(f"[seed] 完成，{total} 行落库到 {DB_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
