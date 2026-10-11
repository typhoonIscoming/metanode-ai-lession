"""pytest 顶层 conftest。

提供 TestClient fixture；DB 相关 fixture（testcontainers-postgres）由 B-02/Q-02 之后在
`tests/integration/conftest.py` 中分层加入。
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# 让 settings 在 import main 之前拿到一个不会触发真实连接的 DB URL
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://btc_arb:btc_arb@localhost:5432/btc_arb_test",
)
os.environ.setdefault("LOG_LEVEL", "warning")


@pytest.fixture()
def client() -> TestClient:
    """同步 TestClient；async 路由由 FastAPI/Starlette 自动桥接。"""
    from btc_arb.main import create_app

    return TestClient(create_app())
