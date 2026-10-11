"""验证基础 import / 配置加载正常。"""


def test_config_loads():
    from app.config import settings

    assert settings.quant_db_url.startswith("sqlite:")


def test_ohlc_fixture_shape(ohlc_fixture):
    assert ohlc_fixture.shape == (200, 5)
    assert list(ohlc_fixture.columns) == ["open", "high", "low", "close", "volume"]
    assert ohlc_fixture.index.tz is not None


def test_ohlc_fixture_validity(ohlc_fixture):
    df = ohlc_fixture
    assert (df["high"] >= df["open"]).all(), "high < open in some bars"
    assert (df["high"] >= df["close"]).all(), "high < close in some bars"
    assert (df["low"] <= df["open"]).all(), "low > open in some bars"
    assert (df["low"] <= df["close"]).all(), "low > close in some bars"
