# 演示：Harness 三件套

本目录是 lesson 6 课堂演示的三个产物的副本——和 `lesson6/project/plans/` + `lesson6/project/reports/` 完全同步，方便学员在不进入 project 目录的情况下直接 `cat` 出来看。

| 文件 | 阶段 | 用途 |
|---|---|---|
| `01-plan/multi-period-backtest.md` | 起点 | Plan 文件，列出 6 个 scenarios + 任务拆解 + Resume Protocol |
| `02-handoff/HANDOFF.md` | 阶段切换 | 阶段 1 → 阶段 2 的交接快照（含 Next prompt） |
| `03-report/multi_period.md` | 终点 | 6 scenarios 聚合的最终报告 |

学员在课堂上跟着这三份文件复刻一遍流程，体会"plan 是 AI 的外脑"。

## 怎么用

```bash
cat lesson6/demo/01-plan/multi-period-backtest.md   # 看任务怎么拆
cat lesson6/demo/02-handoff/HANDOFF.md              # 看 Phase 1 → Phase 2 的交接长什么样
cat lesson6/demo/03-report/multi_period.md          # 看最终聚合报告长什么样
```

三个文件按时序排列：先看 01-plan 理解"任务起点"，再看 02-handoff 理解"会话切换"，最后看 03-report 理解"任务终点"。

## 与 project/ 的关系

这是**副本**——真实的 harness 产物长在 `lesson6/project/plans/` 和 `lesson6/project/reports/` 下。本目录的存在只是为了让学员不用 `cd` 进 project 也能看到样本。如果你跟着 README 真跑了一遍流程，**修改的是 project/ 下的文件**，本目录的副本不会自动更新——但下次课堂讲解时会用 project/ 下的最新版重新生成 demo。
