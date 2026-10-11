## Why

lesson 5 已落地 `dual_ma`（趋势跟踪），策略库里缺少 **反转 / 均值回归** 类样本。RSI 是业内最普及的反转指标，加入 `rsi_reversal` 后，学员可以在同一回测引擎上对比"顺势"与"反势"两类逻辑，为 lesson 6-7 的对比研究和 plan / report 演示提供素材。

## What Changes

- 新增策略函数 `rsi_reversal(df, period=14, oversold=30, overbought=70)`：RSI 自下方上穿 `oversold` 时进多（信号 `+1`），RSI 自上方下穿 `overbought` 时离场（信号 `0`），其他时刻持仓维持
- 在 `project/strategies/__init__.py` 顶层导出 `rsi_reversal`
- 在 `openspec/specs/strategies.md` 的"已实现策略"表新增 `rsi_reversal` 行
- 不引入新第三方依赖（仅用现有 pandas + numpy）
- 不修改 `backtest.py` —— `rsi_reversal` 满足现有 callable 契约即可被 `run_backtest()` 直接消费
- **非破坏性**：`dual_ma` 行为、文件位置、接口均保持不变

## Capabilities

### New Capabilities

<!-- 无；不引入新能力 -->

### Modified Capabilities

- `strategies`: 现有策略目录新增一个反转类策略 `rsi_reversal`；目录的通用约定（callable 签名、值域 {-1,0,+1}、防 lookahead、可被 `run_backtest` 直接调用）保持不变

## Impact

- **新增文件**: `project/strategies/rsi_reversal.py`（约 50-70 行）
- **修改文件**:
  - `project/strategies/__init__.py`（追加导出）
  - `project/openspec/specs/strategies.md`（变更归档时合并 specs/ 增量）
- **不影响**: `backtest.py`、`seed_db.py`、`dual_ma.py`、prices.db schema
- **数据要求**: 至少需要 `period + 1` 根 K 线 RSI 才能成立；默认 `period=14`，当前 `seed_db.py LIMIT=90` 远超阈值
- **教学影响**: 学员将获得一对"趋势 vs 反转"的对照样本，便于在 lesson 6 plan / lesson 7 测试中作横向对比
