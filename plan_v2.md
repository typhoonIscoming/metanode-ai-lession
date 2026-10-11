# AI 驱动的软件开发提效实战课

## 课程定位
面向研发人员，聚焦 AI 在真实开发工作流中的提效方法。课程围绕 Claude、Cursor、Codex、Copilot、MCP、Skill、OpenSpec、Harness、Everything Claude Code、Superpowers、Agent Teams 等核心内容展开，强调"工具使用 + 上下文接入 + 能力沉淀 + 工作流自动化 + 项目落地"。

## 课程目标
通过本课程，学员能够：

- 理解 AI 如何进入真实软件开发流程
- 掌握 Claude、Cursor、Codex 等主流开发工具的典型使用方式
- 理解并实践上下文工程、MCP、Skill、规则体系与 Spec 驱动开发
- 理解 Harness 的理念，能够为 AI 搭建可执行、可验证、可持续推进的开发环境
- 了解 OpenSpec、Everything Claude Code、Superpowers 在开发提效中的定位与用法
- 设计可复用的 Agent 工作流与多 Agent 协作方式
- 将所学内容应用到实际项目开发与团队协作中

---

# 课程结构

- **第 1–7 课：核心方法、环境搭建与工作流设计**
- **第 8–10 课：综合项目实战**

---

# 课程主线

**工具使用 → 进阶技巧 → 上下文接入 → 能力沉淀 → Spec 与规则约束 → Harness 搭建 → 工作流自动化 → 项目实战**

---

# 第一部分：核心方法、环境搭建与工作流设计

## 第 1 课：AI 开发提效全景与工具对比
### 内容
- 环境搭建：安装 Claude Code 和 Cursor，验证可用
- 三种模式：聊天式 / IDE 内嵌 / 命令式 Agent，谁适合谁
- 工具速览：Claude Code、Cursor、Codex 对比矩阵 + 社区生态（Everything Claude Code、Superpowers）
- 基础技巧 ×20：Cursor 10 条 + Claude Code 10 条 + 两款通用心法

### 实践
- 现场演示：同一 Prompt 在 Claude Code 与 Cursor 中并排跑（BTC K 线脚本），观察结构、风格与交互轮次的差异

### 作业
分别用 Claude Code 和 Cursor 实现一个加密货币行情监控 CLI（支持实时价格、阈值告警、SQLite 落库、统计查询）。提交两份代码 + 对比报告：交互轮次、代码结构、错误处理、是否补写测试、主观体验评分（1-5），并说明后续会优先使用哪个工具、为什么。

---

## 第 2 课：Claude Code × Cursor 高级技巧
### 内容
- Subagents 并行作业：隔离上下文跑探索 / 审阅 / 研究，不污染主线
- Hooks 入门：SessionStart / UserPromptSubmit / PostToolUse 做个人自动化
- Cursor 进阶：Composer、Background Agents、.cursorrules 深挖
- Plugins 生态使用：直接装 Everything Claude Code / Superpowers 等社区插件上手

### 实践
- 现场演示：用 subagent 做一次代码审阅；写一条 PostToolUse hook 自动跑 lint；装一个社区插件并调用其能力

### 作业
完成两件事：（1）为常用任务自定义一个 slash command 或 hook（如自动 lint、commit message 生成）；（2）用 subagent 对一段真实代码做一次审阅。提交命令/hook 配置文件、subagent 调用记录与审阅结论。

---

## 第 3 课：MCP 与外部能力接入
### 内容
- MCP 核心概念：Tools、Resources、Prompts
- 实操演示：把本地文件 / 数据库 / API 文档接给 AI
- 权限与安全边界控制

### 实践
- 现场接入一个 MCP Server，让 AI 读取外部资源完成一个开发任务

### 作业
为你的项目接入一个 MCP Server（可选方向：本地文件系统、数据库、API 文档或 GitHub）。完成一个端到端任务：AI 通过 MCP 读取外部资源 → 理解内容 → 产出开发产物（如生成接口代码、数据模型或测试用例）。提交 MCP 配置文件、任务执行过程的会话记录，以及你对接入效果的简要评价（哪些好用、哪些不好用）。

---

## 第 4 课：Skill 设计与能力沉淀
### 内容
- Skill 是什么，与 Prompt / 规则 / 工作流的区别
- Skill 的结构：触发条件、输入输出、执行步骤
- 如何把高频任务沉淀为可复用的标准能力

### 实践
- 现场设计并调用一个开发类 Skill（如代码审查或接口文档生成）

### 作业
从你日常开发中找一个重复性高的任务（如代码审查、日志分析、接口文档生成、SQL 审查等），将其设计成一个完整的 Skill。提交 SKILL.md 文件，需包含：触发条件、输入输出定义、执行步骤和使用示例。额外加分项：实际调用该 Skill 完成一次真实任务，并附上执行效果截图。

---

