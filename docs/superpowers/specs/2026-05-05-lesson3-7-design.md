# Lesson 3-7 课程设计 / Spec

**日期**：2026-05-05
**作者**：locey + Claude (brainstorming session)
**适用范围**：lesson3 / lesson4 / lesson5 / lesson6 / lesson7

---

## 1. 总体目标

围绕同一个项目（lesson1 引入的 `btc_kline.py`），五节课各加一项能力，最终把它演进为**一个学员可继续扩展为 BTC 量化交易的本地骨架**。

**最终形态**（L7 结束时）：

```
project/
├── btc_kline.py             # L1: 数据获取 + K 线绘图
├── prices.db                # L1 作业产物：SQLite 历史价格
├── strategies/
│   ├── __init__.py
│   └── dual_ma.py           # L5: 双均线策略（OpenSpec 驱动）
├── backtest.py              # L4: 策略回测核心
├── reports/
│   └── multi_period.md      # L6: 多周期回测报告
├── tests/
│   └── test_*.py            # L7: 测试
├── bin/
│   └── verify.sh            # L7: 一键验收
├── .mcp.json                # L3: SQLite MCP 接入配置
├── .claude/
│   └── skills/
│       └── backtest/        # L4: 策略回测 Skill
├── openspec/                # L5: OpenSpec 工件
│   └── changes/
└── .github/workflows/
    └── verify.yml           # L7: GitHub Actions
```

学员之后想接真实交易所，只需在 `strategies/` 旁边加一个 `broker/` 目录写 30 行下单代码 —— 课程不教这一步，但骨架已经为它留好位置。

---

## 2. 主线项目演进表

| 课 | 时长 | 主题 | 加给项目的能力 | 主要产物 |
|---|---|---|---|---|
| L3 | 20-25 min | MCP 与外部能力接入 | SQLite MCP，AI 直接 SQL 查 `prices.db` | `.mcp.json` + 课堂会话记录 |
| L4 | 20-25 min | Skill 设计与能力沉淀 | `backtest` Skill（输入策略函数 + 时间窗 → 夏普 / 回撤 / 胜率 / 曲线 / 文字总结）+ Skill 市场速览 | `.claude/skills/backtest/SKILL.md` + 一次完整调用 |
| L5 | 25-30 min | OpenSpec 完整流程 | "双均线策略" feature，按 proposal → specs → design → tasks → implement 走一遍 | `openspec/changes/<id>/*.md` + `strategies/dual_ma.py` |
| L6 | 20-25 min | Harness（Superpowers） | 用 superpowers 的 `writing-plans` + `executing-plans` 跑"多周期 / 多币种回测评估"长任务 | `plans/multi-period-backtest.md` + 跨 `/clear` 续接记录 + `reports/multi_period.md` |
| L7 | 20-25 min | 验收集成 | `bin/verify.sh`（ruff + pytest + review skill）+ `.github/workflows/verify.yml` 推到 GitHub Actions | 验收脚本 + workflow + 一次完整执行报告 |

注：L5 因走 OpenSpec 完整五段，预算放宽到 25-30 min；用户对 OpenSpec 熟悉，节奏可以紧。

---

## 3. 每课统一结构

每节课产物完全对齐 lesson1/lesson2 的现有结构：

```
lessonN/
├── README.md                # 学员讲义（step-by-step followable，遵循 CLAUDE.md 第 3 条）
├── 讲稿.md                  # 讲师可念的口播稿
├── lessonN.pdf              # 课件 PDF（约 25 页）
├── lessonN.pptx             # 课件 PPTX（同上）
├── demo/                    # 现场演示用（prompts/ 配置文件 / 样例代码）
└── homework/                # 作业（30 分钟内可完成，不要求写大段新代码）
```

**配色与视觉**（PPTX）：
- 与 lesson2 区分：每节课用一个独有色板
  - L3: `Forest & Moss`（forest #2C5F2D + moss #97BC62 + cream #F5F5F5）
  - L4: `Coral Energy`（coral #F96167 + gold #F9E795 + navy #2F3C7E）
  - L5: `Ocean Gradient`（deep blue #065A82 + teal #1C7293 + midnight #21295C）
  - L6: `Berry & Cream`（berry #6D2E46 + dusty rose #A26769 + cream #ECE2D0）
  - L7: `Cherry Bold`（cherry #990011 + off-white #FCF6F5 + navy #2F3C7E）
