"""FastAPI 应用入口。

Phase 0：装好 CORS、日志、6 个 router stub、healthz、lifespan 释放 DB engine。
B-04：补全局异常处理器、请求上下文中间件。
B-18：lifespan 内启动 APScheduler。
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from btc_arb import __version__
from btc_arb.config import get_settings
from btc_arb.db import dispose_engine
from btc_arb.logging import configure_logging, get_logger
from btc_arb.routers import api_router
from btc_arb.scheduler import start_scheduler, stop_scheduler
from btc_arb.services.bootstrap import bootstrap_settings_from_env


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动初始化日志 + 从 ENV bootstrap setting + 启动 APScheduler。"""
    settings = get_settings()
    configure_logging(level=settings.log_level)
    logger = get_logger(__name__)
    logger.info("app.startup", version=__version__, env_host=settings.app_host, env_port=settings.app_port)
    # 从 .env BOOTSTRAP_* 自动填 setting 表空字段（已配置的不覆盖）
    try:
        await bootstrap_settings_from_env()
    except Exception as e:  # noqa: BLE001
        logger.warning("bootstrap.failed", error=str(e))
    # 启动后台调度（discover / predict / price-poll / signal+notify）
    start_scheduler()
    try:
        yield
    finally:
        logger.info("app.shutdown")
        await stop_scheduler()
        await dispose_engine()


def create_app() -> FastAPI:
    """工厂模式构造 FastAPI 实例，方便测试覆盖 settings。"""
    settings = get_settings()
    app = FastAPI(
        title="btc-arb backend",
        version=__version__,
        description="Polymarket BTC 套利信号工具后端。",
        lifespan=lifespan,
    )

    # CORS：env 里的固定列表 + 本地 dev regex（30xx 端口都放行，避免 Next.js
    # 端口漂移导致跨域；regex 仅匹配 localhost / 127.0.0.1，不会泄露到外网）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):3[0-9]{3}",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
