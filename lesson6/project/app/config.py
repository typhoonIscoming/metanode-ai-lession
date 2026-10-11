"""集中加载环境变量。所有模块通过 `settings` 单例读配置。"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    binance_testnet_api_key: str = Field(default="")
    binance_testnet_api_secret: str = Field(default="")
    binance_testnet_base_url: str = Field(default="https://testnet.binance.vision")

    quant_db_url: str = Field(default="sqlite:///quant.db")
    log_level: str = Field(default="INFO")


settings = Settings()
