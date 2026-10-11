"""
加密货币K线图 - 获取 Binance 行情数据并绘制K线图，支持 BTC/ETH 切换与对比

数据源: Binance 公开API (无需API Key)
图表库: mplfinance (专业金融K线图)

用法:
    python btc_kline.py                       # 默认 BTC、1d、30 天
    python btc_kline.py -s ETH                # ETH 1d K线
    python btc_kline.py -s ETH -i 1h          # ETH 1 小时 K线
    python btc_kline.py --compare             # BTC vs ETH 收盘价归一化对比
    python btc_kline.py --compare -i 4h -d 30
"""

import os
import sys
import argparse
import requests
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime, timedelta

# 无图形界面时使用 Agg 后端，仅保存图片不弹窗
if not os.environ.get("DISPLAY") and sys.platform != "win32":
    matplotlib.use("Agg")


# Binance 支持的 K 线粒度及对应秒数，用于分页计算
INTERVAL_SECONDS = {
    "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "2h": 7200, "4h": 14400, "6h": 21600, "8h": 28800, "12h": 43200,
    "1d": 86400, "3d": 259200, "1w": 604800,
}

# 各粒度的默认回溯天数，避免 `-i 1m` 一次拉出数万根 K 线
DEFAULT_DAYS = {
    "1m": 1, "3m": 2, "5m": 3, "15m": 7, "30m": 10,
    "1h": 14, "2h": 30, "4h": 60, "6h": 90, "8h": 90, "12h": 120,
    "1d": 30, "3d": 180, "1w": 365,
}

# 支持的币种 → Binance 交易对映射；扩展新币种只需在此追加
SUPPORTED_SYMBOLS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
}

# 对比图中各币种的品牌色，缺省回退由 matplotlib 自动选色
SYMBOL_COLORS = {
    "BTC": "#f7931a",
    "ETH": "#627eea",
}

BINANCE_KLINE_URL = "https://api.binance.com/api/v3/klines"
BINANCE_MAX_LIMIT = 1000  # Binance 单次请求返回的最大 K 线数


def fetch_klines(symbol: str = "BTC", interval: str = "1d", days: int = 30) -> pd.DataFrame:
    """从 Binance API 获取指定币种的 K线数据，自动分页"""
    if interval not in INTERVAL_SECONDS:
        raise ValueError(f"Unsupported interval: {interval}")
    if symbol not in SUPPORTED_SYMBOLS:
        raise ValueError(
            f"Unsupported symbol: {symbol}; choose from {list(SUPPORTED_SYMBOLS)}"
        )

    binance_symbol = SUPPORTED_SYMBOLS[symbol]
    end_ms = int(datetime.now().timestamp() * 1000)
    start_ms = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

    print(f"正在获取最近 {days} 天的 {binance_symbol} {interval} K线数据...")

    records: list[dict] = []
    cursor = start_ms
    while cursor < end_ms:
        params = {
            "symbol": binance_symbol,
            "interval": interval,
            "startTime": cursor,
            "endTime": end_ms,
            "limit": BINANCE_MAX_LIMIT,
        }
        response = requests.get(BINANCE_KLINE_URL, params=params, timeout=15)
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break

        for item in batch:
            records.append({
                "Date": datetime.fromtimestamp(item[0] / 1000),
                "Open": float(item[1]),
                "High": float(item[2]),
                "Low": float(item[3]),
                "Close": float(item[4]),
                "Volume": float(item[5]),
            })

        # 游标推进到上一根 K 线之后，准备拉下一页
        last_open_ms = batch[-1][0]
        next_cursor = last_open_ms + INTERVAL_SECONDS[interval] * 1000
        if next_cursor <= cursor:  # 兜底：防止异常返回导致死循环
            break
        cursor = next_cursor

        # 返回数量小于 limit 说明已是最后一页
        if len(batch) < BINANCE_MAX_LIMIT:
            break

    if not records:
        raise RuntimeError(f"No kline data returned from Binance for {binance_symbol}")

    df = pd.DataFrame(records).drop_duplicates(subset="Date")
    df.set_index("Date", inplace=True)
    df.index = pd.DatetimeIndex(df.index)

    print(f"成功获取 {len(df)} 条 {binance_symbol} K线数据")
    print(f"时间范围: {df.index[0]} ~ {df.index[-1]}")
    print(f"价格范围: ${df['Low'].min():,.2f} ~ ${df['High'].max():,.2f}")

    return df


