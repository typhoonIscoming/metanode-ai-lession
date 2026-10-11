"""
加密货币行情监控 CLI - 拉取实时价格、阈值告警、落库持久化、历史统计

数据源: Binance 公开现货 Ticker API (无需 API Key)
数据库: SQLite，默认写入脚本同目录下 crypto_prices.db

子命令:
    watch SYMBOL [--interval SEC] [--above X] [--below Y] [--count N]
        持续轮询价格 → 打印 → 落库；传入 --above / --below 时突破阈值即告警
    alert SYMBOL (--above X | --below Y) [两者兼有亦可]
        一次性拉取当前价，检查是否突破阈值，结果打印到终端
    stats SYMBOL [-n N]
        读取 SQLite 中该币种最近 N 条价格记录，聚合最高 / 最低 / 均价 / 最新价

用法示例:
    python crypto_monitor.py watch BTC --interval 10 --above 80000
    python crypto_monitor.py alert ETH --below 2000
    python crypto_monitor.py stats BTC -n 50
"""

import argparse
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

# 支持的币种简称 → Binance 现货交易对
SUPPORTED_SYMBOLS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "BNB": "BNBUSDT",
    "SOL": "SOLUSDT",
    "XRP": "XRPUSDT",
}

BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/price"
DB_PATH = Path(__file__).parent / "crypto_prices.db"


def utc_now_iso() -> str:
    """返回带 Z 后缀的 UTC ISO-8601 时间字符串，遵守仓库统一的 UTC 约定"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_symbol(symbol: str) -> str:
    """把用户输入 (BTC / eth / BTCUSDT) 统一成 Binance 的完整交易对"""
    key = symbol.upper()
    # 预置表里命中就映射到 USDT 对；否则认为用户已经传了完整交易对
    return SUPPORTED_SYMBOLS.get(key, key)


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """建立连接并按需建表、建索引"""
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            queried_at TEXT NOT NULL
        )
        """
    )
    # 统计查询按 symbol + 时间倒序检索，加复合索引避免全表扫描
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_prices_symbol_time "
        "ON prices(symbol, queried_at DESC)"
    )
    conn.commit()
    return conn


def fetch_price(binance_symbol: str) -> float:
    """拉取指定交易对的最新现货价，失败时抛 requests 异常由调用方决定重试"""
    resp = requests.get(
        BINANCE_TICKER_URL,
        params={"symbol": binance_symbol},
        timeout=10,
    )
    resp.raise_for_status()
    return float(resp.json()["price"])


def record_price(
    conn: sqlite3.Connection, symbol: str, price: float, queried_at: str,
) -> None:
    """插入一条价格记录到 prices 表"""
    conn.execute(
        "INSERT INTO prices(symbol, price, queried_at) VALUES (?, ?, ?)",
        (symbol, price, queried_at),
    )
    conn.commit()


def check_alert(
    price: float, above: Optional[float], below: Optional[float],
) -> Optional[str]:
    """按上下阈值生成告警文本；价格在区间内返回 None"""
    if above is not None and price >= above:
        return f"[ALERT] 价格 {price:,.2f} 已突破上限 {above:,.2f}"
    if below is not None and price <= below:
        return f"[ALERT] 价格 {price:,.2f} 已跌破下限 {below:,.2f}"
    return None


