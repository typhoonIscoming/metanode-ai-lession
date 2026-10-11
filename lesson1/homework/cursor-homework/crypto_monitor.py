"""
加密货币行情监控 CLI

功能:
    - price : 一次性查询指定币种的实时价格并落库
    - watch : 周期性轮询并落库, Ctrl+C 退出
    - alert : 周期性轮询, 价格突破阈值时打印告警
    - stats : 从本地 SQLite 查询某币种最近 N 条记录的最高/最低/均价

数据源: Binance 公共 API (无需 API key)
所有时间统一使用 UTC, 落库格式为 ISO 8601 字符串带 +00:00 后缀
"""

import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from typing import Optional

import click
import requests

# 支持的币种到 Binance 交易对的映射, 后续追加币种只需在此扩展
SYMBOL_MAP: dict[str, str] = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT",
    "BNB": "BNBUSDT",
}

# Binance 现货实时价格接口
BINANCE_PRICE_URL = "https://api.binance.com/api/v3/ticker/price"

# SQLite 数据库默认路径, 与脚本同目录
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prices.db")


# 返回当前 UTC 时间, 全脚本只通过此函数生成时间, 避免出现 naive datetime
def utc_now() -> datetime:
    """获取当前 UTC 时间, 带 timezone 信息"""
    return datetime.now(timezone.utc)


# 把 datetime 序列化成 ISO 8601 UTC 字符串, 落库与日志统一用此函数
def iso_utc(dt: datetime) -> str:
    """把 datetime 转成 ISO 8601 UTC 字符串, 形如 2026-04-19T08:30:00+00:00"""
    return dt.astimezone(timezone.utc).isoformat()


# 把用户传入的币种符号 (如 btc / Btc / BTC) 标准化成大写, 并校验是否支持
def normalize_symbol(symbol: str) -> str:
    """把用户输入的币种统一成大写, 不在 SYMBOL_MAP 中则抛 click 错误"""
    s = symbol.upper()
    if s not in SYMBOL_MAP:
        supported = ", ".join(sorted(SYMBOL_MAP.keys()))
        raise click.BadParameter(f"unsupported symbol: {symbol} (supported: {supported})")
    return s


# 打开或创建 SQLite 数据库连接, 同时确保表与索引存在
def open_db(db_path: str) -> sqlite3.Connection:
    """打开 SQLite 连接并初始化 prices 表与索引"""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prices (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT    NOT NULL,
            price  REAL    NOT NULL,
            ts     TEXT    NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_prices_symbol_ts ON prices(symbol, ts)"
    )
    conn.commit()
    return conn


