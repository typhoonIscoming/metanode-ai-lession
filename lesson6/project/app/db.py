"""SQLModel engine + session 工厂。

engine 是模块级单例；测试时用 FastAPI dependency_overrides[get_engine]
覆盖即可（routes 都通过 Depends(get_engine) / Depends(get_session) 取依赖）。
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

engine: Engine = create_engine(
    settings.quant_db_url,
    connect_args={"check_same_thread": False} if settings.quant_db_url.startswith("sqlite") else {},
)


def get_engine() -> Engine:
    """FastAPI Depends 钩子；测试时 override 为另一个 engine。"""
    return engine


def init_db(eng: Engine | None = None) -> None:
    """创建所有 SQLModel 表（幂等）。在 main.lifespan 启动时调一次。"""
    from app import models  # noqa: F401  必须 import 以触发 SQLModel.metadata 注册

    SQLModel.metadata.create_all(eng or engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI Depends 用的 session 生成器。"""
    with Session(engine) as session:
        yield session
