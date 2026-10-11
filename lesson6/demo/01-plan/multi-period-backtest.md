# Multi-Period Backtest — Plan

**Goal:** 在 6 个场景上跑 dual_ma 策略回测，聚合成一份 `reports/multi_period.md`，回答"双均线策略在不同时间窗口、不同币种上是否表现稳定？"

**Architecture:** 用 lesson 4 的 `backtest.run_backtest(dual_ma, symbol, limit=N)` 为每个 scenario 跑一次，把 sharpe / max_dd / win_rate / cumulative_return 四个指标记到 plan 文件里。最后用一段 Python 把 6 行结果整理成 markdown 表 + 一段定性分析。

**Tech Stack:** Python 3.11 / pandas / `lesson6/project/strategies/dual_ma.py` / `lesson6/project/backtest.py`

---

## Scenarios

| # | symbol | limit | sharpe | max_dd | win_rate | cum_return | status |
|---|---|---|---|---|---|---|---|
| 1 | BTCUSDT | 30  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | [x] |
| 2 | BTCUSDT | 60  | 2.6388 | -0.0424 | 0.6538 | 0.1237 | [x] |
| 3 | BTCUSDT | 90  | 1.1563 | -0.0938 | 0.5870 | 0.0911 | [x] |
| 4 | ETHUSDT | 30  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | [x] |
| 5 | ETHUSDT | 60  | 1.5682 | -0.0644 | 0.5789 | 0.1008 | [x] |
| 6 | ETHUSDT | 90  | 1.6456 | -0.1271 | 0.5750 | 0.2019 | [x] |

每个 scenario 完成后回填表里 4 个数字 + 把 `[ ]` 改成 `[x]`。

---

## Tasks

### Task 1: 跑 BTCUSDT × {30, 60, 90} (Phase 1)

- [x] **Step 1.1**: cd 到 `lesson6/project/`
- [x] **Step 1.2**: 跑 scenario 1（BTCUSDT, limit=30）：

  ```bash
  python -c "from strategies import dual_ma; from backtest import run_backtest; r = run_backtest(dual_ma, symbol='BTCUSDT', limit=30); print(f\"sharpe={r['sharpe']:.4f}  max_dd={r['max_drawdown']:.4f}  win_rate={r['win_rate']:.4f}  cum={r['cumulative_return']:.4f}\")"
  ```
  把 4 个数字记到 Scenarios 表行 1，状态改 `[x]`。

- [x] **Step 1.3**: 跑 scenario 2（BTCUSDT, limit=60）—— 同上，limit 换 60。
- [x] **Step 1.4**: 跑 scenario 3（BTCUSDT, limit=90）—— 同上，limit 换 90。

完成 Step 1.4 后**写 HANDOFF.md**（见 Task 2）后停下，等下一阶段续。

### Task 2: 写 HANDOFF.md（阶段 1 结束）

- [x] **Step 2.1**: 在 `lesson6/project/plans/HANDOFF.md` 里记下：
  - 当前进度：Scenarios 1-3 完成，4-6 待跑
  - 已记录的数字（粘贴 4 列）
  - 下一阶段第一句要做什么："续完 scenarios 4-6（ETHUSDT × {30,60,90}），然后写 reports/multi_period.md"
  - 一行用 prompt（**给阶段 2 的人粘贴用**）："请读 lesson6/project/plans/multi-period-backtest.md，从下一个未完成的 scenario 续上。"

### Task 3: 跑 ETHUSDT × {30, 60, 90} (Phase 2，新会话)

> **新会话从这里开始**。第一句粘贴 HANDOFF 里的引用 prompt。

- [x] **Step 3.1**: 读 plan + HANDOFF
- [x] **Step 3.2**: 跑 scenario 4（ETHUSDT, limit=30）
- [x] **Step 3.3**: 跑 scenario 5（ETHUSDT, limit=60）
- [x] **Step 3.4**: 跑 scenario 6（ETHUSDT, limit=90）

每跑完一个回填表 + 状态打勾。

### Task 4: 聚合 → reports/multi_period.md

- [x] **Step 4.1**: 读 plan 表里 6 行数字，写 `reports/multi_period.md`：
  - 一段 100 字的 executive summary
  - 完整 markdown 表（symbol × limit × 4 指标）
  - 3 句话定性分析（哪个 scenario 表现最好？时间窗口越长越稳吗？BTC vs ETH 哪个更适合 dual_ma？）
- [x] **Step 4.2**: 把 plan 里 Tasks 部分**全部打勾**

---

## Resume Protocol

**任何时候（包括跨 /clear）想续上：**
1. 读这份 plan
2. 找 Scenarios 表里第一个 `[ ]` 行
3. 从对应的 Step 续跑

只要 plan 里数据准确（每完成一步就回填+打勾），即使换了 AI 实例 / 换了人 / 隔了一周，也能无缝续上。这就是 harness。