- 视觉母题：左侧粗强调条 + 右上章节徽章（沿用 lesson2 模式）
- 页数：每节 22-28 页

**语言与约定**（沿用 CLAUDE.md）：
- 所有时间处理 UTC
- 代码注释 / docstring 中文
- 学员文档 step-by-step followable
- README 包含：前置 / 编号原子步骤 / 期望输出 / 清理回滚 / 常见错误

---

## 4. 每节课详细设计

### 4.1 Lesson 3 — MCP 与外部能力接入

**学习目标**：
1. 理解 MCP 的三类原语：Tools / Resources / Prompts
2. 当堂跑通一个 MCP server（SQLite）
3. 让 AI 通过 MCP 查 BTC 历史价格，产出一段分析

**前置依赖**：
- 已有 `prices.db`（lesson1 作业产物 `lesson1/homework/claude-homework/crypto_prices.db` 可直接复用，或现场用 lesson1 demo 数据生成）

**核心组件**：
- MCP server: `mcp-server-sqlite`（官方 Python 参考实现，`uvx mcp-server-sqlite --db-path prices.db`）
- 配置入口：`lesson3/project/.mcp.json`

**README 章节**：
1. MCP 是什么 / 三原语速览
2. 动手做（5 分钟）：装 mcp-server-sqlite + 配 .mcp.json + Claude 启动验证
3. 动手做（5 分钟）：让 AI 通过 MCP 查"BTC 过去 30 天最高/最低/均价"
4. 关键认知：MCP 给 AI 的是"能力的接口"，不是"工具的实现"
5. 权限与安全边界：read-only vs read-write
6. 反模式（3 条）
7. 作业

**作业（30 分钟内）**：为 prices.db 之外再接一个 MCP（filesystem 或 GitHub 任选），让 AI 完成"读取一份 README，结合 SQLite 数据写一段对比报告"。提交：`.mcp.json` + 会话记录 + 200 字感受。

---

### 4.2 Lesson 4 — Skill 设计与能力沉淀

**学习目标**：
1. 理解 Skill 与 Prompt / Rule / Subagent 的边界
2. 当堂写一个 `backtest` Skill 并调用一次
3. 知道 Skill 生态有哪些来源

**核心组件**：
- 自建 Skill: `lesson4/project/.claude/skills/backtest/SKILL.md`
  - 输入：策略函数（Python，签名 `def strategy(df: DataFrame) -> Series` 输出 +1/0/-1 信号）+ 时间窗
  - 输出：夏普比 / 最大回撤 / 胜率 / 累计收益曲线（PNG）+ 文字总结
  - 实现：调用 `lesson4/project/backtest.py` 作为底层

**Skill 市场速览（讲义里 1 张幻灯片 + README 一段）**：
- Anthropic 官方：https://github.com/anthropics/skills
- skill.sh（社区聚合）
- skillsmp（社区聚合）
- Superpowers（lesson 2 已装）的 skills
- Everything Claude Code (ECC) 的 skills

**README 章节**：
1. Skill 是什么 / 与 Prompt / Rule / Subagent 区别
2. Skill 市场生态速览
3. Skill 的结构：frontmatter + 触发条件 + 步骤 + 示例
4. 动手做（10 分钟）：写 backtest skill 的 SKILL.md + 底层 Python
5. 动手做（5 分钟）：用 skill 跑一次完整回测
6. 反模式（3 条）
7. 作业

**作业（30 分钟内）**：
- 必做：从你日常工作里找一个高频任务，设计成 SKILL.md（不要求实现），提交 SKILL.md + 一次模拟调用脚本
- 加分：实际实现 + 跑一次

---

### 4.3 Lesson 5 — 规则体系与 Spec 驱动开发（OpenSpec 完整流程）

**学习目标**：
1. 理解 vibe coding → spec-driven 的区别
2. 当堂跑完 OpenSpec 五段：proposal → specs → design → tasks → implement
3. 学会 rules / guidelines / spec 三者的配合

**核心组件**：
- OpenSpec CLI（前置安装）
- 待新增的 feature：双均线策略
  - 短均线、长均线、买入/卖出条件、参数范围
  - 写入 `lesson5/project/strategies/dual_ma.py`
- 至少 2 条 rules（参数命名 / UTC 约定 / 必须有回测结果）

