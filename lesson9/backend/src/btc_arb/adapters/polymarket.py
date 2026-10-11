"""Polymarket 适配器：Gamma 查市场列表 + CLOB 取 YES 中价。"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import httpx

from btc_arb.logging import get_logger

logger = get_logger(__name__)

GAMMA_BASE = "https://gamma-api.polymarket.com"
CLOB_BASE = "https://clob.polymarket.com"
# 抓「$120,000 / $120000 / $120k / $1.2m / 120k / 1.2M」等写法
_STRIKE_RE = re.compile(
    r"\$?\s?([0-9]{1,3}(?:,[0-9]{3})+|[0-9]+(?:\.[0-9]+)?)\s?([kKmM])?",
)


class PolymarketError(Exception):
    """Polymarket 适配器调用失败。"""


class PolymarketClient:
    """httpx async 包装：Gamma + CLOB 两个端点。"""

    def __init__(self, timeout: float = 15.0) -> None:
        # 共享一个 client 实例，调用方手动 close 或用作 context manager
        self._client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> PolymarketClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def fetch_event_pick_closest_to_half(self, event_slug: str) -> dict[str, Any] | None:
        """通过 event slug 拉 event，挑 YES midpoint 最接近 0.5 的二元 sub-market。

        返回归一化字典（与 fetch_btc_markets 输出格式一致），失败/未找到返 None。
        用于：daily discover 拉某天的 bitcoin-above-on-{date} event。
        """
        try:
            resp = await self._client.get(
                f"{GAMMA_BASE}/events", params={"slug": event_slug}
            )
            resp.raise_for_status()
            events = resp.json()
        except httpx.HTTPError as e:
            logger.warning("polymarket.event_fetch_failed", slug=event_slug, error=str(e))
            return None
        if not isinstance(events, list) or not events:
            return None
        event = events[0]

        # 二元 + active sub-markets
        candidates = []
        for sub in (event.get("markets") or []):
            if sub.get("active") is False or sub.get("closed") is True:
                continue
            tids = self._safe_json_list(sub.get("clobTokenIds"))
            outs = self._safe_json_list(sub.get("outcomes"))
            if not tids or len(tids) != 2 or not outs or len(outs) != 2:
                continue
            yes_idx = next(
                (i for i, o in enumerate(outs) if str(o).strip().lower() == "yes"),
                None,
            )
            if yes_idx is None:
                continue
            candidates.append((sub, str(tids[yes_idx]), 1 - yes_idx, tids))
        if not candidates:
            return None

        # 取 midpoint 挑最接近 0.5
        best: tuple[dict[str, Any], float, str, str, float] | None = None
        for sub, yes_tid, no_idx, tids in candidates:
            mid = await self.fetch_midpoint(yes_tid)
            if mid is None:
                continue
            dist = abs(mid - 0.5)
            if best is None or dist < best[1]:
                best = (sub, dist, yes_tid, str(tids[no_idx]), mid)
        if best is None:
            # 全部 midpoint 失败 → 退化挑第一个，midpoint 标 None
            sub, yes_tid, no_idx, tids = candidates[0]
            best = (sub, 1.0, yes_tid, str(tids[no_idx]), 0.5)

        chosen_sub, _dist, yes_tid, no_tid, chosen_mid = best

        # 解析 strike / direction
        strike, direction = _parse_strike_and_direction(chosen_sub.get("question") or "")

        # endDate
        end_iso = chosen_sub.get("endDate") or chosen_sub.get("end_date_iso")
        if not end_iso:
            return None
        try:
            resolve_at = datetime.fromisoformat(str(end_iso).replace("Z", "+00:00"))
            if resolve_at.tzinfo is None:
                resolve_at = resolve_at.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None

        return {
            "condition_id": chosen_sub.get("conditionId") or chosen_sub.get("condition_id") or "",
            "slug": chosen_sub.get("slug") or "",
            "event_slug": event_slug,
            "question": chosen_sub.get("question") or "",
            "description": chosen_sub.get("description") or event.get("description"),
            "strike_price": strike,
            "direction": direction,
            "resolve_at": resolve_at,
            "outcome_yes_token_id": yes_tid,
            "outcome_no_token_id": no_tid,
            "chosen_midpoint": f"{chosen_mid:.4f}",
        }

    @staticmethod
    def _safe_json_list(v: Any) -> list[Any] | None:
        """Gamma 偶尔把 outcomes/clobTokenIds 字段返回为 JSON 字符串。"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            import json as _json
            try:
                parsed = _json.loads(v)
                return parsed if isinstance(parsed, list) else None
            except (ValueError, TypeError):
                return None
        return None

    async def fetch_btc_markets(self, keywords: list[str], max_days_to_resolve: int = 30) -> list[dict[str, Any]]:
        """拉一批活跃市场，按关键词 + 时间窗 + 二元结构过滤后返回归一化字典。

        策略：
        1. /events?tag=bitcoin&active=true 拿到 BTC 事件，每个事件包含多个 sub-market（如 "above $70k", "above $72k"）
        2. /markets?active=true 多页扫，补充直接挂在 markets 列表的 BTC 二元市场
        合并去重 condition_id 后过滤。
        """
        raw_markets: list[dict[str, Any]] = []

        # 1. 通过 events tag 拿 BTC 主题事件
        # 策略：每个 event 内只挑「YES 中价最接近 0.5」的 1 个二元 sub-market 入库
        # （避免同一 event 多个 strike 子市场污染 dashboard，且最接近 50% 的市场套利信息量最高）
        kw_lower = [k.lower() for k in keywords]
        try:
            resp = await self._client.get(
                f"{GAMMA_BASE}/events",
                params={"tag": "bitcoin", "active": "true", "closed": "false", "limit": "100"},
            )
            resp.raise_for_status()
            events = resp.json()
            if isinstance(events, list):
                events_picked = 0
                for event in events:
                    ev_slug = event.get("slug") or ""
                    # 关键词预过滤：event title / slug 含关键词
                    ev_haystack = (
                        f"{(event.get('title') or '').lower()} "
                        f"{ev_slug.lower()}"
                    )
                    if not any(k in ev_haystack for k in kw_lower):
                        continue
                    # 该 event 下二元 + active sub-markets
                    candidates = []
                    for sub in (event.get("markets") or []):
                        if sub.get("active") is False or sub.get("closed") is True:
                            continue
                        tids = self._safe_json_list(sub.get("clobTokenIds"))
                        outs = self._safe_json_list(sub.get("outcomes"))
                        if not tids or len(tids) != 2 or not outs or len(outs) != 2:
                            continue
                        yes_idx = next(
                            (i for i, o in enumerate(outs) if str(o).strip().lower() == "yes"),
                            None,
                        )
                        if yes_idx is None:
                            continue
                        candidates.append((sub, str(tids[yes_idx])))
                    if not candidates:
                        continue
                    # 给每个 candidate 取 YES midpoint，挑最接近 0.5 的
                    best: tuple[dict[str, Any], float] | None = None
                    for sub, yes_tid in candidates:
                        mid = await self.fetch_midpoint(yes_tid)
                        if mid is None:
                            continue
                        dist = abs(mid - 0.5)
                        if best is None or dist < best[1]:
                            best = (sub, dist)
                    if best is None:
                        # 全部 midpoint 失败 → 退化挑第一个
                        best = (candidates[0][0], 1.0)
                    chosen = best[0]
                    chosen["_event_slug"] = ev_slug
                    raw_markets.append(chosen)
                    events_picked += 1
                logger.info("polymarket.events_btc", events_total=len(events),
                            events_picked=events_picked)
        except httpx.HTTPError as e:
            logger.warning("polymarket.events_failed", error=str(e))

        # 2. 补充直接 markets 列表（多页扫）
        for offset in (0, 200, 400):
            try:
                resp = await self._client.get(
                    f"{GAMMA_BASE}/markets",
                    params={"active": "true", "closed": "false", "archived": "false",
                            "limit": "200", "offset": str(offset)},
                )
                resp.raise_for_status()
                page = resp.json()
                if isinstance(page, list):
                    raw_markets.extend(page)
                    if len(page) < 200:
                        break  # 没满页说明到底了
            except httpx.HTTPError as e:
                logger.warning("polymarket.markets_failed", offset=offset, error=str(e))

        # condition_id 去重
        seen_ids: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for m in raw_markets:
            cid = m.get("conditionId") or m.get("condition_id") or ""
            if not cid or cid in seen_ids:
                continue
            seen_ids.add(cid)
            deduped.append(m)
        raw_markets = deduped
        if not raw_markets:
            raise PolymarketError("gamma returned 0 markets total")

        now = datetime.now(timezone.utc)
        normalized: list[dict[str, Any]] = []

        for m in raw_markets:
            # 关键词匹配：question / slug / tags 任一含关键词
            question = (m.get("question") or "").lower()
            slug = (m.get("slug") or "").lower()
            tags = " ".join(str(t).lower() for t in (m.get("tags") or []))
            haystack = f"{question} {slug} {tags}"
            if not any(k in haystack for k in kw_lower):
                continue

            # 二元市场：outcomes 长度必须 == 2 且 YES/NO
            outcomes = m.get("outcomes")
            if isinstance(outcomes, str):
                # gamma 偶尔返回 JSON 字符串
                import json as _json
                try:
                    outcomes = _json.loads(outcomes)
                except (ValueError, TypeError):
                    outcomes = None
            if not isinstance(outcomes, list) or len(outcomes) != 2:
                continue

            # clob token ids
            token_ids = m.get("clobTokenIds")
            if isinstance(token_ids, str):
                import json as _json
                try:
                    token_ids = _json.loads(token_ids)
                except (ValueError, TypeError):
                    token_ids = None
            if not isinstance(token_ids, list) or len(token_ids) != 2:
                continue

            # YES token：outcomes 里 == "Yes" 那一项对应的 token_id
            yes_idx = next(
                (i for i, o in enumerate(outcomes) if str(o).strip().lower() == "yes"),
                None,
            )
            if yes_idx is None:
                continue
            no_idx = 1 - yes_idx

            # 截止时间
            end_iso = m.get("endDate") or m.get("end_date_iso")
            if not end_iso:
                continue
            try:
                resolve_at = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
                if resolve_at.tzinfo is None:
                    resolve_at = resolve_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue

            # 时间窗：未来 N 天内
            days_left = (resolve_at - now).total_seconds() / 86400
            if days_left <= 0 or days_left > max_days_to_resolve:
                continue

            # 解析 strike / direction（best-effort，失败时为 None，预测时降级）
            strike, direction = _parse_strike_and_direction(m.get("question") or "")

            normalized.append({
                "condition_id": m.get("conditionId") or m.get("condition_id") or "",
                "slug": m.get("slug") or "",
                "event_slug": m.get("_event_slug") or "",  # 若来自 event，记录 event slug 用于真实 URL
                "question": m.get("question") or "",
                "description": m.get("description"),
                "strike_price": strike,
                "direction": direction,
                "resolve_at": resolve_at,
                "outcome_yes_token_id": str(token_ids[yes_idx]),
                "outcome_no_token_id": str(token_ids[no_idx]),
            })

        logger.info("polymarket.fetch_btc_markets", total_raw=len(raw_markets), matched=len(normalized))
        return normalized

    async def fetch_midpoint(self, token_id: str) -> float | None:
        """CLOB 取单个 token 的中价。返回 [0,1] 浮点；失败返 None（调用方决定 stale 策略）。"""
        try:
            resp = await self._client.get(f"{CLOB_BASE}/midpoint", params={"token_id": token_id})
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("polymarket.midpoint_failed", token_id=token_id, error=str(e))
            return None
        data = resp.json()
        mid = data.get("mid")
        if mid is None:
            return None
        try:
            value = float(mid)
        except (ValueError, TypeError):
            return None
        # clip 到 (0,1) 边界，避免极端值后续除零
        return max(0.001, min(0.999, value))


def _parse_strike_and_direction(question: str) -> tuple[float | None, str | None]:
    """从 question 文本里尽力提取 strike 价 + 方向（above/below）。

    e.g. "Will Bitcoin reach $120,000 by Dec 31?" → (120000.0, "above")
         "Will BTC be below $90k on Jan 1?" → (90000.0, "below")
    解析失败时返回 (None, None)，下游预测会降级到无方向模型。
    """
    q = question.lower()
    direction: str | None = None
    if any(w in q for w in ("reach", "above", "exceed", "hit", "≥", ">=", ">")):
        direction = "above"
    elif any(w in q for w in ("below", "under", "<", "<=", "≤", "less than")):
        direction = "below"

    m = _STRIKE_RE.search(question)
    if not m:
        return None, direction
    raw = m.group(1).replace(",", "")
    suffix = (m.group(2) or "").lower()
    try:
        value = float(raw)
    except ValueError:
        return None, direction
    if suffix == "k":
        value *= 1_000
    elif suffix == "m":
        value *= 1_000_000
    # 过滤掉明显不是 BTC 价的数字（如年份 2026、小金额 < 1000）
    if value < 1_000 or value > 10_000_000:
        return None, direction
    return value, direction
