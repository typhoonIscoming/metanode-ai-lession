"""量化预测：对数正态模型算 P(BTC > strike at T) 或 P(BTC < strike at T)。

模型假设：log(S_T / S_0) ~ N(0, σ² · τ)（无漂移，简化版 Black-Scholes 中性世界）
- S_0：当前现货
- σ：年化已实现波动率
- τ：到结算的剩余年化时间
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

# scipy 提供更精确的标准正态 CDF；没有就退化到 erf
try:
    from scipy.stats import norm  # type: ignore[import-untyped]

    def _phi(x: float) -> float:
        return float(norm.cdf(x))
except ImportError:  # pragma: no cover
    def _phi(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def quant_probability(
    *,
    spot_price: float,
    strike_price: float,
    direction: str,
    resolve_at: datetime,
    realized_vol: float,
    now: datetime | None = None,
) -> float:
    """返回 P(market YES) 的纯量化估计，clip 到 [0.001, 0.999]。

    direction:
      - "above" → P(S_T > strike)
      - "below" → P(S_T < strike)

    边界：
      - 距结算 ≤ 1 分钟：直接按当前 spot 是否已过 strike 给 0.001/0.999
      - σ ≤ 0 或 τ ≤ 0：上一条退化路径
    """
    if direction not in ("above", "below"):
        raise ValueError(f"unknown direction: {direction!r}")
    now = now or datetime.now(timezone.utc)
    tau_seconds = (resolve_at - now).total_seconds()

    # 退化：临近结算或非法波动率，按当前 spot 与 strike 的关系直接给极值
    if tau_seconds <= 60 or realized_vol <= 0:
        is_above = spot_price > strike_price
        if direction == "above":
            return 0.999 if is_above else 0.001
        return 0.001 if is_above else 0.999

    tau_years = tau_seconds / (365.0 * 86400.0)
    sigma_sqrt_tau = realized_vol * math.sqrt(tau_years)
    # log(K/S) / (σ√τ)
    d = math.log(strike_price / spot_price) / sigma_sqrt_tau
    # P(S_T > K) = 1 - Φ(d) = Φ(-d)
    p_above = _phi(-d)
    p = p_above if direction == "above" else (1.0 - p_above)
    return max(0.001, min(0.999, p))


MODEL_VERSION = "quant-lognormal-v1"
