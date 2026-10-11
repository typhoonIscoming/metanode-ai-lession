"""飞书 webhook 推送：交互式卡片 + dry-run（webhook 未配时打印到日志）。"""

from __future__ import annotations

from typing import Any

import httpx

from btc_arb.logging import get_logger

logger = get_logger(__name__)


KIND_HEADER = {
    "ENTRY_LONG": ("🟢 入场信号 · 做多 YES", "green"),
    "ENTRY_SHORT": ("🔴 入场信号 · 做空 YES（=做多 NO）", "red"),
    "EXIT_LONG": ("⚪ 退出信号 · 平多 YES", "grey"),
    "EXIT_SHORT": ("⚪ 退出信号 · 平空 YES", "grey"),
    "EXPIRED": ("⚫ 市场结算 / 已过期", "carmine"),
}


class FeishuClient:
    """飞书自定义机器人 webhook 客户端。"""

    def __init__(self, webhook_url: str | None, timeout: float = 10.0) -> None:
        # 允许 webhook_url 为 None，此时进入 dry-run 模式（不发请求，只打 log）
        self._url = webhook_url
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> FeishuClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def push_card(self, payload: dict[str, Any]) -> dict[str, Any]:
        """发送 interactive card；返回飞书原始响应。dry-run 时返回 {"dry_run": True}。"""
        if not self._url:
            logger.info("feishu.dry_run", payload_preview=str(payload)[:300])
            return {"dry_run": True}
        try:
            resp = await self._client.post(self._url, json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("feishu.push_failed", error=str(e))
            raise
        return resp.json()


def render_signal_card(
    *,
    kind: str,
    question: str,
    slug: str,
    p_ai: float,
    p_mkt: float,
    gap: float,
    spot_price: float | None,
    resolve_at_iso: str,
    event_slug: str | None = None,
    is_demo: bool = False,
) -> dict[str, Any]:
    """把一条 SignalEvent 渲染成飞书 interactive card payload。

    URL 优先级：event_slug > slug > polymarket.com
    is_demo: True 时不放按钮，避免推到飞书的"打开市场"链到 404
    """
    title, color = KIND_HEADER.get(kind, ("📣 信号", "blue"))
    if event_slug:
        market_url = f"https://polymarket.com/event/{event_slug}"
    elif slug:
        market_url = f"https://polymarket.com/market/{slug}"
    else:
        market_url = "https://polymarket.com"
    spot_str = f"${spot_price:,.2f}" if spot_price is not None else "n/a"

    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color,
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{question}**",
                    },
                },
                {
                    "tag": "div",
                    "fields": [
                        {"is_short": True, "text": {"tag": "lark_md", "content": f"**AI 概率**\n{p_ai:.1%}"}},
                        {"is_short": True, "text": {"tag": "lark_md", "content": f"**市场价**\n{p_mkt:.1%}"}},
                        {"is_short": True, "text": {"tag": "lark_md", "content": f"**Gap**\n{gap:+.2%}"}},
                        {"is_short": True, "text": {"tag": "lark_md", "content": f"**BTC 现价**\n{spot_str}"}},
                    ],
                },
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": f"结算时间：{resolve_at_iso}"}
                    ],
                },
                *(
                    []
                    if is_demo
                    else [
                        {
                            "tag": "action",
                            "actions": [
                                {
                                    "tag": "button",
                                    "text": {"tag": "plain_text", "content": "打开 Polymarket 市场"},
                                    "type": "primary",
                                    "url": market_url,
                                }
                            ],
                        }
                    ]
                ),
            ],
        },
    }
