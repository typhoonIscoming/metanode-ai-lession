"""
btc_kline.py 单元测试

覆盖范围:
- fetch_klines: 入参校验 / 单页 / 多页分页 / 空响应 / 去重
- plot_kline:   PNG 落盘 / 数据稀少时均线降级
- plot_compare: PNG 落盘 / 跳过空 DataFrame
- parse_args:   默认值 / 复合参数 / 非法粒度

网络已通过 unittest.mock 全程拦截，离线即可运行：
    pytest test_btc_kline.py -v
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import matplotlib
# 强制无窗口后端，避免本地有 DISPLAY 时测试弹窗
matplotlib.use("Agg")

import pandas as pd
import pytest

# 让测试文件可直接 import 同目录下的脚本
sys.path.insert(0, str(Path(__file__).parent))

import btc_kline  # noqa: E402


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

ONE_DAY_MS = 86_400_000


def _kline_row(open_ms: int, base: float = 100.0) -> list:
    """构造一条 Binance 风格的 K 线原始数据，字段顺序与 /klines 接口一致"""
    return [
        open_ms,
        f"{base:.2f}",          # open
        f"{base + 5:.2f}",      # high
        f"{base - 5:.2f}",      # low
        f"{base + 1:.2f}",      # close
        f"{1000 + base:.2f}",   # volume
        open_ms + ONE_DAY_MS - 1,
        "0", 0, "0", "0", "0",
    ]


def _mock_response(payload):
    resp = MagicMock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


def _make_df(n_rows: int) -> pd.DataFrame:
    """生成测试用 OHLCV DataFrame"""
    idx = pd.date_range("2026-01-01", periods=n_rows, freq="D")
    return pd.DataFrame(
        {
            "Open":   [100 + i for i in range(n_rows)],
            "High":   [105 + i for i in range(n_rows)],
            "Low":    [95 + i for i in range(n_rows)],
            "Close":  [101 + i for i in range(n_rows)],
            "Volume": [1000 + i for i in range(n_rows)],
        },
        index=idx,
    )


# --------------------------------------------------------------------------- #
# fetch_klines
# --------------------------------------------------------------------------- #

def test_fetch_klines_rejects_bad_interval():
    with pytest.raises(ValueError, match="Unsupported interval"):
        btc_kline.fetch_klines(symbol="BTC", interval="2d", days=1)


def test_fetch_klines_rejects_bad_symbol():
    with pytest.raises(ValueError, match="Unsupported symbol"):
        btc_kline.fetch_klines(symbol="DOGE", interval="1d", days=1)


def test_fetch_klines_raises_when_api_returns_empty():
    with patch("btc_kline.requests.get", return_value=_mock_response([])):
        with pytest.raises(RuntimeError, match="No kline data"):
            btc_kline.fetch_klines(symbol="ETH", interval="1d", days=3)


def test_fetch_klines_single_page_returns_dataframe():
    rows = [_kline_row(i * ONE_DAY_MS, base=100 + i) for i in range(5)]

    with patch("btc_kline.requests.get", return_value=_mock_response(rows)) as mock_get:
        df = btc_kline.fetch_klines(symbol="BTC", interval="1d", days=5)

    # 短于 limit 的批次应当只发一次请求
    assert mock_get.call_count == 1
    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert len(df) == 5
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df["Open"].iloc[0] == pytest.approx(100.00)
    assert df["Close"].iloc[-1] == pytest.approx(105.00)


def test_fetch_klines_paginates_until_short_batch():
    """连续两批：第一批满 BINANCE_MAX_LIMIT 触发翻页；第二批短批次结束循环

    时间戳必须接近 now，否则 fetch_klines 内部基于 now 推算的 start_ms 会大于
    我们伪造的 last_open_ms，触发 `next_cursor <= cursor` 兜底退出。
    """
    days = 1500
    base_ms = int(datetime.now().timestamp() * 1000) - days * ONE_DAY_MS
    full_page = [
        _kline_row(base_ms + i * ONE_DAY_MS, base=i)
        for i in range(btc_kline.BINANCE_MAX_LIMIT)
    ]
    short_page = [
        _kline_row(
            base_ms + (btc_kline.BINANCE_MAX_LIMIT + i) * ONE_DAY_MS,
            base=2000 + i,
        )
        for i in range(3)
    ]

    with patch(
        "btc_kline.requests.get",
        side_effect=[_mock_response(full_page), _mock_response(short_page)],
    ) as mock_get:
        df = btc_kline.fetch_klines(symbol="BTC", interval="1d", days=days)

    assert mock_get.call_count == 2
    assert len(df) == btc_kline.BINANCE_MAX_LIMIT + 3


def test_fetch_klines_drops_duplicate_timestamps():
    rows = [
        _kline_row(0, base=100),
        _kline_row(0, base=100),         # 故意制造重复时间戳
        _kline_row(ONE_DAY_MS, base=101),
    ]
    with patch("btc_kline.requests.get", return_value=_mock_response(rows)):
        df = btc_kline.fetch_klines(symbol="ETH", interval="1d", days=2)
    assert len(df) == 2


# --------------------------------------------------------------------------- #
# plot_kline / plot_compare
# --------------------------------------------------------------------------- #

def _redirect_script_dir(monkeypatch, tmp_path):
    """把 plot_* 函数里 os.path.dirname(__file__) 重定向到 tmp_path"""
    monkeypatch.setattr(btc_kline, "__file__", str(tmp_path / "btc_kline.py"))


def test_plot_kline_writes_png(tmp_path, monkeypatch):
    _redirect_script_dir(monkeypatch, tmp_path)
    btc_kline.plot_kline(_make_df(30), symbol="BTC", interval="1d")
    out = tmp_path / "btc_kline_1d.png"
    assert out.exists() and out.stat().st_size > 0


def test_plot_kline_handles_short_history(tmp_path, monkeypatch):
    """数据少于最小均线窗口 (5) 时应平滑降级为 mav=None，不能抛错"""
    _redirect_script_dir(monkeypatch, tmp_path)
    btc_kline.plot_kline(_make_df(3), symbol="ETH", interval="1d")
    assert (tmp_path / "eth_kline_1d.png").exists()


def test_plot_compare_writes_png(tmp_path, monkeypatch):
    _redirect_script_dir(monkeypatch, tmp_path)
    btc_kline.plot_compare(
        {"BTC": _make_df(20), "ETH": _make_df(20)},
        interval="1d",
    )
    assert (tmp_path / "compare_btc_eth_1d.png").exists()


def test_plot_compare_skips_empty_dataframe(tmp_path, monkeypatch):
    """有币种 DataFrame 为空时不应抛错，仍能输出包含其它币种的图"""
    _redirect_script_dir(monkeypatch, tmp_path)
    empty_df = pd.DataFrame(
        columns=["Open", "High", "Low", "Close", "Volume"],
        index=pd.DatetimeIndex([]),
    )
    btc_kline.plot_compare(
        {"BTC": _make_df(20), "ETH": empty_df},
        interval="1d",
    )
    assert (tmp_path / "compare_btc_eth_1d.png").exists()


# --------------------------------------------------------------------------- #
# parse_args
# --------------------------------------------------------------------------- #

def test_parse_args_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["btc_kline.py"])
    args = btc_kline.parse_args()
    assert args.symbol == "BTC"
    assert args.interval == "1d"
    assert args.days is None
    assert args.compare is False


def test_parse_args_compare_eth_15m(monkeypatch):
    monkeypatch.setattr(
        sys, "argv",
        ["btc_kline.py", "-s", "ETH", "-i", "15m", "--compare", "-d", "5"],
    )
    args = btc_kline.parse_args()
    assert args.symbol == "ETH"
    assert args.interval == "15m"
    assert args.days == 5
    assert args.compare is True


def test_parse_args_invalid_interval_exits(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["btc_kline.py", "-i", "2d"])
    with pytest.raises(SystemExit):
        btc_kline.parse_args()