# 调用 Binance ticker/price 接口拉取一个币种的实时价格
def fetch_price(symbol: str) -> float:
    """从 Binance 拉取指定币种的最新成交价 (USDT 计价)"""
    pair = SYMBOL_MAP[symbol]
    response = requests.get(
        BINANCE_PRICE_URL,
        params={"symbol": pair},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return float(data["price"])


# 拉取一组币种的最新价并写入数据库, 返回 (symbol, price, ts) 三元组列表
# price / watch / alert 三个子命令共用此函数, 保证落库逻辑只有一处
def fetch_and_record(
    conn: sqlite3.Connection, symbols: list[str]
) -> list[tuple[str, float, str]]:
    """批量拉价并写入 SQLite, 返回本轮成功的记录列表"""
    rows: list[tuple[str, float, str]] = []
    for symbol in symbols:
        try:
            price = fetch_price(symbol)
        except requests.RequestException as exc:
            # 单个币种失败不影响其它币种, 也不让循环命令直接退出
            click.echo(f"[WARN] fetch {symbol} failed: {exc}", err=True)
            continue

        ts = iso_utc(utc_now())
        conn.execute(
            "INSERT INTO prices(symbol, price, ts) VALUES (?, ?, ?)",
            (symbol, price, ts),
        )
        rows.append((symbol, price, ts))

    if rows:
        conn.commit()
    return rows


# 把一行价格记录格式化成对齐的字符串, watch / price / alert 共用
def format_row(symbol: str, price: float, ts: str) -> str:
    """把 (symbol, price, ts) 渲染成单行展示文本"""
    return f"{symbol:<5} {price:>14,.4f}  {ts}"


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------


# click 顶层命令组, 通过 --db 让所有子命令共享数据库路径
@click.group(help="Crypto price monitor CLI (Binance + SQLite, all timestamps in UTC).")
@click.option(
    "--db",
    "db_path",
    default=DEFAULT_DB_PATH,
    show_default=True,
    type=click.Path(dir_okay=False),
    help="SQLite database file path.",
)
@click.pass_context
def cli(ctx: click.Context, db_path: str) -> None:
    """顶层命令组, 把数据库路径放进 ctx.obj 供子命令使用"""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = db_path


# price 子命令: 一次性查询并落库, 适合脚本化轮询或手动 spot check
@cli.command(help="Fetch current price(s) once and store into SQLite.")
@click.argument("symbols", nargs=-1, required=True)
@click.pass_context
def price(ctx: click.Context, symbols: tuple[str, ...]) -> None:
    """price 子命令: 一次性查询指定币种当前价格"""
    normalized = [normalize_symbol(s) for s in symbols]
    conn = open_db(ctx.obj["db_path"])
    try:
        rows = fetch_and_record(conn, normalized)
    finally:
        conn.close()

    if not rows:
        click.echo("[ERROR] no price fetched", err=True)
        sys.exit(1)

    for symbol, p, ts in rows:
        click.echo(format_row(symbol, p, ts))


# watch 子命令: 周期性轮询, 持续打印并落库, Ctrl+C 退出
@cli.command(help="Continuously poll prices and store into SQLite.")
@click.argument("symbols", nargs=-1, required=True)
@click.option("--interval", "-i", type=float, default=10.0, show_default=True,
              help="Polling interval in seconds.")
@click.option("--duration", "-d", type=float, default=0.0, show_default=True,
              help="Total duration in seconds; 0 means run until Ctrl+C.")
@click.pass_context
def watch(
    ctx: click.Context,
    symbols: tuple[str, ...],
    interval: float,
    duration: float,
) -> None:
    """watch 子命令: 周期轮询币种最新价, 每轮落库 + 打印"""
    normalized = [normalize_symbol(s) for s in symbols]
    conn = open_db(ctx.obj["db_path"])

    start = utc_now()
    deadline_ts = start.timestamp() + duration if duration > 0 else None
    click.echo(
        f"[INFO] watching {','.join(normalized)} "
        f"every {interval}s (duration={'inf' if deadline_ts is None else f'{duration}s'})"
    )

    try:
        while True:
            rows = fetch_and_record(conn, normalized)
            for symbol, p, ts in rows:
                click.echo(format_row(symbol, p, ts))

            if deadline_ts is not None and utc_now().timestamp() >= deadline_ts:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        click.echo("\n[INFO] interrupted by user, exiting.")
    finally:
        conn.close()


# 校验 alert 子命令的 --above / --below 至少传一个, 且 above > below 时合理
def _validate_alert_thresholds(above: Optional[float], below: Optional[float]) -> None:
    """校验告警阈值参数, --above / --below 至少传一个"""
    if above is None and below is None:
        raise click.UsageError("at least one of --above / --below must be provided")
    if above is not None and below is not None and above <= below:
        raise click.UsageError("--above must be greater than --below")


# 根据当前价格与上一次状态, 判断是否需要触发告警, 返回新状态
# state 取值: "normal" | "above" | "below"
def _eval_alert_state(
    price: float,
    above: Optional[float],
    below: Optional[float],
    last_state: str,
) -> tuple[str, Optional[str]]:
    """根据阈值与上一次状态判断新状态, 仅在跨越边界时返回告警文本"""
    new_state = "normal"
    if above is not None and price > above:
        new_state = "above"
    elif below is not None and price < below:
        new_state = "below"

    if new_state == last_state:
        return new_state, None

    if new_state == "above":
        return new_state, f"price {price:,.4f} > above {above:,.4f}"
    if new_state == "below":
        return new_state, f"price {price:,.4f} < below {below:,.4f}"
    # 从异常态回到正常区间, 也提示一次, 便于观察价格回归
    return new_state, f"price {price:,.4f} back to normal range"


# alert 子命令: 周期轮询并在跨越阈值时打印告警
@cli.command(help="Poll a symbol and alert when price crosses thresholds.")
@click.argument("symbol")
@click.option("--above", type=float, default=None, help="Alert when price > ABOVE.")
@click.option("--below", type=float, default=None, help="Alert when price < BELOW.")
@click.option("--interval", "-i", type=float, default=30.0, show_default=True,
              help="Polling interval in seconds.")
@click.option("--duration", "-d", type=float, default=0.0, show_default=True,
              help="Total duration in seconds; 0 means run until Ctrl+C.")
@click.pass_context
def alert(
    ctx: click.Context,
    symbol: str,
    above: Optional[float],
    below: Optional[float],
    interval: float,
    duration: float,
) -> None:
    """alert 子命令: 周期监听单个币种, 越界时打印告警"""
    _validate_alert_thresholds(above, below)
    normalized = normalize_symbol(symbol)
    conn = open_db(ctx.obj["db_path"])

    start = utc_now()
    deadline_ts = start.timestamp() + duration if duration > 0 else None

    bounds_desc = []
    if above is not None:
        bounds_desc.append(f"above={above}")
    if below is not None:
        bounds_desc.append(f"below={below}")
    click.echo(
        f"[INFO] alert on {normalized} ({', '.join(bounds_desc)}) "
        f"every {interval}s"
    )

    # 用一个内存状态机记住上一次价格相对阈值的位置, 仅在穿越时打印告警
    last_state = "normal"
    try:
        while True:
            rows = fetch_and_record(conn, [normalized])
            for sym, p, ts in rows:
                click.echo(format_row(sym, p, ts))
                last_state, message = _eval_alert_state(p, above, below, last_state)
                if message:
                    click.echo(f"[ALERT] {ts} {sym} {message}")

            if deadline_ts is not None and utc_now().timestamp() >= deadline_ts:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        click.echo("\n[INFO] interrupted by user, exiting.")
    finally:
        conn.close()


# stats 子命令: 从本地 SQLite 查询某币种最近 N 条记录的统计值
@cli.command(help="Show max/min/avg of the last N records for a symbol.")
@click.argument("symbol")
@click.option("--last", "-n", "last_n", type=int, default=100, show_default=True,
              help="Number of most recent records to aggregate.")
@click.pass_context
def stats(ctx: click.Context, symbol: str, last_n: int) -> None:
    """stats 子命令: 查询某币种最近 N 条价格的最高/最低/均价"""
    if last_n <= 0:
        raise click.BadParameter("--last must be positive")

    normalized = normalize_symbol(symbol)
    conn = open_db(ctx.obj["db_path"])
    try:
        cursor = conn.execute(
            "SELECT price, ts FROM prices WHERE symbol = ? ORDER BY ts DESC LIMIT ?",
            (normalized, last_n),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        click.echo(f"[INFO] no records for {normalized}, run `price`/`watch` first.")
        return

    prices = [r[0] for r in rows]
    actual_n = len(prices)
    high = max(prices)
    low = min(prices)
    avg = sum(prices) / actual_n
    # rows 是按 ts DESC 取的, 所以末尾是最早的那条
    earliest_ts = rows[-1][1]
    latest_ts = rows[0][1]

    if actual_n < last_n:
        click.echo(f"[INFO] only {actual_n} record(s) available (requested {last_n})")

    click.echo(f"symbol : {normalized}")
    click.echo(f"count  : {actual_n}")
    click.echo(f"range  : {earliest_ts}  ->  {latest_ts}")
    click.echo(f"high   : {high:,.4f}")
    click.echo(f"low    : {low:,.4f}")
    click.echo(f"avg    : {avg:,.4f}")


if __name__ == "__main__":
    cli()