**README 章节**：
1. 为什么不能直接让 AI 写代码（vibe vs spec）
2. rules / guidelines / spec 的差异
3. OpenSpec 五段式概览
4. 动手做（4-5 分钟一段）：每段一个动手小节
   - proposal: 1 段话写"我要加什么、为什么"
   - specs: 写期望行为
   - design: 技术方案 + 决策记录
   - tasks: 拆解成可执行清单
   - implement: 让 AI 基于上面四段产出代码
5. 关键认知：spec 是"AI 和你之间的合同"
6. 反模式（3 条）
7. 作业

**作业（30 分钟内）**：为你的项目挑一个新 feature，按 OpenSpec 五段全跑一次，提交 `openspec/changes/<id>/` 全套 + AI 生成的代码 + 一段反思（哪段最好用、哪段最累赘）。

---

### 4.4 Lesson 6 — Harness 设计（Superpowers 风格）

**学习目标**：
1. 理解 harness 解决什么 —— 跨上下文、跨时间持续推进
2. 用 superpowers 的 `writing-plans` + `executing-plans` 跑一个长任务
3. 看到一次"任务跑了一半 → /clear → 续上"

**核心组件**：
- superpowers 的 skills（lesson 2 已装）
- 长任务：在多个时间粒度（1d / 1h / 5m）和多个币种（BTC / ETH）上跑双均线策略 → 产出一份评估报告 `reports/multi_period.md`
- harness 三件套：
  - `plans/multi-period-backtest.md`（writing-plans 产出）
  - 任务状态在 plan 里维护（superpowers 的约定）
  - checkpoint：每个粒度跑完都记一次

**README 章节**：
1. Harness 是什么 / 为什么 AI 干 20 分钟会变笨
2. Harness 四要素：初始化 / 执行 / 检查点 / 上下文交接
3. 动手做（6 分钟）：用 `writing-plans` skill 把任务写成 plan
4. 动手做（10 分钟）：用 `executing-plans` skill 跑前 2 个粒度 → /clear → 续后 2 个
5. 关键认知：plan 文件是 AI 的"外脑"
6. 反模式（3 条）
7. 作业

**作业（30 分钟内）**：选一个你日常需要分阶段做的任务，写一份最小 plan（writing-plans 风格即可），跑至少一次 /clear 续接。提交 plan 文件 + 续接前后两段对话。

---

### 4.5 Lesson 7 — Agent 工作流与验收集成

**学习目标**：
1. 理解 AI 工作流的闭环：规划 → 执行 → 检查 → 修正
2. 当堂搭一套三节点的本地验收（lint / test / review skill）
3. 把同样的验收推到 GitHub Actions

**核心组件**：
- 本地：`lesson7/project/bin/verify.sh`
  - `ruff check .`（继承 lesson1 的 lint 约定）
  - `pytest tests/`（lesson 7 同时演示补几个最小测试）
  - 调一次 review skill 对最近 diff 给意见 —— 用 `superpowers:requesting-code-review`（lesson 2 装的 superpowers 自带）
- CI：`lesson7/project/.github/workflows/verify.yml`
  - 推到 GitHub 时自动跑 ruff + pytest（review skill 因为依赖 Claude Code，CI 里跳过）

**README 章节**：
1. 验收的意义：correctness signal 让 AI 闭环
2. 三节点：lint / test / review skill
3. 动手做（4 分钟）：写 bin/verify.sh
4. 动手做（4 分钟）：写 .github/workflows/verify.yml
5. 动手做（6 分钟）：故意改一段坏代码 → 跑 verify.sh → 看见报错 → AI 自修 → 通过
6. 关键认知：本地 + CI 双跑，AI 改的代码两道关
7. 反模式（3 条）
8. 作业

**作业（30 分钟内）**：为你自己的项目设计一套验收（至少 3 个节点），可以是 shell + Actions / hooks 任选，跑一次 AI 提交并记录每节点通过/失败 + 修复过程。

---

## 5. 项目目录与课程目录的关系

> **Refactor Note (2026-05-05):** 原设计（见下"原始方案"）将 `project/` 放在仓库根（L3-L7 五课共享）。实施后重构为**每节课有独立 `lessonN/project/` 快照**，各节课完全独立，学员可以从任意一课开始练习。`specs/` 和文档已更新为 `lesson3/project/`、`lesson4/project/`、`lesson5/project/` 等路径。

### 当前方案（重构后）：每节课独立 `lessonN/project/` 快照

