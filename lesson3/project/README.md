# lesson3/project/

**Lesson 3 的项目快照** —— 学完 lesson 3 后 `project/` 应当长这样。

| 文件 | 来源 |
|---|---|
| `btc_kline.py` | 从 lesson 1 demo 复制 |
| `seed_db.py` | lesson 3 加：拉历史 K 线落 SQLite |
| `.mcp.json` | lesson 3 加：mcp-server-sqlite 配置 |
| `.gitignore` | 忽略 prices.db / *.png / __pycache__ |

学完 lesson 3，跑过 `python seed_db.py` 后，本目录还会多出 `prices.db`（gitignored）。

## 与其他课的关系

每节课有自己的 `project/` 快照，互不干扰：

| 课 | 路径 | 在前一节基础上加什么 |
|---|---|---|
| L3 | `lesson3/project/` | 起点（从 lesson1 demo 引入） |
| L4 | `lesson4/project/` | + `backtest.py` + `.claude/skills/backtest/` |
| L5 | `lesson5/project/` | + `openspec/` + `strategies/` |
| L6 | `lesson6/project/` | + `plans/`（Superpowers harness）+ `reports/` |
| L7 | `lesson7/project/` | + `tests/` + `bin/verify.sh` + `.github/workflows/` |

学员可以选任一节课的 `project/` 作为起点，独立跟着课程走，不受其他课影响。
