"""LLM 调整器适配器：调 OpenAI 兼容端点（默认 AIHubMix）返回对市场 YES 概率的调整。

设计：
- 与模型无关：URL/key/model 都从 setting 表读，便于换 provider
- 调用失败返 None，不抛；上游决定降级策略（fallback 到纯量化 + 后缀标记）
- 输入：市场问题 + 量化模型 P(YES) + 当前 BTC 现价 + 距结算时间
- 输出：JSON {adjustment ∈ [-0.30, 0.30], confidence ∈ {low/medium/high}, rationale: str}
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from btc_arb.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class LLMAdjustment:
    """LLM 返回的调整结构（与 Prediction 表字段对齐）。"""

    adjustment: float
    confidence: str  # low / medium / high
    rationale: str
    raw_response: dict[str, Any]


SYSTEM_PROMPT = """你是一个加密货币市场分析助手。你的任务是评估 Polymarket 上 BTC 二元价格预测市场的真实概率。

输入会给你：
- 市场问题（如 "Will BTC reach $120,000 by Dec 31?"）
- 量化模型的初始 P(YES) 估计（基于对数正态 + 历史波动率）
- 当前 BTC 现货价
- 距离结算的剩余天数

输出 JSON：
{
  "adjustment": <-0.30 到 0.30 之间的浮点数>,
  "confidence": "low" | "medium" | "high",
  "rationale": "<2-3 句中文解释你为什么这样调整，包含具体逻辑>"
}

调整原则：
- adjustment 是对量化基线 P(YES) 的偏移，正值表示你认为真实概率高于量化值
- 在没有强烈方向性证据（如近期新闻、监管事件、链上数据异常）时，adjustment 应接近 0（±0.05 以内）
- 即使你有看法，绝对值不能超过 0.30（硬约束，超出会被裁剪）
- confidence 反映你对该调整的把握度

输出必须是合法 JSON，不要包含 markdown 围栏或多余文字。"""


class LLMAdjuster:
    """OpenAI 兼容的 LLM 调整器。"""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "gpt-5.5",
        base_url: str = "https://aihubmix.com/v1",
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> LLMAdjuster:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def adjust(
        self,
        *,
        question: str,
        p_quant: float,
        spot_price: float,
        resolve_at: datetime,
        now: datetime | None = None,
    ) -> LLMAdjustment | None:
        """调 LLM，失败时返 None。"""
        if not self._api_key:
            logger.info("llm.no_api_key")
            return None

        now = now or datetime.now(timezone.utc)
        days_left = max(0.0, (resolve_at - now).total_seconds() / 86400)
        user_prompt = (
            f"市场问题：{question}\n"
            f"量化模型 P(YES)：{p_quant:.4f}\n"
            f"当前 BTC 现货价：${spot_price:,.2f}\n"
            f"距结算剩余天数：{days_left:.1f} 天\n"
            f"\n请给出 JSON 格式的调整。"
        )

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = await self._client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("llm.http_failed", error=str(e), model=self._model)
            return None

        try:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = _safe_parse_json(content)
            if not parsed:
                logger.warning("llm.parse_failed", raw=content[:200])
                return None
            # clip 到边界
            adj_raw = float(parsed.get("adjustment", 0))
            adjustment = max(-0.30, min(0.30, adj_raw))
            confidence = parsed.get("confidence", "low")
            if confidence not in ("low", "medium", "high"):
                confidence = "low"
            rationale = str(parsed.get("rationale", "")).strip() or "(LLM 未给出解释)"
            return LLMAdjustment(
                adjustment=adjustment,
                confidence=confidence,
                rationale=rationale,
                raw_response=data,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning("llm.malformed_response", error=str(e))
            return None


def _safe_parse_json(text: str) -> dict[str, Any] | None:
    """尽力解析 JSON：先直解，再去掉 markdown ``` 围栏后重试。"""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 去掉 ```json ... ``` 围栏
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            return None
    # 找最外层 {...}
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None
