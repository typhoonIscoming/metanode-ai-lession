"""统一异常体系，对应 backend-PRD §7。

FastAPI 全局处理器把 `AppError` 子类转 422 + {error: {code, message}}；
其它未捕获异常转 500 + INTERNAL_ERROR。处理器注册在 B-04 中完成。
"""

from __future__ import annotations


class AppError(Exception):
    """业务异常基类。所有子类必须声明 `code`。"""

    code: str = "APP_ERROR"

    def __init__(self, message: str | None = None, details: dict | None = None) -> None:
        super().__init__(message or self.code)
        self.message = message or self.code
        self.details = details or {}


# --- 外部依赖类 ---


class PolymarketError(AppError):
    code = "POLYMARKET_UNAVAILABLE"


class LLMUnavailableError(AppError):
    code = "LLM_UNAVAILABLE"


class WebSearchEmptyError(AppError):
    """非异常，仅作为 info 级别信号给上层，触发「无新闻」路径。"""

    code = "WEBSEARCH_EMPTY"


class SpotUnavailableError(AppError):
    code = "SPOT_UNAVAILABLE"


class FeishuPushError(AppError):
    code = "FEISHU_PUSH_FAILED"


# --- 用户输入类 ---


class UrlInvalidError(AppError):
    code = "URL_INVALID"


class MarketNotSupportedError(AppError):
    code = "MARKET_NOT_SUPPORTED"


class MarketNotBinaryError(AppError):
    code = "MARKET_NOT_BINARY"


class MarketResolvedError(AppError):
    code = "MARKET_RESOLVED"


class MarketNotParsableError(AppError):
    code = "MARKET_NOT_PARSABLE"


class MarketNotFoundError(AppError):
    code = "MARKET_NOT_FOUND"
