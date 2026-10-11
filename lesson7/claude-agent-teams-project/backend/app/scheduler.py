"""定时调度器与 SSE 广播中心。

职责：
1. 用 APScheduler 的 AsyncIOScheduler 每 30s 调用 `BinanceFetcher.fetch()`
2. 启动时立即跑一次（避免前端要等 30s 才看到第一条数据）
3. 抓取结果同时：
   - 写入内部最新缓存 `_latest_snapshot`，供 REST `/api/tokens` 读取
   - 广播给所有 SSE 订阅者（每个连接一个 `asyncio.Queue`）
4. 抓取异常时打日志、不崩溃，下次继续

线程模型说明：
- AsyncIOScheduler 在当前 event loop 上跑协程任务，跟 FastAPI 同 loop，无需跨线程通信
- 广播采用 per-subscriber `asyncio.Queue`，订阅时注册、断开时注销，避免慢消费者拖累抓取
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .binance_fetcher import BinanceFetcher
from .models import SnapshotResponse

logger = logging.getLogger(__name__)

# 抓取间隔（秒），契约规定 30s
FETCH_INTERVAL_SECONDS = 30

# 每个 SSE 订阅者的 Queue 容量。若前端消费慢，老数据会被丢弃只保留最新一条
SUBSCRIBER_QUEUE_MAXSIZE = 1


class SnapshotHub:
    """快照中心：持有最新缓存 + 管理 SSE 订阅者队列。"""

    def __init__(self) -> None:
        self._fetcher = BinanceFetcher()
        self._scheduler: AsyncIOScheduler | None = None
        # 最新一次抓取成功的快照；首次抓取完成前为 None
        self._latest_snapshot: SnapshotResponse | None = None
        # 所有活跃 SSE 订阅者的队列集合
        self._subscribers: set[asyncio.Queue[SnapshotResponse]] = set()
        # 保护 _subscribers 增删
        self._lock = asyncio.Lock()

    # ---------- 对外属性 ----------

    @property
    def latest(self) -> SnapshotResponse | None:
        """获取最新缓存快照，可能为 None（首次抓取尚未完成）。"""
        return self._latest_snapshot

    # ---------- 生命周期 ----------

    async def start(self) -> None:
        """启动调度器；立即触发一次首抓，再按 30s 周期运行。"""
        if self._scheduler is not None:
            logger.warning("SnapshotHub 已启动，忽略重复 start")
            return

        self._scheduler = AsyncIOScheduler()
        # 注意：APScheduler 的 add_job 会把 coroutine function 包装为 task
        self._scheduler.add_job(
            self._tick,
            trigger="interval",
            seconds=FETCH_INTERVAL_SECONDS,
            id="binance-fetch",
            max_instances=1,  # 同一时刻只允许一个抓取实例
            coalesce=True,    # 错过多次执行也只补一次
        )
        self._scheduler.start()
        logger.info("调度器已启动，间隔 %ss", FETCH_INTERVAL_SECONDS)

        # 立即触发首抓（不等 30s），失败也不阻塞启动
        asyncio.create_task(self._tick())

    async def stop(self) -> None:
        """停止调度器并清理订阅者。"""
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info("调度器已停止")

        # 通知所有订阅者退出（向队列塞一个 None 会让 stream 端识别为关闭）
        async with self._lock:
            for q in list(self._subscribers):
                # 用 put_nowait 避免阻塞，若队列满直接覆盖（最新一条即停止信号）
                try:
                    q.put_nowait(None)  # type: ignore[arg-type]
                except asyncio.QueueFull:
                    pass
            self._subscribers.clear()

    # ---------- 抓取与广播 ----------

    async def _tick(self) -> None:
        """单次抓取：失败时记日志、不抛出。"""
        try:
            snapshot = await self._fetcher.fetch()
        except Exception as exc:  # noqa: BLE001 — 调度器必须吞掉所有异常以保持存活
            logger.exception("Binance 抓取失败: %s", exc)
            return

        self._latest_snapshot = snapshot
        logger.info(
            "抓取完成 tokens=%d fetchedAt=%s",
            len(snapshot.tokens),
            snapshot.fetchedAt,
        )

        # 广播给所有订阅者
        await self._broadcast(snapshot)

    async def _broadcast(self, snapshot: SnapshotResponse) -> None:
        """把快照投递到每个订阅者的队列；慢消费者会被丢弃旧值只保留最新一条。"""
        async with self._lock:
            subscribers = list(self._subscribers)

        for q in subscribers:
            # 队列容量为 1：如果上一条还没被消费，先丢掉它再塞新值
            if q.full():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                q.put_nowait(snapshot)
            except asyncio.QueueFull:
                # 理论上不会到这里（上面已 drain）；保险起见忽略
                pass

    # ---------- 订阅管理 ----------

    async def subscribe(self) -> AsyncIterator[SnapshotResponse]:
        """注册一个新订阅者，返回异步迭代器。

        断开（generator close）时自动注销。
        若 hub 中已有最新快照，会先把它推给新订阅者，避免新连接要等 30s 才看到第一帧。
        """
        queue: asyncio.Queue[SnapshotResponse | None] = asyncio.Queue(
            maxsize=SUBSCRIBER_QUEUE_MAXSIZE
        )
        async with self._lock:
            self._subscribers.add(queue)  # type: ignore[arg-type]
        logger.info("SSE 新订阅者，当前订阅数=%d", len(self._subscribers))

        # 立即把当前缓存推给新订阅者
        if self._latest_snapshot is not None:
            queue.put_nowait(self._latest_snapshot)

        try:
            while True:
                item = await queue.get()
                if item is None:
                    # 停止信号
                    break
                yield item
        finally:
            async with self._lock:
                self._subscribers.discard(queue)  # type: ignore[arg-type]
            logger.info("SSE 订阅者断开，当前订阅数=%d", len(self._subscribers))


# 全局单例：FastAPI lifespan 启动时初始化
hub = SnapshotHub()
