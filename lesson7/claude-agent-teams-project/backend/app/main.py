"""FastAPI 应用入口。

提供：
- CORS 中间件（允许 http://localhost:3000）
- 健康检查接口 GET /api/health
- REST 接口 GET /api/tokens：返回最新快照
- SSE 接口 GET /api/stream：实时推送 snapshot 事件

在 lifespan 中启动/停止调度器（SnapshotHub）。
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from .models import SnapshotResponse
from .scheduler import hub

# 设置基础日志级别为 INFO，方便 docker / uvicorn 日志查看抓取轨迹
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """FastAPI 生命周期：启动时拉起调度器，关闭时停掉。"""
    logger.info("应用启动，初始化 SnapshotHub")
    await hub.start()
    try:
        yield
    finally:
        logger.info("应用关闭，停止 SnapshotHub")
        await hub.stop()


app = FastAPI(
    title="Crypto Heatmap API",
    description="加密货币市值热力图后端：抓取 Binance 24h 行情并通过 SSE 推送",
    version="0.1.0",
    lifespan=lifespan,
)

# 前端开发环境跑在 http://localhost:3000，需要放行跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    """健康检查接口，供 Docker / 部署平台探活使用。"""
    return {"status": "ok"}


@app.get("/api/tokens", response_model=SnapshotResponse)
async def get_tokens() -> SnapshotResponse:
    """返回最新一次抓取的快照。

    首次抓取尚未完成时返回 503，让前端稍后重试。
    """
    snapshot = hub.latest
    if snapshot is None:
        raise HTTPException(
            status_code=503,
            detail="首次抓取尚未完成，请稍后重试",
        )
    return snapshot


@app.get("/api/stream")
async def stream_tokens(request: Request) -> EventSourceResponse:
    """SSE 接口：持续推送 snapshot 事件。

    - event 名固定为 `snapshot`
    - data 为 `SnapshotResponse` 序列化后的 JSON 字符串
    - 客户端断开时自动注销订阅
    """

    async def event_gen() -> AsyncIterator[dict[str, str]]:
        """异步生成器：把 hub.subscribe() 转成 sse-starlette 期望的 dict 事件。"""
        async for snapshot in hub.subscribe():
            # 客户端断开时主动退出
            if await request.is_disconnected():
                logger.info("SSE 客户端已断开，退出生成器")
                break
            yield {
                "event": "snapshot",
                "data": json.dumps(snapshot.model_dump(), ensure_ascii=False),
            }

    return EventSourceResponse(event_gen())
