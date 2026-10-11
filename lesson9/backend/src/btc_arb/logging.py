"""structlog 配置：JSON 输出到 stdout，所有时间 UTC ISO+Z。

B-04 会扩展请求上下文与敏感字段过滤；当前仅做基础 JSON renderer。
"""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime

import structlog


def _iso_utc_z(_logger, _method, event_dict):
    """覆盖 timestamp，强制 UTC + Z 后缀，符合项目时区规约。"""
    event_dict["timestamp"] = (
        datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    )
    return event_dict


_PROCESSORS = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    _iso_utc_z,
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.JSONRenderer(),
]


def configure_logging(level: str = "info") -> None:
    """初始化 structlog；同时收编 stdlib logging 走同一个 renderer。

    注意：cache_logger_on_first_use=False，避免某个 module 在 configure 之前
    `get_logger()` 拿到默认处理器后被永久缓存（B-04 接入完整 stdlib 桥接后再开启）。
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    structlog.configure(
        processors=_PROCESSORS,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


# 模块加载时立刻设一个安全的默认（避免 import 链上某个 module 先 get_logger）
configure_logging()


def get_logger(name: str | None = None):
    """统一 logger 入口。"""
    return structlog.get_logger(name)