## 第 5 课：规则体系与 Spec 驱动开发
### 内容
- 从 vibe coding 到 spec-driven：为什么不能直接让 AI 写代码
- rules / guidelines / spec 的作用差异与配合方式
- OpenSpec 工作流：proposal → specs → design → tasks → implement

### 实践
- 为一个功能写一页 spec + 配套 rules，让 AI 基于 spec 生成实现计划

### 作业
选一个功能需求，为它写一份 spec（含目标、方案、任务拆解）和至少 2 条 rules，让 AI 基于 spec + rules 生成实现计划。提交 spec 文件、rules 文件和 AI 生成的计划。

---

## 第 6 课：Harness 设计——让 AI 能持续做事
### 内容
- 什么是 Harness：为 AI 提供稳定环境、任务状态和阶段目标
- Harness 四要素：初始化、执行、检查点、上下文交接
- 长任务如何跨上下文窗口持续推进

### 实践
- 为一个跨多文件的重构任务设计最小 harness 并现场演示

### 作业
选一个需要多轮对话的开发任务，为它写一个最小 harness（初始化文档 + 任务状态文件 + 交接模板），用这个 harness 驱动 AI 完成任务。提交 harness 文件和执行记录。

---

## 第 7 课：Agent 工作流——Claude Code Agent Teams + Hermes Agent
### 内容
- 心智模型：从单 agent 到 agent team
- Claude Code Agent Teams（内嵌型）：多 agent 共享 task list、互相对话
- Hermes Agent（独立型）：持久记忆 + 多入口 + 模型无关
- 选型与组合：何时用哪个，二者怎么叠加

### 实践
- 现场演示：跑一次 3-teammate 的 PR review + 切 Hermes provider

### 作业
二选一（30 分钟内可完成）：(A) 跑通 Claude Code Agent Team（开实验 flag 起 3-teammate review 一个真实项目，提交 synthesis）；(B) 装通 Hermes（配两家 provider 演示 `/model` 切换 + 接通 Telegram，提交会话截图 + `hermes doctor`）。

---

# 第二部分：综合项目实战

## 第 8 课：项目实战一——用 Superpowers 复刻 web3.career
### 内容
- 用 Superpowers 的 writing-plans / executing-plans / subagent-driven-development 串起整个项目
- 前后端联调：Next.js 前端 + 后端 API，AI 全程辅助 spec → 代码 → 联调

### 实践
- 现场用 Superpowers 跑一段 web3.career 复刻：从 PRD 拆 plan，到分块执行

### 作业
选一个模块（列表 / 详情 / 筛选 / 数据接入任选其一），用 Superpowers 跑一遍 plan→implement→review 闭环。提交 plan 文件、代码、跑通截图。

---

## 第 9 课：项目实战二——用 Claude Agent Teams 做 Polymarket 黑客松
### 内容
- 用 Claude Code Agent Teams 拆角色（如 backend / frontend / reviewer）并行推进
- 与第 7 课对应：lead + teammates + 共享 task list 真实落地一个项目

### 实践
- 现场起一个 3-teammate team 协同完成 Polymarket 项目的一段需求

### 作业
为黑客松项目起一个至少 3 角色的 Agent Team，让它们协同完成一个 feature。提交 team 配置、各 teammate 输出、lead synthesis。

---

## 第 10 课：项目实战三——用 Hermes Agent 做 Hyperliquid 黑客松
### 内容
- 用 Hermes Agent 长跑、自托管、跨平台特性服务一个真实项目
- 与第 7 课对应：持久记忆 + 多入口 + 模型无关在实战中怎么发挥

### 实践
- 现场用 Hermes 跑通一段 Hyperliquid 项目工作流（自动数据拉取 / 推送通知 / 切模型对比）

### 作业（期末大作业）
基于 Hermes 搭一个长跑 agent 服务 Hyperliquid 项目（至少接通一个消息入口 + 用上持久记忆），完成一个完整功能。提交配置、跑通录像或 transcript、感受。

---

# 课程中涉及的重点生态与方法

## 官方基础能力
- Claude / Claude Code
- Cursor
- Codex
- Copilot
- MCP

## 方法与流程体系
- Prompt 工程
- 上下文工程
- Rules / Guidelines / Policy 注入
- Spec 驱动开发（SDD）
- Harness 设计
- Agent Workflow
- Eval / 验收体系
- CI/CD 集成

## 社区增强实践与扩展生态
- OpenSpec（Spec 驱动开发框架）
- Everything Claude Code（agent harness 优化系统）
- Superpowers（AI agent 开发方法论与 skills 框架）
- Claude Code 插件 / Skills / Hooks / MCP 扩展开发

---

# 一句话总结

这套课程不只是教"如何使用 AI 编码工具"，而是系统讲清：

**如何结合 Claude、Cursor、Codex、MCP、Skill、OpenSpec、Harness、Everything Claude Code、Superpowers、Agent Workflow 和 Agent Teams，把 AI 真正融入软件开发全流程并形成稳定提效。**
