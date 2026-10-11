# Implementation Note: add-rsi-strategy

## 实施日期

2026-05-13T19:44:45Z

## 实施产物

- `project/strategies/rsi_reversal.py`（75 行，含 `__main__` 自测块）
- `project/strategies/__init__.py`（追加 `rsi_reversal` 的导入与 `__all__` 条目）
- `project/openspec/specs/strategies.md`（"已实现"表追加一行；"通用约定"追加 §5 关于 `_long_short` 命名后缀的约定）

## 自测结果（90 日 BTCUSDT 1d K 线，default 参数）

```
sharpe=0.0000
max_drawdown=0.0000
win_rate=0.0000
cumulative_return=0.0000
rows=90
```

中文 summary：

> BTCUSDT 在最近 90 根 K 线上的回测结果：累计上涨 0.00%，年化夏普 0.00，最大回撤 0.00%，信号触发日胜率 0.00%。

**全 0 是意料之中**。RSI 在该窗口里的真实分布：

| 指标 | 数值 |
|---|---|
| 有效 RSI 数 | 87（前 3 根为 NaN / burn-in） |
| RSI 值域 | 42.13 ~ 92.75 |
| RSI < 30 出现次数 | **0** |
| RSI > 70 出现次数 | 9 |

整段窗口 BTC 在 64,058 ~ 82,210 USDT 区间单边偏强，RSI 最低 42 始终未触达 30；既然从未进入超卖，自下穿越事件就不存在 → 策略全程空仓。ETH 同窗口 RSI 最低 44，结果一致。

为验证实现本身正确，单独构造了一段"先跌后涨再跌"的合成价格序列（80 根，三段），观察到了清晰的两次切换：

| 事件 | 触发位置 | RSI 值 |
|---|---|---|
| 0 → 1（超卖反弹进多） | bar 30 | 31.37 |
| 1 → 0（超买回落离场） | bar 62 | 69.68 |

值域断言 `set(sig.unique()).issubset({0, 1})` 在真实数据和合成数据上均通过；`len(df)=5, period=14` 的边界用例返回全 0 整数 Series，无异常。

## 与 design.md 的偏差

无。RSI 公式、穿越判定、`ffill` 维持、long-only 二态、整数 dtype、起始期全 0 均按 design.md 落地。

## 反思

> 教学样本里反转策略可能跑不过 buy_and_hold —— 这是预期的：**单边行情就是反转策略的失效模式**。

本次回测 BTC 累计 +28.4%（窗口内 64k → 82k），buy_and_hold 直接拿满；rsi_reversal 全程空仓收益 0% —— 差距 28 个百分点不是 bug，是 RSI 反转**在持续上涨中无法找到入场点**这一本质特征的真实呈现。

教学意义反而被强化：

1. **策略 vs 行情匹配** —— 学员将直观看到，"明明逻辑没问题、代码没 bug，但收益就是 0" 来自策略与行情风格的错配
2. **lesson 6-7 plan/report 的天然素材** —— "把 RSI 反转的 period 从 14 降到 7、把 oversold 从 30 升到 40 试一试"，是非常自然的策略调参 plan
3. **横向对照** —— 与 `dual_ma` 在同一窗口的 +9.11%（Sharpe 1.16）相比，趋势跟踪在单边市场里完胜反转，这一组数对（顺势赢 / 反势平）将贯穿后续课程

## 后续

- 不在此变更内手工合并 `specs/strategies/spec.md` 增量进 `openspec/specs/strategies.md` —— 留给 `/opsx:archive` 阶段，以保持流程清晰
- 不调整 `seed_db.py` `LIMIT` —— 90 行已能让策略起步；若教学时需要演示触发场景，建议临时把 `LIMIT` 提到 180+ 或用 `-i 1h` 拉时间窗
