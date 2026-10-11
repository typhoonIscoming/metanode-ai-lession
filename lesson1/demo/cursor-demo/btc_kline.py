"""
Bitcoin K-Line Chart - Fetch BTC/USDT data from Binance and draw candlestick
chart with configurable time granularity. All timestamps are in UTC+0.

Data source: Binance public API (no API key required)
Chart library: mplfinance

Usage:
    python btc_kline.py                       # default: 1d interval, 30 days
    python btc_kline.py --interval 1h         # 1-hour candles
    python btc_kline.py -i 5m -d 1            # 5-minute candles, last 1 day
    python btc_kline.py --interval 15m --days 3
"""

import os
import sys
import argparse
import requests
import pandas as pd
import matplotlib
import mplfinance as mpf
from datetime import datetime, timedelta, timezone

if not os.environ.get("DISPLAY") and sys.platform != "win32":
    matplotlib.use("Agg")


# Supported Binance kline intervals and their seconds per candle.
# Used for pagination math and default lookback selection.
INTERVAL_SECONDS = {
    "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "2h": 7200, "4h": 14400, "6h": 21600, "8h": 28800, "12h": 43200,
    "1d": 86400, "3d": 259200, "1w": 604800,
}

# Sensible default lookback (in days) per interval, so a user running
# `python btc_kline.py -i 1m` doesn't accidentally fetch a month of 1-min data.
DEFAULT_DAYS = {
    "1m": 1, "3m": 2, "5m": 3, "15m": 7, "30m": 10,
    "1h": 14, "2h": 30, "4h": 60, "6h": 90, "8h": 90, "12h": 120,
    "1d": 30, "3d": 180, "1w": 365,
}

BINANCE_KLINE_URL = "https://api.binance.com/api/v3/klines"
BINANCE_MAX_LIMIT = 1000  # max candles per single Binance request


# Fetch BTC/USDT klines for a given interval and lookback, paginating
# through Binance's 1000-candle-per-request limit when necessary.
# All datetime objects are constructed as UTC+0 to match Binance's epoch.
def fetch_btc_klines(interval: str = "1d", days: int = 30) -> pd.DataFrame:
    """Fetch BTC/USDT kline data from Binance API with auto-pagination."""
    if interval not in INTERVAL_SECONDS:
        raise ValueError(f"Unsupported interval: {interval}")

    now_utc = datetime.now(timezone.utc)
    end_ms = int(now_utc.timestamp() * 1000)
    start_ms = int((now_utc - timedelta(days=days)).timestamp() * 1000)

    print(f"Fetching last {days} days of BTC/USDT {interval} kline data (UTC)...")

    records: list[dict] = []
    cursor = start_ms
    while cursor < end_ms:
        params = {
            "symbol": "BTCUSDT",
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
                "Date": datetime.fromtimestamp(item[0] / 1000, tz=timezone.utc),
                "Open": float(item[1]),
                "High": float(item[2]),
                "Low": float(item[3]),
                "Close": float(item[4]),
                "Volume": float(item[5]),
            })

        # Advance cursor past the last candle to fetch the next page.
        last_open_ms = batch[-1][0]
        next_cursor = last_open_ms + INTERVAL_SECONDS[interval] * 1000
        if next_cursor <= cursor:  # safety guard against infinite loops
            break
        cursor = next_cursor

        # Last page reached when Binance returns fewer than the limit.
        if len(batch) < BINANCE_MAX_LIMIT:
            break

    if not records:
        raise RuntimeError("No kline data returned from Binance")

    df = pd.DataFrame(records).drop_duplicates(subset="Date")
    df.set_index("Date", inplace=True)
    # mplfinance requires a tz-naive DatetimeIndex; values are already UTC.
    df.index = pd.DatetimeIndex(df.index).tz_convert("UTC").tz_localize(None)

    print(f"Got {len(df)} kline records")
    print(f"Range (UTC): {df.index[0]} ~ {df.index[-1]}")
    print(f"Price: ${df['Low'].min():,.2f} ~ ${df['High'].max():,.2f}")

    return df


# Plot candlestick chart with volume and moving averages.
# The interval is included in title and output filename so multiple
# granularities can coexist in the same directory.
def plot_kline(df: pd.DataFrame, interval: str = "1d") -> None:
    """Draw candlestick chart with volume and moving averages."""
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

    # Drop MA windows that are larger than the dataset to avoid mplfinance errors
    # (e.g. when fetching only a few intraday candles).
    candidate_mavs = (5, 10, 20)
    mavs = tuple(m for m in candidate_mavs if m < len(df))
    mav_arg = mavs if mavs else None

    title = f"\nBTC/USDT {interval} K-Line ({len(df)} candles, UTC)"

    fig, _axes = mpf.plot(
        df,
        type="candle",
        style=style,
        title=title,
        ylabel="Price (USDT)",
        ylabel_lower="Volume",
        volume=True,
        mav=mav_arg,
        figsize=(14, 8),
        tight_layout=True,
        returnfig=True,
    )

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, f"btc_kline_{interval}.png")
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nChart saved to: {output_path}")

    try:
        mpf.show()
    except Exception:
        print("(No GUI available, please open the PNG file directly)")


# Parse CLI arguments for interval and lookback window.
def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Plot BTC/USDT candlestick chart with configurable time granularity",
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
    return parser.parse_args()


def main():
    """Entry point: parse args, fetch data and plot chart."""
    args = parse_args()
    days = args.days if args.days is not None else DEFAULT_DAYS[args.interval]
    df = fetch_btc_klines(interval=args.interval, days=days)
    plot_kline(df, interval=args.interval)


if __name__ == "__main__":
    main()
