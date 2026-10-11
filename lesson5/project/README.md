# lesson5/project/

**Lesson 5 的项目快照** —— 学完 lesson 5 后 `project/` 应当长这样。

在 lesson4/project/ 基础上新增：

| 文件 / 目录 | 用途 |
|---|---|
| `openspec/specs/` | 项目当前规范的 source of truth |
| `openspec/changes/add-dual-ma-strategy/` | lesson 5 走完的 OpenSpec 5 段示例 |
| `strategies/dual_ma.py` | lesson 5 实施产物：双均线策略 |
| `strategies/rsi_reversal.py` | 同上扩展：RSI 反转（long-only，反转家族示例） |
| `strategies/__init__.py` | 包入口 |
| `web/` | 本地 Flask 可视化 dashboard —— 详见 [`web/README.md`](web/README.md) |

`seed_db.py` 的 LIMIT 在本课经历两次扩窗：30 → 90（让 dual_ma 在双层 shift(1) 防 lookahead 下能触发金叉）→ 365（让 rsi_reversal 也能遇上真正的 oversold 反弹事件 —— 90 天窗口里 BTC 最低 RSI 只到 42，从未进入 30 以下）。

学完 lesson 5，跑过 `python seed_db.py` 后，本目录还会多出 `prices.db`（365 行 BTCUSDT + 365 行 ETHUSDT）+ `cum_BTCUSDT.png`（gitignored）。

## 与其他课的关系

每节课有自己的 `project/` 快照，互不干扰：

| 课 | 路径 | 在前一节基础上加什么 |
|---|---|---|
| L3 | `lesson3/project/` | 起点 |
| L4 | `lesson4/project/` | + `backtest.py` + `.claude/skills/backtest/` |
| L5 | `lesson5/project/` | + `openspec/` + `strategies/` + seed_db LIMIT 30→90 |
| L6 | `lesson6/project/` | + `plans/` + `reports/` |
| L7 | `lesson7/project/` | + `tests/` + `bin/verify.sh` + `.github/workflows/` |
