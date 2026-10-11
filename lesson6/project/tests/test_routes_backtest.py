"""验证 /backtest GET 渲染表单、POST 跑回测并渲染结果。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_engine
from app.main import app
from app.models import OHLC


@pytest.fixture(autouse=True)
def _setup_db(tmp_path, ohlc_fixture):
    """切到 tmp 数据库 + 注入 OHLC + 用 dependency_overrides 让 routes 看到新 engine。"""
    db_path = tmp_path / "test.db"
    new_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(new_engine)
    with Session(new_engine) as s:
        for ts, row in ohlc_fixture.iterrows():
            s.add(OHLC(
                symbol="BTCUSDT", interval="1h",
                open_time=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                open=row["open"], high=row["high"], low=row["low"],
                close=row["close"], volume=row["volume"],
            ))
        s.commit()

    app.dependency_overrides[get_engine] = lambda: new_engine
    yield
    app.dependency_overrides.clear()


def test_get_backtest_form():
    with TestClient(app) as client:
        r = client.get("/backtest")
        assert r.status_code == 200
        assert "form" in r.text.lower()
        assert "dual_ma" in r.text


def test_post_backtest_runs_and_renders_summary():
    with TestClient(app) as client:
        r = client.post(
            "/backtest",
            data={
                "strategy_name": "dual_ma",
                "symbol": "BTCUSDT",
                "interval": "1h",
                "limit": "100",
                "params": '{"short_window": 7, "long_window": 14}',
            },
        )
        assert r.status_code == 200
        assert "夏普" in r.text or "Sharpe" in r.text


def test_post_backtest_with_range(monkeypatch, ohlc_fixture):
    """填了 start/end 走 range 模式；mock ensure_range_in_db 避免真网络。"""
    monkeypatch.setattr(
        "app.routes.backtest.ensure_range_in_db",
        lambda *a, **kw: 0,  # 假装数据已就绪
    )
    with TestClient(app) as client:
        r = client.post("/backtest", data={
            "strategy_name": "dual_ma",
            "symbol": "BTCUSDT",
            "interval": "1h",
            "limit": "100",  # 被 range 覆盖
            "params": "{}",
            "start_time": "2025-01-01T01:00",
            "end_time": "2025-01-01T03:00",
        })
        assert r.status_code == 200
        assert "夏普" in r.text or "Sharpe" in r.text


def test_post_backtest_range_too_large(monkeypatch):
    """估算 bar 数超过 200000 → 400 + 中文提示。"""
    with TestClient(app) as client:
        # 1m × 200 天 = 288000 bars，超过 200000
        r = client.post("/backtest", data={
            "strategy_name": "dual_ma",
            "symbol": "BTCUSDT",
            "interval": "1m",
            "limit": "100",
            "params": "{}",
            "start_time": "2024-01-01T00:00",
            "end_time": "2024-07-20T00:00",
        })
        assert r.status_code == 400
        assert "时间范围过大" in r.text


def test_post_backtest_start_after_end():
    with TestClient(app) as client:
        r = client.post("/backtest", data={
            "strategy_name": "dual_ma",
            "symbol": "BTCUSDT", "interval": "1h", "limit": "100", "params": "{}",
            "start_time": "2025-02-01T00:00",
            "end_time": "2025-01-01T00:00",
        })
        assert r.status_code == 400
        assert "起始时间不能晚于结束时间" in r.text
