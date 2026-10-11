"""手动预测路由：贴 Polymarket URL → 拉市场 → 跑 quant+LLM。

两个模式：
- persist=false (默认)：dry-run，不入库不监控不推送
- persist=true：upsert market + 写 prediction/tick + 跑 signal_engine + 推送飞书
  （condition_id 重复则更新已有 market，不新建）
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_arb.adapters.binance import BinanceClient, BinanceError
from btc_arb.adapters.openai_llm import LLMAdjuster
from btc_arb.adapters.polymarket import GAMMA_BASE, _parse_strike_and_direction
from btc_arb.db import get_session
from btc_arb.logging import get_logger
from btc_arb.models.market import Market
from btc_arb.models.prediction import Prediction
from btc_arb.models.price_tick import PriceTick
from btc_arb.models.setting import Setting
from btc_arb.services.notification import push_unpushed_signals
from btc_arb.services.prediction import DEMO_FORCE_MIN_GAP
from btc_arb.services.quant import MODEL_VERSION, quant_probability
from btc_arb.services.signal_engine import evaluate_all_active

router = APIRouter(tags=["predict"])
logger = get_logger(__name__)

SessionDep = Depends(get_session)


def _extract_slug(url: str) -> str | None:
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    host = parsed.netloc.lower()
    if host != "polymarket.com" and not host.endswith(".polymarket.com"):
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2 and parts[0] in ("event", "market", "markets", "events"):
        return parts[1]
    if len(parts) >= 1:
        return parts[-1]
    return None


def _is_binary_market(m: dict[str, Any]) -> tuple[list[Any], list[Any]] | None:
    outcomes = m.get("outcomes")
    if isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except (ValueError, TypeError):
            return None
    if not isinstance(outcomes, list) or len(outcomes) != 2:
        return None
    tids = m.get("clobTokenIds")
    if isinstance(tids, str):
        try:
            tids = json.loads(tids)
        except (ValueError, TypeError):
            return None
    if not isinstance(tids, list) or len(tids) != 2:
        return None
    return outcomes, tids


async def _midpoint(client: httpx.AsyncClient, token_id: str) -> float | None:
    try:
        resp = await client.get(
            "https://clob.polymarket.com/midpoint",
            params={"token_id": token_id},
        )
        if resp.status_code != 200:
            return None
        return float(resp.json().get("mid"))
    except (httpx.HTTPError, ValueError, TypeError):
        return None


async def _fetch_market_by_slug(slug: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """slug → (chosen_market, event)。event 非 None 表示从 event 集合挑了最接近 50% 的子市场。"""
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        try:
            resp = await client.get(f"{GAMMA_BASE}/markets", params={"slug": slug})
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and data and _is_binary_market(data[0]) is not None:
                    return data[0], None
        except httpx.HTTPError as e:
            logger.warning("predict.gamma_markets_failed", slug=slug, error=str(e))

        try:
            resp = await client.get(f"{GAMMA_BASE}/events", params={"slug": slug})
            if resp.status_code != 200:
                return None, None
            events = resp.json()
            if not isinstance(events, list) or not events:
                return None, None
            event = events[0]
            sub_markets = [m for m in (event.get("markets") or []) if _is_binary_market(m) is not None]
            if not sub_markets:
                return None, event

            yes_token_ids = []
            for m in sub_markets:
                outs, tids = _is_binary_market(m)  # type: ignore[misc]
                yes_idx = next(
                    (i for i, o in enumerate(outs) if str(o).strip().lower() == "yes"),
                    0,
                )
                yes_token_ids.append(str(tids[yes_idx]))

            mids = [await _midpoint(client, tid) for tid in yes_token_ids]

            best_idx = None
            best_dist = 2.0
            for i, mid in enumerate(mids):
                if mid is None:
                    continue
                d = abs(mid - 0.5)
                if d < best_dist:
                    best_dist = d
                    best_idx = i

            if best_idx is None:
                return sub_markets[0], event
            chosen = sub_markets[best_idx]
            chosen["_chosen_midpoint"] = mids[best_idx]
            chosen["_event_title"] = event.get("title") or event.get("slug")
            chosen["_event_slug"] = event.get("slug")
            chosen["_event_sub_count"] = len(sub_markets)
            return chosen, event
        except httpx.HTTPError as e:
            logger.warning("predict.gamma_events_failed", slug=slug, error=str(e))

    return None, None


def _normalize_market(m: dict[str, Any]) -> dict[str, Any] | None:
    """精简归一化：必须是二元 + 有 endDate。"""
    outcomes = m.get("outcomes")
    if isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except (ValueError, TypeError):
            return None
    if not isinstance(outcomes, list) or len(outcomes) != 2:
        return None

    tids = m.get("clobTokenIds")
    if isinstance(tids, str):
        try:
            tids = json.loads(tids)
        except (ValueError, TypeError):
            return None
    if not isinstance(tids, list) or len(tids) != 2:
        return None
    yes_idx = next((i for i, o in enumerate(outcomes) if str(o).strip().lower() == "yes"), 0)

    end_iso = m.get("endDate") or m.get("end_date_iso")
    if not end_iso:
        return None
    try:
        resolve_at = datetime.fromisoformat(str(end_iso).replace("Z", "+00:00"))
        if resolve_at.tzinfo is None:
            resolve_at = resolve_at.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None

    strike, direction = _parse_strike_and_direction(m.get("question") or "")
    return {
        "condition_id": m.get("conditionId") or m.get("condition_id") or "",
        "question": m.get("question") or "",
        "slug": m.get("slug") or "",
        "description": m.get("description"),
        "strike_price": strike,
        "direction": direction or "above",
        "resolve_at": resolve_at,
        "outcome_yes_token_id": str(tids[yes_idx]),
        "outcome_no_token_id": str(tids[1 - yes_idx]),
    }


@router.post("/predict", status_code=status.HTTP_200_OK)
async def predict(
    body: dict[str, Any],
    session: AsyncSession = SessionDep,
) -> dict[str, Any]:
    """贴 Polymarket URL → 拉 + 量化 + LLM → 预测结果。

    body:
      polymarket_url: str (required)
      persist: bool (default false) — true 时入库 + 跑 signal_engine + 推飞书

    persist=true 行为：
    - condition_id 不在 DB → INSERT market（state=WATCHING, source=manual,
      last_state_change_at 推到去抖窗口外让信号能立刻触发）
    - condition_id 已存在 → 复用已有 market，不重复插
    - 写 prediction + 写当前 midpoint 到 price_tick
    - 跑 signal_engine.evaluate_all_active → 可能触发 ENTRY 信号
    - 跑 push_unpushed_signals → 真实推飞书
    """
    url = (body.get("polymarket_url") or "").strip()
    if not url:
        raise HTTPException(status_code=422, detail="polymarket_url required")
    persist = bool(body.get("persist", False))

    slug = _extract_slug(url)
    if not slug:
        raise HTTPException(
            status_code=422,
            detail="无法从 URL 解析 slug；URL 应类似 https://polymarket.com/event/xxxxx",
        )

    raw, event = await _fetch_market_by_slug(slug)
    if raw is None:
        raise HTTPException(
            status_code=404,
            detail=f"未在 Polymarket 找到 slug={slug} 的市场（也不是 event 集合）",
        )

    m = _normalize_market(raw)
    if m is None:
        raise HTTPException(
            status_code=422,
            detail="该市场不是二元 Yes/No 结构或缺 endDate；v1 仅支持二元 BTC 价格预测",
        )

    event_slug = None
    if event is not None:
        m["chosen_from_event"] = raw.get("_event_title") or event.get("title")
        m["event_sub_count"] = raw.get("_event_sub_count")
        m["chosen_midpoint"] = raw.get("_chosen_midpoint")
        event_slug = raw.get("_event_slug") or event.get("slug")

    # spot + vol
    try:
        async with BinanceClient() as bc:
            spot = await bc.fetch_spot_price()
            vol = await bc.fetch_realized_volatility(days=30)
    except BinanceError as e:
        raise HTTPException(status_code=502, detail=f"Binance 取数失败：{e}") from e

    # 当前市场价（YES token midpoint），用于 nudge p_ai 远离市场价
    p_mkt = m.get("chosen_midpoint")  # event 集合时已拿过
    if p_mkt is None:
        async with httpx.AsyncClient(timeout=10.0) as c:
            p_mkt = await _midpoint(c, m["outcome_yes_token_id"])

    # quant
    if m["strike_price"] and m["direction"]:
        p_quant = quant_probability(
            spot_price=spot,
            strike_price=m["strike_price"],
            direction=m["direction"],
            resolve_at=m["resolve_at"],
            realized_vol=vol,
        )
        quant_rationale = (
            f"对数正态：spot={spot:.2f}, strike={m['strike_price']:.2f}, "
            f"direction={m['direction']}, vol={vol:.4f} → p_quant={p_quant:.4f}"
        )
    else:
        p_quant = 0.5
        quant_rationale = "无法从问题文本解析 strike/方向，量化退化到 0.5"

    # LLM
    setting = (await session.execute(select(Setting).where(Setting.id == 1))).scalar_one()
    llm_adjustment = 0.0
    llm_confidence: str | None = None
    llm_rationale = quant_rationale
    model_version = MODEL_VERSION

    if setting.openai_api_key and m["strike_price"] and m["direction"]:
        async with LLMAdjuster(
            api_key=setting.openai_api_key,
            model=setting.openai_model or "gpt-5.5",
        ) as llm:
            adj = await llm.adjust(
                question=m["question"],
                p_quant=p_quant,
                spot_price=spot,
                resolve_at=m["resolve_at"],
            )
        if adj is not None:
            llm_adjustment = adj.adjustment
            llm_confidence = adj.confidence
            llm_rationale = f"[LLM] {adj.rationale}\n[Quant] {quant_rationale}"
            model_version = f"{MODEL_VERSION}+llm-{setting.openai_model}"
        else:
            llm_rationale = f"[LLM-FAIL] 调用失败\n[Quant] {quant_rationale}"
            model_version = f"{MODEL_VERSION}-llm-fail"

    p_ai = max(0.001, min(0.999, p_quant + llm_adjustment))

    # demo 套利偏向：保证 |p_ai - p_mkt| >= 20pp
    if p_mkt is not None and DEMO_FORCE_MIN_GAP > 0:
        gap = p_ai - p_mkt
        if abs(gap) < DEMO_FORCE_MIN_GAP:
            direction_sign = (1.0 if gap > 0 else -1.0) if abs(gap) > 1e-6 else (1.0 if p_quant >= 0.5 else -1.0)
            target = p_mkt + direction_sign * DEMO_FORCE_MIN_GAP
            nudged = max(0.001, min(0.999, target))
            llm_rationale = (
                f"[NUDGED for demo: |{p_ai:.3f}-{p_mkt:.3f}|<{DEMO_FORCE_MIN_GAP:.2f} → "
                f"p_ai 从 {p_ai:.4f} 调整到 {nudged:.4f}]\n{llm_rationale}"
            )
            p_ai = nudged
            model_version = f"{model_version}-nudged"

    persist_result: dict[str, Any] = {}
    if persist:
        persist_result = await _persist_and_signal(
            session,
            normalized=m,
            event_slug=event_slug,
            p_ai=p_ai, p_quant=p_quant,
            llm_adjustment=llm_adjustment, llm_confidence=llm_confidence,
            llm_rationale=llm_rationale, model_version=model_version,
            spot=spot, vol=vol,
            p_mkt=p_mkt,
        )

    return {
        "market_preview": {
            "question": m["question"],
            "strike_price": f"{m['strike_price']:.8f}" if m["strike_price"] is not None else None,
            "direction": m["direction"],
            "resolve_at": m["resolve_at"].isoformat(),
            "chosen_from_event": m.get("chosen_from_event"),
            "event_sub_count": m.get("event_sub_count"),
            "chosen_midpoint": (
                f"{m['chosen_midpoint']:.4f}"
                if isinstance(m.get("chosen_midpoint"), (int, float))
                else None
            ),
        },
        "prediction": {
            "id": persist_result.get("prediction_id", 0),
            "p_ai": f"{p_ai:.4f}",
            "p_quant": f"{p_quant:.4f}",
            "llm_adjustment": f"{llm_adjustment:.4f}",
            "llm_confidence": llm_confidence,
            "llm_rationale": llm_rationale,
            "news_sources": [],
            "spot_price": f"{spot:.8f}",
            "realized_vol": f"{vol:.6f}",
            "model_version": model_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "persist": persist_result if persist else None,
    }


async def _persist_and_signal(
    session: AsyncSession,
    *,
    normalized: dict[str, Any],
    event_slug: str | None,
    p_ai: float, p_quant: float,
    llm_adjustment: float, llm_confidence: str | None,
    llm_rationale: str, model_version: str,
    spot: float, vol: float,
    p_mkt: float | None,
) -> dict[str, Any]:
    """入库 + 跑信号 + 推送。失败时返回 partial dict（不抛）。"""
    now = datetime.now(timezone.utc)
    cid = normalized["condition_id"]
    if not cid:
        return {"error": "no condition_id, cannot persist"}

    # upsert market
    existing = (
        await session.execute(select(Market).where(Market.condition_id == cid))
    ).scalar_one_or_none()
    market_created = False
    if existing is None:
        md = {"discovered_at": now.isoformat(), "source_url": "manual_predict"}
        if event_slug:
            md["event_slug"] = event_slug
        # last_state_change_at 推到去抖窗口外让信号能立刻触发
        market = Market(
            condition_id=cid,
            slug=normalized.get("slug") or "",
            question=normalized.get("question") or "",
            description=normalized.get("description"),
            strike_price=normalized.get("strike_price"),
            direction=normalized.get("direction") or "above",
            resolve_at=normalized["resolve_at"],
            outcome_yes_token_id=normalized["outcome_yes_token_id"],
            outcome_no_token_id=normalized["outcome_no_token_id"],
            state="WATCHING",
            source="manual",
            last_state_change_at=now - timedelta(minutes=30),
            market_metadata=md,
        )
        session.add(market)
        await session.flush()
        market_created = True
    else:
        market = existing
        # 已存在：把 last_state_change_at 推到去抖窗口外，确保信号可触发
        if market.state == "WATCHING":
            market.last_state_change_at = now - timedelta(minutes=30)

    # 写 prediction
    pred = Prediction(
        market_id=market.id,
        p_ai=p_ai,
        p_quant=p_quant,
        llm_adjustment=llm_adjustment,
        llm_confidence=llm_confidence,
        llm_rationale=llm_rationale,
        news_sources=[],
        spot_price=spot,
        realized_vol=vol,
        model_version=model_version,
    )
    session.add(pred)
    await session.flush()
    prediction_id = pred.id

    # 写 price_tick（p_mkt 已经在外面拿过）
    tick_created = False
    if p_mkt is not None:
        session.add(PriceTick(market_id=market.id, p_yes=p_mkt, p_no=1.0 - p_mkt))
        tick_created = True

    await session.commit()

    # 跑信号引擎 + 推送（共用现有 service）
    signal_stats: dict[str, Any] = {}
    push_stats: dict[str, Any] = {}
    try:
        signal_stats = await evaluate_all_active(session)
    except Exception as e:  # noqa: BLE001
        logger.warning("predict.persist_signal_failed", error=str(e))
        signal_stats = {"error": str(e)[:200]}
    try:
        push_stats = await push_unpushed_signals(session)
    except Exception as e:  # noqa: BLE001
        logger.warning("predict.persist_push_failed", error=str(e))
        push_stats = {"error": str(e)[:200]}

    return {
        "market_id": market.id,
        "market_created": market_created,
        "prediction_id": prediction_id,
        "tick_created": tick_created,
        "signal_stats": signal_stats,
        "push_stats": push_stats,
    }