def plot_kline(df: pd.DataFrame, symbol: str = "BTC", interval: str = "1d") -> None:
    """绘制单币种 K 线图，含成交量与均线；输出文件名带粒度，便于多粒度共存"""
    # 红涨绿跌（中国习惯，与欧美默认相反）
    mc = mpf.make_marketcolors(
        up="red",
        down="green",
        edge="inherit",
        wick="inherit",
        volume="in",
    )
    style = mpf.make_mpf_style(
        marketcolors=mc,
        gridstyle="--",
        gridcolor="#e0e0e0",
        facecolor="white",
    )

    # 丢掉窗口大于数据量的均线；mplfinance 不接受 mav=None，只能完全省略该 kwarg
    candidate_mavs = (5, 10, 20)
    mavs = tuple(m for m in candidate_mavs if m < len(df))

    pair = SUPPORTED_SYMBOLS[symbol]
    title = f"\n{pair} {interval} K-Line ({len(df)} candles)"

    plot_kwargs = dict(
        type="candle",
        style=style,
        title=title,
        ylabel="Price (USDT)",
        ylabel_lower="Volume",
        volume=True,
        figsize=(14, 8),
        tight_layout=True,
        returnfig=True,
    )
    if mavs:
        plot_kwargs["mav"] = mavs

    fig, _axes = mpf.plot(df, **plot_kwargs)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, f"{symbol.lower()}_kline_{interval}.png")
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nK线图已保存到: {output_path}")

    try:
        mpf.show()
    except Exception:
        print("(无图形界面环境，请直接打开 PNG 文件查看)")


def plot_compare(dfs: dict[str, pd.DataFrame], interval: str = "1d") -> None:
    """对比模式：将多个币种的收盘价归一化到 100，画在同一张图上看相对走势"""
    fig, ax = plt.subplots(figsize=(14, 7))

    for symbol, df in dfs.items():
        if df.empty:
            continue
        # 归一化到起点 100，方便不同价格量级的币种放在同一坐标系
        normalized = df["Close"] / df["Close"].iloc[0] * 100
        change_pct = normalized.iloc[-1] - 100
        ax.plot(
            df.index,
            normalized,
            label=(
                f"{SUPPORTED_SYMBOLS[symbol]}  "
                f"(${df['Close'].iloc[-1]:,.2f}, {change_pct:+.2f}%)"
            ),
            color=SYMBOL_COLORS.get(symbol),
            linewidth=1.6,
        )

    ax.axhline(100, color="#999", linewidth=0.8, linestyle="--")
    symbols_label = " vs ".join(dfs.keys())
    # 使用英文标题，避免无 CJK 字体环境下的方框乱码
    ax.set_title(f"{symbols_label} - {interval} Close Price (normalized to 100)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Normalized Price (start = 100)")
    ax.grid(True, linestyle="--", color="#e0e0e0")
    ax.legend(loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    suffix = "_".join(s.lower() for s in dfs.keys())
    output_path = os.path.join(script_dir, f"compare_{suffix}_{interval}.png")
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\n对比图已保存到: {output_path}")


def parse_args() -> argparse.Namespace:
    """解析命令行参数：币种 -s、粒度 -i、回溯天数 -d、对比模式 --compare"""
    parser = argparse.ArgumentParser(
        description="Plot BTC/ETH candlestick chart or normalized comparison",
    )
    parser.add_argument(
        "-s", "--symbol",
        choices=list(SUPPORTED_SYMBOLS.keys()),
        default="BTC",
        help="Crypto symbol (default: BTC). Ignored when --compare is set.",
    )
    parser.add_argument(
        "-i", "--interval",
        choices=list(INTERVAL_SECONDS.keys()),
        default="1d",
        help="Candle interval (default: 1d)",
    )
    parser.add_argument(
        "-d", "--days",
        type=int,
        default=None,
        help="Lookback window in days (default depends on interval)",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Plot BTC vs ETH normalized comparison instead of a single-symbol candle chart",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    days = args.days if args.days is not None else DEFAULT_DAYS[args.interval]

    if args.compare:
        dfs = {
            sym: fetch_klines(symbol=sym, interval=args.interval, days=days)
            for sym in ("BTC", "ETH")
        }
        plot_compare(dfs, interval=args.interval)
    else:
        df = fetch_klines(symbol=args.symbol, interval=args.interval, days=days)
        plot_kline(df, symbol=args.symbol, interval=args.interval)


if __name__ == "__main__":
    main()
