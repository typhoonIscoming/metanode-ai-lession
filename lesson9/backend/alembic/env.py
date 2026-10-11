"""Alembic 环境入口。

数据库 URL 从应用 settings 注入（asyncpg 异步连接串），所有迁移走 async engine。
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import btc_arb.models  # noqa: F401  触发所有 ORM 模型注册，让 Base.metadata 收集完整 schema
from alembic import context
from btc_arb.config import get_settings
from btc_arb.db import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 注入运行时数据库 URL（避免在 alembic.ini 里硬编码密码）
config.set_main_option("sqlalchemy.url", get_settings().database_url)

# autogenerate 与 schema 比对的真相源
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：直接渲染 SQL，不连库。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在线模式：通过 async engine 走真连接。"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
