"""应用配置：仅装载 infra 层 ENV（数据库 / Web / 日志 / bootstrap 密钥）。

业务参数（阈值、调度间隔、API key 等）存 `setting` 表，运行时通过 PATCH /api/v1/settings 改。
ENV 中的 BOOTSTRAP_* 字段仅在 setting 表对应字段为 NULL 时被首次写入。
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从环境变量装载的 infra 配置。"""

    # 数据库（async driver）
    database_url: str = Field(
        default="postgresql+asyncpg://btc_arb:btc_arb@localhost:5432/btc_arb",
        description="SQLAlchemy async 连接串",
    )

    # Web 服务
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = Field(default="info")

    # CORS：逗号分隔的源列表
    cors_allow_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="允许的前端源，逗号分隔",
    )

    # bootstrap 密钥（启动时检测 setting 表对应字段为空就写入；非空不覆盖）
    # 这样 user 改了 setting UI 后 ENV 不会回灌覆盖
    bootstrap_openai_api_key: str | None = None
    bootstrap_openai_model: str | None = None
    bootstrap_openai_base_url: str | None = None
    bootstrap_web_search_api_key: str | None = None
    bootstrap_feishu_webhook_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """把逗号分隔的 CORS 源拆成列表。"""
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例 settings，进程级缓存。"""
    return Settings()
