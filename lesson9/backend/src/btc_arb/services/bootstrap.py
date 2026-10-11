"""启动时 bootstrap：把 ENV BOOTSTRAP_* 写入 setting 表对应空字段。

规则：
- 只填空：setting 表中 NULL/空字符串的字段才被 ENV 覆盖
- 非空跳过：避免 user 在 UI 改过的值被 ENV 回灌
- 每次启动都跑一遍（轻量），日志说明哪些字段被填了哪些被跳过
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_arb.config import get_settings
from btc_arb.db import get_session_factory
from btc_arb.logging import get_logger
from btc_arb.models.setting import Setting

logger = get_logger(__name__)


# (env 字段名, setting ORM 属性名) 映射
BOOTSTRAP_MAP = [
    ("bootstrap_openai_api_key", "openai_api_key"),
    ("bootstrap_openai_model", "openai_model"),
    ("bootstrap_web_search_api_key", "web_search_api_key"),
    ("bootstrap_feishu_webhook_url", "feishu_webhook_url"),
]


async def bootstrap_settings_from_env() -> dict[str, int]:
    """读 ENV，把 BOOTSTRAP_* 写入 setting 表的空字段。返回 {filled, skipped, missing_env}."""
    env = get_settings()
    factory = get_session_factory()
    filled: list[str] = []
    skipped: list[str] = []
    missing: list[str] = []

    async with factory() as session:
        row = (await session.execute(select(Setting).where(Setting.id == 1))).scalar_one_or_none()
        if row is None:
            logger.warning("bootstrap.no_setting_row")
            return {"filled": 0, "skipped": 0, "missing_env": 0}

        for env_attr, setting_attr in BOOTSTRAP_MAP:
            env_val = getattr(env, env_attr, None)
            current = getattr(row, setting_attr, None)
            if not env_val:
                missing.append(env_attr)
                continue
            if current and str(current).strip():
                skipped.append(setting_attr)
                continue
            setattr(row, setting_attr, env_val)
            filled.append(setting_attr)

        if filled:
            await session.commit()

    logger.info("bootstrap.done", filled=filled, skipped=skipped, missing_env=missing)
    return {
        "filled": len(filled),
        "skipped": len(skipped),
        "missing_env": len(missing),
    }
