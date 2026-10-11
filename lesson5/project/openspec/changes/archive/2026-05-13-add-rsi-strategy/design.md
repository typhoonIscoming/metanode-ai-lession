## Context

`project/strategies/` 当前只有 `dual_ma`（趋势跟踪 / 顺势）。lesson 5-7 的教学线索希望同时展示"反向 / 均值回归"逻辑，方便学员在同一回测引擎上做 A/B 对照。RSI 是行业最广泛使用的反转指标（TradingView / Binance / 各大量化书目均默认提供），把它作为反转家族第一个落地策略，认知门槛低、对外验证容易。

约束：

- 必须复用 `backtest.run_backtest()` 现有契约 —— 即 `def strategy(df) -> Series ∈ {-1,0,+1}`
- 必须不引入新的第三方依赖（保持 lesson 1 安装清单不变）
- 必须符合项目两条硬规约：UTC + 中文注释
- 25 分钟教学场景内可以讲透 → 决策点越少越好，避免与 `dual_ma` 重复同类讨论

## Goals / Non-Goals

**Goals:**

- 提供一个**反转家族**的可回测策略 `rsi_reversal`，行为可解释、参数可调（`period / oversold / overbought`）
- 行为与 `dual_ma` **结构对称**：同样 long-only、同样用 `shift(1)` 防 lookahead、同样依赖 `ffill` 维持持仓 —— 学员对照阅读时认知负担小
- 在 `openspec/specs/strategies.md` 留下可追溯的接口/规则规范，让 lesson 6-7 可以基于它写 plan / report

**Non-Goals:**

- 不做参数自动寻优（学员自行 sweeping）
- 不做做空 / 仓位分级（保持 `{0, +1}` 二态）
- 不做 RSI 之外的反转指标（KDJ、Williams %R、Bollinger 等留给后续 change）
- 不调整 `seed_db.py` / `backtest.py` —— 默认 90 行 K 线已够算 14 周期 RSI

## Decisions

### 1. RSI 平滑方法：Wilder EWMA（`alpha = 1/period`）而非 SMA

| 方案 | 优势 | 劣势 |
|---|---|---|
| **A. Wilder EWMA**（选用） | 行业事实标准；TradingView/Binance 同源；曲线更平滑、信号噪声小 | 起始 burn-in 不可解析（数学定义就是渐近） |
| B. SMA(period) | 实现一行；学员一眼能懂 | 与外部 RSI 数值不匹配，验证时学员可能困惑"为什么和 Binance 不一致" |

公式：

```python
delta = close.shift(1).diff()
gain = delta.clip(lower=0)
loss = (-delta).clip(lower=0)
avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
rs = avg_gain / avg_loss.replace(0, np.nan)
rsi = 100 - 100 / (1 + rs)
```

> 注意 `close.shift(1)` 这一层是**策略层**防 lookahead，与 `run_backtest` 内部 `signal.shift(1)` 共同构成两层防护，与 `dual_ma` 一致。

### 2. 触发条件：**穿越**而非**区间**

| 方案 | 行为 |
|---|---|
| **A. 穿越**（选用） | RSI 自下穿 30 → 进多；自上穿 70 → 离场 |
| B. 区间 | RSI < 30 期间持续做多；RSI > 70 期间持续空仓 |

理由：

- 穿越仅在事件那一根 K 线给信号，搭配 `ffill` 维持仓位，**逻辑形状和 `dual_ma` 的金叉/死叉完全对称** → 学员对照阅读零成本
- 区间方案在 RSI 围绕阈值反复抖动时会产生大量重复信号，引入额外的"去抖"决策点，超出教学预算

### 3. 长仓 only（不做空）

跟 `dual_ma` 保持一致：教学语境下加做空只会让回撤/胜率解读复杂化。学员之后若想做空版本，自然就是下一个 change。

### 4. 起始期 / 数据不足 → 全 0

- `len(df) < period + 1` → 直接 `return pd.Series(0, index=df.index, dtype=int)`
- 数据够但 RSI 在 burn-in 期为 NaN → 该段强制为 0

理由：让函数对小样本"安静失败"而不是抛异常，方便 `run_backtest` 在任何 `limit` 下都跑出 PNG / summary。

### 5. 维持仓位用 `ffill`

```python
sig = pd.Series(np.nan, index=df.index)
sig[cross_up] = 1
sig[cross_dn] = 0
sig = sig.ffill().fillna(0).astype(int)
```

跟 `dual_ma` 同款骨架 —— **可读性优先于性能**。

### 6. 输出 dtype：`int`

回测引擎接受 float，但 `int` 强信号更直观，并可显式排除"信号被乘上 NaN"的尴尬。

## Risks / Trade-offs

- **[Wilder burn-in 段无信号]** → 前 ~`period * 3` 根 K 线 RSI 数值未完全收敛，可能少触发 1 次反弹买入 → 在 design.md / spec.md 标注；学员可通过加大 `seed_db.py LIMIT` 缓解
- **[反转策略在持续单边行情下表现差]** → RSI 长时间高于 70 而不回落时策略空仓错过整段上涨；在 IMPLEMENTATION.md 的回测样本里如实写出 Sharpe / MaxDD，让学员**直观看到反转策略的失效模式**（教学价值）
- **[`avg_loss = 0` 会导致 RS = ∞]** → 在极端单边时分母为 0；用 `replace(0, np.nan)` → RSI = 100，逻辑上正确（强烈超买），不会破坏后续 `ffill`
- **[与外部 RSI 数值轻微差异]** → 不同库的 EWMA `adjust` 参数不同；我们固定 `adjust=False` 即标准 Wilder，与 TradingView 默认一致；在 design.md 显式说明，方便学员对账

## Migration Plan

不涉及在线服务；纯库内新增。回滚策略：删除 `project/strategies/rsi_reversal.py` 并撤回 `__init__.py` 中的一行导出即可。

## Open Questions

- 是否在 `seed_db.py` 同步把 `LIMIT` 调到 ≥ 120 以让 RSI 充分 burn-in？**默认不动** —— 当前 90 根够用，调整属于另一个变更的范围
- 是否同时给 `example_strategies.py` 加一个 RSI 模板？**默认不动** —— `example_strategies.py` 是回测 skill 的 starter 模板，与生产策略目录解耦
