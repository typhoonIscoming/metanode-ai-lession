"""B-01/B-02 验收：骨架 + DB-backed settings 冒烟测试。

- 不依赖真实 Postgres：healthz 在 DB ping 失败时降级为 `degraded`；
- GET /settings 用 dependency_overrides 注入伪 session 返回固定默认行，
  避免单元测试也要起容器；真正 DB 集成验证由 Q-02 集成测试覆盖。
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_openapi_lists_v1_routes(client) -> None:
    """OpenAPI schema 应包含所有 /api/v1 路由前缀。"""
    resp = client.get("/openapi.json")
    assert resp.status_code == status.HTTP_200_OK
    paths = resp.json()["paths"].keys()
    expected_prefixes = [
        "/api/v1/healthz",
        "/api/v1/markets",
        "/api/v1/signals",
        "/api/v1/predict",
        "/api/v1/settings",
        "/api/v1/scheduler/jobs",
    ]
    for p in expected_prefixes:
        assert any(path.startswith(p) for path in paths), f"missing route {p}"


def test_healthz_shape(client) -> None:
    """无论 DB 是否连得通，healthz 路由都应返 200 + 正确 schema。"""
    resp = client.get("/api/v1/healthz")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["status"] in ("ok", "degraded")
    assert "db" in body
    assert body["version"].endswith("-skeleton")


def test_list_markets_returns_empty_container(client) -> None:
    resp = client.get("/api/v1/markets")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body == {"items": [], "total": 0, "page": 1, "page_size": 50}


def test_get_market_returns_404(client) -> None:
    resp = client.get("/api/v1/markets/1")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_list_signals_returns_empty_container(client) -> None:
    resp = client.get("/api/v1/signals")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_predict_post_returns_422(client) -> None:
    resp = client.post("/api/v1/predict", json={"polymarket_url": "https://polymarket.com/event/x"})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.fixture()
def client_with_fake_setting() -> TestClient:
    """覆盖 get_session 依赖，避免 GET /settings 真连 DB；返回固定默认 setting 行。"""
    from btc_arb.db import get_session
    from btc_arb.main import create_app

    fake_row = SimpleNamespace(
        id=1,
        entry_threshold=0.150,
        debounce_minutes=10,
        price_poll_minutes=5,
        predict_ttl_hours=24,
        discovery_keywords=["bitcoin", "btc"],
        discovery_max_days_to_resolve=30,
        feishu_webhook_url=None,
        openai_api_key=None,
        openai_model="gpt-5",
        web_search_provider="tavily",
        web_search_api_key=None,
        updated_at=datetime(2026, 5, 18, tzinfo=UTC),
    )

    class _FakeResult:
        def scalar_one_or_none(self):
            return fake_row

    class _FakeSession:
        async def execute(self, _stmt):
            return _FakeResult()

    async def _fake_session():
        yield _FakeSession()

    app = create_app()
    app.dependency_overrides[get_session] = _fake_session
    return TestClient(app)


def test_settings_get_returns_defaults(client_with_fake_setting: TestClient) -> None:
    resp = client_with_fake_setting.get("/api/v1/settings")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["entry_threshold"] == "0.150"
    assert body["price_poll_minutes"] == 5
    assert body["discovery_keywords"] == ["bitcoin", "btc"]
    assert body["openai_model"] == "gpt-5"
    assert body["web_search_provider"] == "tavily"
    assert body["openai_api_key"] is None  # mask 函数对 None 直通


def test_settings_patch_returns_422(client) -> None:
    resp = client.patch("/api/v1/settings", json={"entry_threshold": "0.2"})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_scheduler_jobs_returns_empty(client) -> None:
    resp = client.get("/api/v1/scheduler/jobs")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"items": []}


def test_scheduler_trigger_returns_422(client) -> None:
    resp = client.post("/api/v1/scheduler/trigger", json={"job": "price_poll"})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
