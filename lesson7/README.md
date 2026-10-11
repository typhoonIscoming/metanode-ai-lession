# 第 7 课：Agent 工作流——Claude Code Agent Teams + Hermes Agent

> 课程视频回放：[点击观看](https://appibxs98ig9955.h5.xet.pomoho.com/p/course/video/v_6a29cec9e4b0694c35173753?product_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&course_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&sub_course_id=subcourse_3EUmreviThPpAUC2IJ1NTqoDbk5)

上节课你看到 harness 让 AI 在长任务里跨会话续命。但一直是**一个 AI**在干活——状态在文件、活儿还得排队跑。本课往前再走一步：**让多个 AI 同时干、互相讨论、自己分配工作**——这就是 "agent team / agent 工作流"。

行业里 2026 年最具代表性的两条路：

- **Claude Code Agent Teams**（Anthropic 官方，实验性）—— 在 Claude Code **内部** 编排多个 Claude 实例，会话内并行干活、互发消息、共享 task list
- **Hermes Agent**（Nous Research 开源，MIT，155k stars）—— 一个**独立**的、长跑的、能挂 Slack/Telegram/Discord 的自进化 agent，模型无关

两者刚好是 **"内嵌型 vs 独立型"** 的对偶。学完本课你能判断什么场景该用哪个。

> **本课以听讲为主**：演示由讲师在课堂上现场进行——你只需要看着配置文件、命令行长什么样、teammates 之间怎么对话，不必跟着敲键盘。所有命令和配置都在讲义里能找到，课后想自己装一遍随时可以。

时长约 25 分钟，四个主题：
1. 引子：从单 agent 走到 agent team
2. Claude Code Agent Teams（内嵌型多 agent 协作）
3. Hermes Agent（独立型长跑 agent + 多平台）
4. 对比 + 选型 + 反模式

---

## 〇、前置确认（30 秒）

开始前，确认以下各项：

- [ ] Claude Code 已安装（`claude --version` 能跑），版本 ≥ **v2.1.32**（Agent Teams 要求的最低版本）
- [ ] 你的 Claude Code 至少有 Pro / Team / Max 之一的 plan（Agent Teams 会消耗显著更多 token，免费额度跑两次就用完）
- [ ] 终端最好是 macOS Terminal / iTerm2 / WSL Ubuntu——split-pane 模式依赖 `tmux` 或 iTerm2，**VS Code 内置终端 / Windows Terminal / Ghostty 不支持**（in-process 模式它们都能用，作降级方案）
- [ ] 如果你想课后玩 Hermes：Linux / macOS / WSL2 / Termux 都行（Windows 原生 PowerShell 装 Hermes 还在 early beta）

全部打勾，继续。

---

## 一、引子：从单 agent 走到 agent team

**一句话**：你以前是和**一个 AI 结对**，现在你**管一个 agent team**。

| | 单 agent | Agent team |
|---|---|---|
| 谁在干活 | 一个 Claude / GPT，你 prompt 一句它干一句 | 多个 agent 实例并行干活，每个有自己的 context |
| 任务分发 | 你手工说"先做 A、再做 B" | 一个 lead 拆任务到 task list，其它 agent 自己 claim |
| 沟通方式 | 你 ↔ AI 单线 | agent 之间互发消息、相互挑战、共享发现 |
| 适用场景 | 大部分日常编码 | research / review / 多视角 debug / 跨层重构 |
| 瓶颈 | AI 写得快，但每次只能在一条线推进 | "瓶颈从生成转移到验证" —— 多个 agent 同时出活，人来收口 |

后半句"瓶颈从生成转移到验证"是 Addy Osmani 2026 年总结的——**这也是 L6 harness 概念能 work 的真正理由**：harness 把 state 落到文件后，再多 agent 同时读同一份 plan 也不会冲突。Agent team 就是这种"多个 agent 同时按一份 plan / task list 跑"的工程化产物。

本课的 §二、§三 分别讲两种代表实现：**Claude Code 把 agent team 做成内嵌功能；Nous Research 把 agent 做成独立长跑平台**。

---

## 二、Claude Code Agent Teams（内嵌型）

### 2.1 一句话 + 关键事实

**Agent Teams 是 Claude Code 的实验性 feature**：一个 Claude Code 会话当 **lead**（领班），它派出多个 Claude Code 实例当 **teammates**（队员）。Teammates **彼此可以直接对话**，**共享 task list**，**各自有独立 context window**——和老的 subagent 不是一回事。

实验性 + 需要显式开启 + 要 v2.1.32+。

### 2.2 vs 老的 subagents（关键区别）

| | Subagents | Agent Teams |
|---|---|---|
| Context | 自己的 context；结果汇报回 caller | 自己的 context；**完全独立** |
| Communication | 只能回报 main agent | **Teammates 之间直接发消息** |
| Coordination | Main agent 统管全部 | **共享 task list 自协调** |
| 适合什么 | 干完一件事、把结果给我 | 需要互相讨论、挑战、汇总的复杂工作 |
| Token | 低（结果摘要返回主上下文） | 高（每个 teammate 一个独立 Claude 实例） |

> **认知核心**：subagent 是"派一个跑腿"，Agent Team 是"派一个真正的小组——他们之间能商量"。

### 2.3 怎么开启

默认关闭。在 `~/.claude/settings.json` 加一行环境变量：

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

或直接在 shell 里 `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`。

### 2.4 起一个 team（自然语言而已）

开启后**不需要写任何配置文件**——直接用自然语言告诉 Claude 你要什么。比如：

```
我在设计一个 CLI 工具，让开发者追踪代码里的 TODO 注释。
帮我起一个 agent team 从三个角度探索：一个负责 UX，一个负责技术架构，
一个唱反调。
```

Claude 会自动：
1. 建一个 team（落到 `~/.claude/teams/<team-name>/config.json`）
2. Spawn 3 个 teammates，每个独立的 Claude Code 实例
3. 建共享 task list（落到 `~/.claude/tasks/<team-name>/`）
4. 协调它们干完活、汇总结论、清理 team

**官方推荐 size：3-5 个 teammates，每人 5-6 个 task**——再多协调开销超过收益。

### 2.5 架构——四个组件

| 组件 | 作用 |
|---|---|
| **Team lead** | 起 team 的那个主会话——拆任务、spawn teammates、协调、汇总 |
| **Teammates** | 独立 Claude Code 实例，每个有自己的 context window |
| **Task list** | 共享的工作清单（pending / in_progress / completed + 依赖管理） |
| **Mailbox** | 异步消息系统——teammates 之间发的消息自动投递 |

落盘位置：
- `~/.claude/teams/{team-name}/config.json` —— 团队配置（runtime state，**别手动改，会被覆盖**）
- `~/.claude/tasks/{team-name}/` —— task list 文件

> **注意**：Claude Code 不识别项目级的 `.claude/teams/teams.json`。Team config 只在用户级的 `~/.claude/teams/` 下。

### 2.6 两种显示模式

| 模式 | 哪儿展示 | 依赖 | 适合 |
|---|---|---|---|
| **in-process**（默认）| 全部 teammate 在主终端里，`Shift+Down` 切换查看 | 无 | 任何终端，包括 VS Code 内置、Windows Terminal |
| **split-pane** | 每个 teammate 一个独立 pane | `tmux` 或 iTerm2 + `it2` CLI | macOS / WSL，想同屏盯全员 |

切换方式：

```json
// ~/.claude/settings.json
{
  "teammateMode": "in-process"  // 或 "tmux"、"auto"
}
```

或单次 override：`claude --teammate-mode in-process`。

### 2.7 关键工作流：plan approval 流程

对**风险动作 / 复杂改动**，可以要求 teammate **先做 plan 再实施**：

```
派一个架构师 teammate 重构 auth 模块。
进改动前必须先提 plan 给我审批。
```

Teammate 在 **read-only plan mode** 工作 → 把 plan 发给 lead → lead **自主审批**（你可以在 prompt 里加判断标准，比如"只批通过包含测试的 plan"）→ 批准后 teammate 退出 plan mode 开始实施。

### 2.8 质量门——三个 hook

```
TeammateIdle    # teammate 即将进入 idle 时跑；exit 2 让它继续干
TaskCreated     # task 被创建时跑；exit 2 拦截创建并反馈
TaskCompleted   # task 即将 mark completed 时跑；exit 2 拦截并反馈
```

例如：可以写一个 `TaskCompleted` hook，让它跑一遍 `pytest`，挂了就 exit 2 把 task 打回 in_progress——这就是把 L6 harness 的 "verify before complete" 自动绑到 task 上。

### 2.9 适合场景 / 不适合场景

✅ **适合**：
- **Parallel code review**：3 个 reviewer 分别看 security / performance / test coverage
- **Debugging with competing hypotheses**：5 个 teammate 各自验证一个假说，相互挑战
- **Cross-layer 重构**：frontend / backend / tests 三个人各管一摊
- **新 feature 多模块并行**

❌ **不适合**：
- 顺序任务（B 必须等 A 出结果）
- 多个 teammate 改同一个文件（会互相覆盖）
- 简单任务（协调开销大于收益）

### 2.10 限制（实验性，需知道的边界）

- ❌ **不能 nested**：teammate 不能再起自己的 team
- ❌ **Lead 不能转**：起 team 那个 session 终身是 lead
- ❌ **同时一个 team**：一个 lead 只能管一个 team，要新建必须先清理旧的
- ⚠️ **`/resume` 不恢复 in-process teammates**：session 恢复后 lead 可能找不到原 teammate，要让它重新 spawn
- ⚠️ **Task 状态偶尔卡住**：teammate 偶尔忘记 mark complete，导致依赖 task 不解锁

---

## 三、Hermes Agent（独立型）

### 3.1 一句话 + 关键事实

**Hermes Agent = Nous Research 开源（MIT，155k GitHub stars）的自进化 AI agent**。

它和 Agent Teams 截然不同——**Hermes 是独立平台**，不绑 Claude Code、不绑 Anthropic、不绑任何一家模型供应商。装一次能跑在 $5 VPS 上 7×24 服务你，通过 CLI / Telegram / Discord / Slack / WhatsApp / Signal / Email / Home Assistant 8 种入口和你对话。

### 3.2 装它（一行）

```bash
# Linux / macOS / WSL2 / Termux
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Windows PowerShell（early beta）
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

装完后跑一次 `hermes setup` 走完整向导（选模型、配 key、开工具）。

### 3.3 核心命令（CLI 层）

| 命令 | 用途 |
|---|---|
| `hermes` | 启动交互式 CLI |
| `hermes setup` | 完整向导（首次推荐） |
| `hermes model` | 切换 LLM 提供商 / 模型 |
| `hermes tools` | 启用 / 禁用工具 |
| `hermes gateway` | 启动消息网关（连 Telegram / Discord / ...） |
| `hermes config set` | 单独改某个配置 |
| `hermes doctor` | 诊断当前安装状态 |
| `hermes claw migrate` | 从 OpenClaw 迁移历史会话 |

### 3.4 会话内 slash 命令

| 命令 | 用途 |
|---|---|
| `/new` 或 `/reset` | 新建会话 |
| `/model [provider:model]` | 切换模型（如 `/model openai:gpt-4o` 或 `/model anthropic:claude-opus-4-7`） |
| `/personality [name]` | 切换人格（基于 `SOUL.md` 配置） |
| `/skills` 或 `/<skill-name>` | 浏览 / 调用技能 |
| `/retry` / `/undo` | 重试 / 撤销上一轮 |
| `/compress` | 压缩 context |
| `/usage` / `/insights --days N` | 查 token 用量 / 行为洞察 |
| `/stop` | 中断当前工作 |

### 3.5 模型无关——切换 Claude ↔ OpenAI 的真实做法

Hermes 支持 **任意模型供应商**：Nous Portal / OpenRouter（200+ 模型）/ NovitaAI / NVIDIA NIM / OpenAI / Anthropic / Kimi / MiniMax / Hugging Face / 自托管 endpoint 等等。

**切换方式有三种**：

**A. 交互向导（推荐——加 / 切 provider 都走这个）**

```bash
hermes model
# 选 provider → 输 API key（或 OAuth 登录）→ 选默认 model
```

**B. 会话内即时切**（前提：provider 已配置过）

```
/model openai:gpt-4o
/model anthropic:claude-opus-4-7
/model openrouter:google/gemini-2.0
/model custom:local:qwen-2.5
```

**C. 改配置文件 `~/.hermes/config.yaml`**

```yaml
model:
  provider: "anthropic"
  default: "claude-opus-4-7"
```

API key 落 `~/.hermes/.env`，OAuth providers（Anthropic / Google Gemini / MiniMax）token 落 `~/.hermes/auth/` 自动刷新。

### 3.6 持久记忆三件套（这是 Hermes 和 Agent Teams 最大的差异）

Agent Teams 的 teammate 一旦 lead 退出就**全员失忆**。Hermes 不一样——它自带持久记忆系统：

| 文件 / 机制 | 作用 |
|---|---|
| `MEMORY.md` | 一般知识 / 事实（agent 自己往里写） |
| `USER.md` | 用户画像（Honcho 辩证式建模，渐进式了解你） |
| **FTS5 全文索引 + LLM 摘要** | 跨会话搜索过往对话，三周前聊的内容也能调出来 |

**关键概念**：**Agent-curated memory**——不是你手写 CLAUDE.md，是 agent 自己 curate。complex task 跑完它会自动**写一个 skill 存到 `~/.hermes/skills/`**，下次再遇到类似活直接调用。

### 3.7 多入口 / 多平台 / 多人格

| 入口 | 用途 |
|---|---|
| CLI | 主要开发体验 |
| Telegram / Discord / Slack / WhatsApp / Signal | 移动端随手用 |
| Email | 邮件触发任务 |
| Home Assistant | 智能家居场景 |

所有入口背后是**同一个 gateway 进程**——支持语音备忘转文字、跨平台会话延续、多人格切换（`/personality work` ↔ `/personality casual`）。

### 3.8 部署形态

| 形态 | 适用 |
|---|---|
| **$5 VPS** | 个人长跑，最便宜 |
| **Daytona / Modal（serverless）** | 空闲时休眠、按需唤醒，几乎零成本 |
| **Docker / Compose** | 容器化部署 |
| **SSH** | 远程跑 |
| **GPU 集群** | 自托管开源模型 + Hermes |
| **Vercel Sandbox / Singularity** | 沙盒隔离 |

### 3.9 适合场景

✅ **适合**：
- 想要一个 **跨会话有记忆** 的私人 agent
- 想要 **多平台触达**（Slack 提个事、回来 CLI 接着干）
- 想 **自托管开源模型**、不绑定 Anthropic / OpenAI
- 长跑任务（每日报告、夜间备份、周审计——自然语言描述）

❌ **不适合**：
- 一次性短任务（杀鸡用牛刀）
- 需要 Claude Code 那种 IDE 级编辑能力（Hermes 是 chat 入口，不是 IDE 替代品——但可以通过 MCP 协议调 Claude Code）

---

## 四、对比 + 选型 + 关键认知

### 4.1 一张表对比

| 维度 | Claude Code Agent Teams | Hermes Agent |
|---|---|---|
| 性质 | Claude Code 内的实验 feature | 独立开源平台（MIT） |
| 生命周期 | 单次会话内（lead 退出就散） | 持续运行（VPS / serverless） |
| 记忆 | 各 teammate 各自 context，结束消失 | SQLite + FTS5 持久 + 自动 curate |
| 模型 | Claude only | Model-agnostic（200+ 模型） |
| 协作模式 | 多 agent 互发消息 + 共享 task list | 一个 agent 多渠道服务多用户 |
| 入口 | 终端 / IDE | CLI + 8 个消息平台 |
| 安装 | 已有 Claude Code 就只加一个环境变量 | `curl ... \| bash` 一行 |
| Token 成本 | 高（n 个 Claude 实例并发） | 看你挂的模型 |
| 适合人群 | Claude Code 重度用户、想并行做复杂工作 | 想要 7×24 私人 agent、跨平台、不绑供应商 |

### 4.2 怎么选

- **写代码、要多视角 review / debug** → Agent Teams
- **要长跑、跨周复盘、多平台触达** → Hermes
- **两个都想要** → 一起用。Hermes 可以通过 MCP 把任务派给 Claude Code（Claude Code 又可以在内部开 Agent Team）——上下游互补

### 4.3 关键认知

**Agent team 不只是"多个 agent"——是 agent 之间能对话 / 自协调**。 这是它和 subagent / 并发脚本最大的区别。Subagent 是"派跑腿、单线汇报"；agent team 是"派一个会议室、agent 自己开会"。

**单 agent 时代结束，agent team 时代开始**。前 6 课你都在和**一个** AI 打交道；从 L7 起，AI 应该被理解成 **可以被实例化为 N 个、可以互相协作的工人池**。

**记忆是 agent 长跑的命门**。 Agent Teams 没有跨会话记忆，靠 CLAUDE.md + 你的 prompt 补；Hermes 自带 agent-curated memory。要让 agent 7×24 服务你，记忆系统是绕不开的工程问题。

记忆口诀：

```
Subagent 报告，Agent Team 讨论。
单次会话用 Teams，长跑落地用 Hermes。
Agent team 不解决记忆——记忆要 harness 或 Hermes 那种文件级持久。
```

---

## 五、反模式（3 条）

**1. 起 5 个 teammate 干同一件顺序事**

Agent Teams 的甜区是**并行**。如果任务必须 A→B→C 顺序做，多个 teammate 只会互相等、互相覆盖文件。**修复**：先问自己"这事能拆成几条互不依赖的线？"——能拆出 3+ 条再起 team。

**2. Hermes 装完就当云端 ChatGPT 用**

Hermes 的核心价值是 **持久记忆 + 多入口 + 模型无关**。如果你只把它当一个套壳 CLI 用，3 天后会觉得"还不如 ChatGPT"。**修复**：装完一定要配至少一个消息入口（`hermes gateway` 接 Telegram 或 Slack），让它真的在你生活流里跑一周——你会突然发现它记得你两周前讨论过的某个方案。

**3. Agent Team 改同一个文件**

文档明写："**两个 teammate 编辑同一个文件会互相覆盖**"。**修复**：起 team 时 prompt 里就要说清楚"A 只改 src/auth/，B 只改 src/api/，C 只改 tests/"——把文件所有权显式分到 teammate 上。

---

## 六、作业

> **完整任务说明**：[homework/task1-agent-team/README.md](./homework/task1-agent-team/README.md)

二选一（30 分钟内）：

- **A. Claude Code Agent Team 跑通**：开实验 flag → 起一个 3-teammate 的 PR review team（security / performance / test coverage 三角度）→ 给一个真实小项目跑一次 review → 提交 lead 的最终 synthesis 输出
- **B. Hermes Agent 装通**：装 Hermes → 配两个不同 provider（如 Anthropic + OpenAI）→ 会话里用 `/model` 切换演示模型无关 → 接通一个消息入口（Telegram 最快）→ 提交一段会话截图 + `hermes doctor` 输出

任一都行——选你更想真正用上的那个方向。

---

## 七、学完这课你能做什么

- 解释 Claude Code Agent Teams 和 subagent 的本质区别（teammates 之间能对话 + 共享 task list）
- 在 Claude Code 里**实际开启** Agent Teams 并起一个 3-5 人的 team 干 review / debug
- 理解 Hermes Agent 为什么"独立长跑"是它的核心价值（持久记忆 + 多入口 + 模型无关）
- 在 Hermes 里用 `hermes model` 和 `/model` 在 Claude / OpenAI / 其它 provider 间切换
- 给出"何时该用 Agent Teams、何时该用 Hermes、何时一起用"的判断

下节课（Lesson 8）：综合项目实战——把 L1-L7 学到的工具串起来，完成一个端到端业务流。

---

## 八、延伸阅读

| 来源 | 路径 / URL | 说明 |
|---|---|---|
| **Claude Code Agent Teams 官方文档** | [code.claude.com/docs/en/agent-teams](https://code.claude.com/docs/en/agent-teams) | 本课 §二 主要依据，含全部 use case + best practices + limitations |
| **Hermes Agent GitHub** | [github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | 本课 §三 主要依据，含安装、配置、所有命令 |
| **Hermes Agent 文档** | [hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/) | 完整中文 + 英文文档 |
| Addy Osmani · Code Agent Orchestra | [addyosmani.com/blog/code-agent-orchestra](https://addyosmani.com/blog/code-agent-orchestra/) | "你以前结对一个 AI，现在管一个 agent team"——2026 工程师视角 |
| 课堂 demo 副本 | [demo/](./demo/) | Agent Teams 启动 prompt 样例 + Hermes 配置样例 + 对比速查表 |
| **Hermes 实战样例** | [hermes-project/](./hermes-project/) | 讲师用 Hermes 跑出来的一个真实小项目（Binance Token Heatmap，Express + 前端热力图），含 src / test / scripts——证明 Hermes 不仅能聊天，能真出活儿 |