```
ai_lesson/
├── lesson1/                 # 已存在：独立 demo
├── lesson2/                 # 已存在：用 lesson1/demo 作素材
├── lesson3/
│   └── project/             # lesson3 独立快照：SQLite MCP 接入
├── lesson4/
│   └── project/             # lesson4 独立快照：backtest Skill
├── lesson5/
│   └── project/             # lesson5 独立快照：OpenSpec + dual_ma
├── lesson6/                 # 规划中
└── lesson7/                 # 规划中
```

- 每个 `lessonN/project/` 包含该课所需的完整文件集
- 课与课之间的增量（如 L4 在 L3 基础上加 backtest）通过快照方式携带，而不是共享
- 学员只需进入 `lessonN/project/` 即可开始对应课的练习，不依赖其他课产物

### 原始方案（已废弃，保留历史记录）

原设计将 `project/` 放在仓库根（L3-L7 共享）：

```
ai_lesson/
└── project/                 # 共享主项目（原设计，已改为 lessonN/project/）
    ├── btc_kline.py         # L3 之前从 lesson1/demo 复制
    ├── prices.db
    └── ...
```

**初始化**：lesson3 的开篇步骤包含一次性的"把 lesson1 demo 的 btc_kline.py + prices.db 复制到 lesson3/project/"。

---

## 6. 学员前置依赖

学员开始 lesson3 前已确认：
- Claude Code + Cursor 已装（L1）
- 仓库已 clone（L1）
- python 3.11+ + pip + uv（uv 用于跑 mcp-server-sqlite）
- L1 作业的 `prices.db` 已生成（如未生成，L3 开篇有 fallback：用 BTC 历史 K 线生成一份等价 SQLite）
- Superpowers 插件已装（L2 装过）
- 浏览器能访问 github.com（L7 推 CI 用）

每节课 README 开头一段"前置确认"，列出当节会用到的依赖。

---

## 7. 不在范围内（YAGNI）

明确**不做**的事：
- 不接真实交易所 API（不是 paper trading 也不是真实下单）
- 不做高级回测：手续费、滑点、流动性建模等
- 不引入 Docker / Kubernetes / 数据库迁移
- 不做前端 / Web UI
- 不教 MCP server 开发（只教消费现成 server）
- 不教 plugin 开发（lesson 2 已介绍消费）
- 不深入金融工程理论（夏普 / 回撤是公式套用，不展开数学推导）
- 不引入实时行情 WebSocket
- 不引入 multi-agent 协作（这是 L8-L10 的内容）

---

## 8. 风险与未决事项

**已知风险**：
- L5 OpenSpec 完整流程在 25-30 min 内压缩到极限。若实操超时，容许讲师在课中切到"讲完概念 + 课后跟做"。
- L6 Superpowers 的 `executing-plans` 可能在某些状态下行为不稳定。准备一份 manual-handoff fallback（即使 superpowers 接管失败也能用 PROJECT.md / TASKS.md 自救）。
- GitHub Actions 在内网/受限网络环境可能拉镜像慢。L7 准备一段"如果 CI 跑不通，本地 verify.sh 拍照证明完成"的 fallback。

**未决事项**：无。所有关键决定已闭环（Q1-Q7）。

---

## 9. 决策记录（Q1-Q7 速查）

| # | 问题 | 决定 |
|---|---|---|
| Q1 | 五课实操是否串成一个项目？ | A：是，连续主线 |
| 扩展 | 主线方向？ | 演进为 BTC 量化雏形（学员可继续扩展为真实量化） |
| Q2 | L7 终态？ | a：本地信号脚本 + 简单回测，零交易所 API |
| Q3 | L3 MCP 用什么？ | a：SQLite MCP（mcp-server-sqlite） |
| Q4 | L4 把什么做成 Skill？ | a：策略回测 Skill；同时介绍 Skill 市场（skill.sh / skillsmp / 官方 / superpowers / ECC） |
| Q5 | L5 spec 走多深？ | b：OpenSpec 完整五段流程 |
| Q6 | L6 Harness 形态？ | b：Superpowers 风格，用 writing-plans + executing-plans 演示 |
| Q7 | L7 验收管线？ | a+b：本地 bin/verify.sh + GitHub Actions workflow，不引入 hook |

---

## 10. 下一步

1. 用户审阅本 spec
2. 通过后调用 `superpowers:writing-plans` 生成实施计划（按"先 L3 写完 README + 讲稿 + demo + 作业 + pptx + pdf，再 L4..."的顺序）
3. 按 plan 实施，每完成一节课就提交一个 commit
