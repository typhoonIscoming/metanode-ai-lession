"""设置路由：GET 真实读 + PATCH 部分字段更新 + test_feishu 真发测试卡片。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_arb.adapters.feishu import FeishuClient
from btc_arb.db import get_session
from btc_arb.models.setting import Setting
from btc_arb.schemas.setting import SettingView, mask_secret

router = APIRouter(prefix="/settings", tags=["settings"])

SessionDep = Depends(get_session)

# 允许 PATCH 的字段白名单 + 各自的类型/校验
PATCHABLE_FIELDS = {
    "entry_threshold": float,
    "debounce_minutes": int,
    "price_poll_minutes": int,
    "predict_ttl_hours": int,
    "discovery_keywords": list,
    "discovery_max_days_to_resolve": int,
    "feishu_webhook_url": str,
    "openai_api_key": str,
    "openai_model": str,
    "web_search_provider": str,
    "web_search_api_key": str,
}


def _to_view(row: Setting) -> SettingView:
    return SettingView(
        entry_threshold=f"{float(row.entry_threshold):.3f}",
        debounce_minutes=row.debounce_minutes,
        price_poll_minutes=row.price_poll_minutes,
        predict_ttl_hours=row.predict_ttl_hours,
        discovery_keywords=list(row.discovery_keywords),
        discovery_max_days_to_resolve=row.discovery_max_days_to_resolve,
        feishu_webhook_url=mask_secret(row.feishu_webhook_url),
        openai_api_key=mask_secret(row.openai_api_key),
        openai_model=row.openai_model,
        web_search_provider=row.web_search_provider,
        web_search_api_key=mask_secret(row.web_search_api_key),
        updated_at=row.updated_at,
    )


@router.get("", response_model=SettingView)
async def get_settings_view(session: AsyncSession = SessionDep) -> SettingView:
    row = (await session.execute(select(Setting).where(Setting.id == 1))).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="setting row missing; run `alembic upgrade head` to seed defaults",
        )
    return _to_view(row)


@router.patch("", response_model=SettingView)
async def patch_settings(
    body: dict[str, Any],
    session: AsyncSession = SessionDep,
) -> SettingView:
    """部分字段更新。前端如果传 mask 字符串（含 `***hidden***`），后端忽略不覆盖。"""
    row = (await session.execute(select(Setting).where(Setting.id == 1))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=503, detail="setting missing")

    applied: list[str] = []
    for k, v in body.items():
        if k not in PATCHABLE_FIELDS:
            continue
        # 跳过 mask 形态的"未改"字段（前端 GET 拿到 mask 串后回传时不更新）
        if isinstance(v, str) and "***hidden***" in v:
            continue
        expected_type = PATCHABLE_FIELDS[k]
        if v is None:
            setattr(row, k, None)
        elif expected_type is float:
            setattr(row, k, float(v))
        elif expected_type is int:
            setattr(row, k, int(v))
        elif expected_type is list:
            if not isinstance(v, list):
                raise HTTPException(status_code=422, detail=f"{k} must be a list")
            setattr(row, k, [str(x) for x in v])
        else:
            setattr(row, k, str(v) if v != "" else None)
        applied.append(k)

    if applied:
        row.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(row)
    return _to_view(row)


@router.post("/test_feishu", status_code=status.HTTP_200_OK)
async def test_feishu(session: AsyncSession = SessionDep) -> dict[str, Any]:
    """读取当前 webhook，发一条"测试卡片"。webhook 未配 → 422。"""
    row = (await session.execute(select(Setting).where(Setting.id == 1))).scalar_one()
    if not row.feishu_webhook_url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="feishu_webhook_url 未配置",
        )
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "🔔 BTC 套利信号 · 飞书 webhook 测试"},
                "template": "blue",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            "若你看到这条卡片，说明 webhook 配置正确。\n"
                            "正常运行时将由后台调度按以下节奏推送：\n"
                            "- 每小时拉一次 Polymarket BTC 市场\n"
                            "- 每 30 分钟跑一次 AI 预测\n"
                            "- 每 5 分钟轮询价格 + 跑信号引擎"
                        ),
                    },
                },
            ],
        },
    }
    try:
        async with FeishuClient(row.feishu_webhook_url) as fc:
            result = await fc.push_card(payload)
        # 飞书成功响应：{"code": 0, "msg": "success", ...}
        return {
            "ok": True,
            "status": 200,
            "response": result if isinstance(result, dict) and "code" in result else {"code": 0, "msg": "dry_run" if result.get("dry_run") else "ok", **result},
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "status": 500, "error": str(e)[:300]}
