# lesson4/project/

**Lesson 4 的项目快照** —— 学完 lesson 4 后 `project/` 应当长这样。

在 lesson3/project/ 基础上新增：

| 文件 | 用途 |
|---|---|
| `backtest.py` | lesson 4 核心：pandas 实现的最小回测引擎 |
| `.claude/skills/backtest/SKILL.md` | lesson 4：backtest skill 定义 |
| `.claude/skills/backtest/example_strategies.py` | lesson 4：buy_and_hold + ma_crossover_7 起手模板 |

学完 lesson 4，跑过 `python seed_db.py` + 用过 backtest skill 之后，本目录还会多出 `prices.db` + `cum_BTCUSDT.png`（gitignored）。

## 与其他课的关系

每节课有自己的 `project/` 快照，互不干扰：

| 课 | 路径 | 在前一节基础上加什么 |
|---|---|---|
| L3 | `lesson3/project/` | 起点 |
| L4 | `lesson4/project/` | + `backtest.py` + `.claude/skills/backtest/` |
| L5 | `lesson5/project/` | + `openspec/` + `strategies/` |
| L6 | `lesson6/project/` | + `plans/` + `reports/` |
| L7 | `lesson7/project/` | + `tests/` + `bin/verify.sh` + `.github/workflows/` |
