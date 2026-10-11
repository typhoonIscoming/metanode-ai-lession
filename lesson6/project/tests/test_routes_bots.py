"""验证 bot 管理路由：列表、创建、详情、启停、策略库。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    """切到 tmp 数据库 + 用 dependency_overrides[get_session] 让 routes 走它。"""
    db_path = tmp_path / "test.db"
    new_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(new_engine)

    def _override_session():
        with Session(new_engine) as s:
            yield s

    app.dependency_overrides[get_session] = _override_session
    yield new_engine
    app.dependency_overrides.clear()


def test_get_bots_empty():
    with TestClient(app) as client:
        r = client.get("/bots")
        assert r.status_code == 200
        assert "还没有机器人" in r.text


def test_create_bot_then_list_shows_it():
    with TestClient(app) as client:
        r = client.post("/bots", data={
            "name": "ma-btc-1h",
            "strategy_name": "dual_ma",
            "symbol": "BTCUSDT",
            "interval": "1h",
            "exchange": "paper",
            "initial_capital": "10000",
            "params": '{"short_window": 7, "long_window": 14}',
        }, follow_redirects=True)
        assert r.status_code == 200
        r2 = client.get("/bots")
        assert "ma-btc-1h" in r2.text


def test_bot_detail_page():
    with TestClient(app) as client:
        client.post("/bots", data={
            "name": "x", "strategy_name": "dual_ma", "symbol": "BTCUSDT",
            "interval": "1h", "exchange": "paper", "initial_capital": "10000", "params": "{}",
        }, follow_redirects=True)
        detail = client.get("/bots/1")
        assert detail.status_code == 200
        assert "x" in detail.text


def test_strategies_page_lists_four():
    with TestClient(app) as client:
        r = client.get("/strategies")
        assert r.status_code == 200
        for name in ["dual_ma", "rsi", "macd", "bollinger"]:
            assert name in r.text


def test_delete_bot_soft_deletes():
    with TestClient(app) as client:
        client.post("/bots", data={
            "name": "to-delete", "strategy_name": "dual_ma", "symbol": "BTCUSDT",
            "interval": "1h", "exchange": "paper", "initial_capital": "10000", "params": "{}",
        }, follow_redirects=True)
        r = client.delete("/bots/1")
        assert r.status_code == 200
        # After delete, /bots no longer shows the bot
        r2 = client.get("/bots")
        assert "to-delete" not in r2.text


def test_bot_detail_renders_equity_section_when_snapshots_exist(_setup_db):
    from sqlmodel import Session

    from app.models import PnLSnapshot
    new_engine = _setup_db
    with TestClient(app) as client:
        client.post("/bots", data={
            "name": "with-pnl", "strategy_name": "dual_ma", "symbol": "BTCUSDT",
            "interval": "1h", "exchange": "paper", "initial_capital": "10000", "params": "{}",
        }, follow_redirects=True)
        with Session(new_engine) as s:
            for i, equity in enumerate([10000.0, 10050.0, 10100.0]):
                s.add(PnLSnapshot(
                    bot_id=1, snapshot_at=f"2026-05-17T0{i}:00:00Z",
                    mark_price=100.0, equity=equity,
                    unrealized_pnl=0.0, realized_pnl=equity - 10000.0,
                ))
            s.commit()
        r = client.get("/bots/1")
        assert r.status_code == 200
        assert "资金曲线" in r.text
        assert "equity_1.png" in r.text


def test_bot_detail_no_equity_section_when_empty(_setup_db):
    with TestClient(app) as client:
        client.post("/bots", data={
            "name": "no-pnl", "strategy_name": "dual_ma", "symbol": "BTCUSDT",
            "interval": "1h", "exchange": "paper", "initial_capital": "10000", "params": "{}",
        }, follow_redirects=True)
        r = client.get("/bots/1")
        assert r.status_code == 200
        assert "资金曲线" not in r.text


def _create_bot(client):
    client.post("/bots", data={
        "name": "t", "strategy_name": "dual_ma", "symbol": "BTCUSDT",
        "interval": "1h", "exchange": "paper", "initial_capital": "10000", "params": "{}",
    }, follow_redirects=True)


def test_bot_start_form_redirects_to_detail():
    """普通 form 提交（无 HX-Request header）→ 303 跳回 detail。"""
    with TestClient(app) as client:
        _create_bot(client)
        r = client.post("/bots/1/start", follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/bots/1"


def test_bot_stop_form_redirects_to_detail():
    """普通 form 提交 stop → 303 跳回 detail。"""
    with TestClient(app) as client:
        _create_bot(client)
        client.post("/bots/1/start", headers={"HX-Request": "true"})  # 先启动
        r = client.post("/bots/1/stop", follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/bots/1"


def test_bot_delete_form_redirects_to_list():
    """普通 delete 提交 → 303 跳回 /bots 列表（不是 detail，因 bot 已 deleted）。"""
    with TestClient(app) as client:
        _create_bot(client)
        r = client.delete("/bots/1", follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/bots"


def test_bot_start_with_hx_request_returns_partial():
    """HTMX 调用仍返回 partial HTML（不是 redirect）。"""
    with TestClient(app) as client:
        _create_bot(client)
        r = client.post("/bots/1/start", headers={"HX-Request": "true"})
        assert r.status_code == 200
        # partial 是一组 .card / .metrics，没有 base.html 的 <header> 或 <title>
        assert "<header" not in r.text
        assert "<title>" not in r.text