def compute_stats(
    conn: sqlite3.Connection, binance_symbol: str, n: int,
) -> Optional[dict]:
    """读取最近 N 条记录，聚合最高 / 最低 / 均价 / 最新价 / 时间范围"""
    cur = conn.execute(
        """
        SELECT price, queried_at FROM prices
        WHERE symbol = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (binance_symbol, n),
    )
    rows = cur.fetchall()
    if not rows:
        return None
    prices = [r[0] for r in rows]
    return {
        "count": len(rows),
        "max": max(prices),
        "min": min(prices),
        "avg": sum(prices) / len(prices),
        "last": prices[0],                 # id DESC，第一条即最新
        "latest_at": rows[0][1],
        "earliest_at": rows[-1][1],
    }


# --------------------------------------------------------------------------- #
# 子命令处理函数
# --------------------------------------------------------------------------- #

def cmd_watch(args: argparse.Namespace) -> int:
    """持续轮询：拉价 → 落库 → 按需告警，支持 Ctrl+C 优雅退出"""
    binance_symbol = resolve_symbol(args.symbol)
    conn = init_db()
    iterations = 0
    last_price: Optional[float] = None  # 用于 --delta 波动比较
    try:
        while True:
            iterations += 1
            try:
                price = fetch_price(binance_symbol)
            except requests.RequestException as e:
                # 网络抖动时打印告警但不退出，等下个周期继续尝试
                print(
                    f"[WARN] 获取价格失败: {e}; {args.interval}s 后重试",
                    file=sys.stderr,
                )
                time.sleep(args.interval)
                continue

            ts = utc_now_iso()
            record_price(conn, binance_symbol, price, ts)

            # 相对上次采样的变化量，用于日志展示和 delta 告警判定
            diff = None if last_price is None else price - last_price
            diff_str = "" if diff is None else f"  (Δ {diff:+.2f})"
            print(f"[{ts}] {binance_symbol} = ${price:,.2f}{diff_str}")

            alert = check_alert(price, args.above, args.below)
            if alert:
                print(alert)

            if args.delta is not None and diff is not None and abs(diff) >= args.delta:
                direction = "上涨" if diff > 0 else "下跌"
                print(
                    f"[ALERT] 价格 {direction} {abs(diff):,.2f}，"
                    f"超过波动阈值 {args.delta:,.2f}"
                )

            last_price = price

            if args.count and iterations >= args.count:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n已手动终止轮询。")
    finally:
        conn.close()
    return 0


def cmd_alert(args: argparse.Namespace) -> int:
    """一次性检查当前价是否突破阈值；同时把当前价也落库"""
    if args.above is None and args.below is None:
        print("error: --above 或 --below 至少提供一个", file=sys.stderr)
        return 2

    binance_symbol = resolve_symbol(args.symbol)
    conn = init_db()
    try:
        price = fetch_price(binance_symbol)
        ts = utc_now_iso()
        record_price(conn, binance_symbol, price, ts)
        print(f"[{ts}] {binance_symbol} = ${price:,.2f}")

        alert = check_alert(price, args.above, args.below)
        print(alert if alert else "[OK] 价格在阈值区间内")
    finally:
        conn.close()
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """读取历史记录，输出最高 / 最低 / 均价等统计；没有数据时给出引导"""
    binance_symbol = resolve_symbol(args.symbol)
    conn = init_db()
    try:
        stats = compute_stats(conn, binance_symbol, args.count)
    finally:
        conn.close()

    if stats is None:
        print(f"未找到 {binance_symbol} 的任何记录；先跑 watch/alert 采集一些数据。")
        return 1

    print(f"{binance_symbol} 最近 {stats['count']} 条记录统计:")
    print(f"  最高价: ${stats['max']:,.2f}")
    print(f"  最低价: ${stats['min']:,.2f}")
    print(f"  均价  : ${stats['avg']:,.2f}")
    print(f"  最新价: ${stats['last']:,.2f}")
    print(f"  时间范围: {stats['earliest_at']} ~ {stats['latest_at']}")
    return 0


# --------------------------------------------------------------------------- #
# argparse
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    """构建带子命令的 argparse 解析器"""
    parser = argparse.ArgumentParser(
        description="加密货币行情监控 CLI (Binance + SQLite)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # watch
    p_watch = sub.add_parser("watch", help="持续轮询价格并落库，可选阈值告警")
    p_watch.add_argument("symbol", help="币种简称或完整交易对 (BTC / ETH / BTCUSDT ...)")
    p_watch.add_argument("--interval", type=int, default=10, help="轮询间隔 (秒)")
    p_watch.add_argument("--above", type=float, default=None, help="价格突破此值触发告警")
    p_watch.add_argument("--below", type=float, default=None, help="价格跌破此值触发告警")
    p_watch.add_argument(
        "--delta", type=float, default=None,
        help="相邻两次采样价差的绝对值 ≥ 此值时告警 (单位: USDT)",
    )
    p_watch.add_argument("--count", type=int, default=None, help="最多轮询次数 (缺省无限)")
    p_watch.set_defaults(func=cmd_watch)

    # alert
    p_alert = sub.add_parser("alert", help="一次性检查当前价是否突破阈值")
    p_alert.add_argument("symbol")
    p_alert.add_argument("--above", type=float, default=None)
    p_alert.add_argument("--below", type=float, default=None)
    p_alert.set_defaults(func=cmd_alert)

    # stats
    p_stats = sub.add_parser("stats", help="读取历史记录，输出最高/最低/均价统计")
    p_stats.add_argument("symbol")
    p_stats.add_argument(
        "-n", "--count", type=int, default=20, help="统计最近 N 条记录 (缺省 20)",
    )
    p_stats.set_defaults(func=cmd_stats)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
