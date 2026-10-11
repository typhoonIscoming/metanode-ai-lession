# 第 6 课：Harness 设计 — Superpowers 风格

> 课程视频回放：[点击观看](https://appibxs98ig9955.h5.xet.pomoho.com/p/course/video/v_6a21b1e4e4b0694c5bd0bc58?product_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&course_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&sub_course_id=subcourse_3EUmreviThPpAUC2IJ1NTqoDbk5)

上节课你用 OpenSpec 把"做什么"写成了合同——proposal / specs / design / tasks / IMPLEMENTATION 五份 markdown 文件。其实 OpenSpec 已经**悄悄做了一件 harness 的事**：tasks.md 里那些 `- [ ]` checkbox 写在磁盘上，新会话读 tasks.md 看哪行还是 `[ ]` 就能从那里接着干——这就是 harness 的最朴素形态。

本课要把这个"把状态写进磁盘文件"的思路**显式化、推广到一切长任务**——这个更通用的模式就叫 **harness**。OpenSpec 是 harness 的一种**特化形态**（只针对 spec-driven feature，五段固定，只管"做什么"）；本课用 Superpowers 风格的 harness 是**更通用的形态**——任何长任务（多策略回测、批量数据处理、跨周末的重构）都能套同一套 plan + HANDOFF 文件管。

打个比方：**OpenSpec 是给 feature 量身定做的轿车，harness 是底盘**——底盘上能造轿车、皮卡、卡车，OpenSpec 是其中一款。本课讲底盘怎么造，并用 Superpowers 的 `writing-plans` + `executing-plans` 跑一个 6-scenario 的多周期回测做现场演示——真实跑一次"跑一半 → /clear → 新会话续完"的完整链路。

时长约 25 分钟，四个主题：
1. Harness 是什么 / AI 为什么会"变笨"
2. Harness 的四要素（init / execute / checkpoint / handoff）
3. Superpowers 的 14 个 skill 分别管什么
4. 演示：用 writing-plans + executing-plans 跑一个跨上下文的 multi-period-backtest

> **本课以听讲为主**：§四 演示由讲师在课堂上现场进行——你只需要看着 plan 文件如何在 AI 的反复 Edit 下成为"任务的进度日志"，不必跟着敲键盘。演示用到的样本都在 `lesson6/project/plans/`、`lesson6/demo/`、`lesson6/project/reports/` 下，课后想自己跑一遍随时可以对照——但本课**不要求**。

---

## 〇、前置确认（30 秒）

开始前，确认以下各项：

- [ ] Claude Code 已安装（`claude --version` 能跑）
- [ ] Superpowers 插件已装（lesson 2 已装过；验证：`claude --plugin list 2>/dev/null | grep -i superpower`，或直接在对话里输 `/superpowers:writing-plans` 看是否能调起）
- [ ] Python ≥ 3.11、`pandas` / `numpy` / `matplotlib` 已装（lesson 4 已用过）
- [ ] `lesson6/project/prices.db` 存在且含 BTCUSDT + ETHUSDT 各 90 天（检查：`sqlite3 lesson6/project/prices.db "select symbol, count(*) from ohlc group by symbol"`，应见 `BTCUSDT|90` 和 `ETHUSDT|90`）
  - 缺数据就 `cd lesson6/project && python seed_db.py` 补一次
- [ ] 你知道 `/clear` 是 Claude Code 的清空上下文命令（不是清空对话记录——是让 AI 忘掉之前所有消息），本课会真用一次

全部打勾，继续。

---

## 一、Harness 是什么 / AI 为什么会"变笨"

**真实失败案例**：你让 Claude 跑一个 10 步的重构任务，前 5 步漂亮通过。第 6 步它开始问"我们刚刚改的是哪个文件来着"——你回头一看，对话窗口已经塞了 70k tokens，模型开始**遗忘前文**。Claude Code 不会"自动 /clear"，但上下文窗口逼近极限时，输出质量会急转直下：忘记规则、重复已做过的步骤、把 lesson 4 的接口签名记错。

**根本原因**：模型本身没有持久记忆。当前会话的所有"state"都活在上下文窗口里——一旦窗口满了或你手动 `/clear`，state 就丢了。

**一个生活化的类比**：harness 就像工地的**施工日志本**——工人下班、换班、甚至换公司，只要日志本一直在工地上，下一拨人翻开日志就知道"昨天干到第 5 层、今天该浇第 6 层混凝土"。AI 也一样：`/clear` 相当于下班，重开 Claude Code 相当于换班——**只要进度都写在日志（plan 文件）里，任务永远不会"断"**。

**Harness 的核心思想**：**把 state 从上下文里搬到文件里**。任何时候有新进展就写一笔到 plan 文件，任何时候要续上就读这份 plan。AI 的对话上下文变成"工作台"——可以随便清，因为真正的进度记录在文件系统里。

| | vibe 会话 | harness 会话 |
|---|---|---|
| 进度记在哪 | AI 的上下文里 | plan 文件里 |
| /clear 后会发生什么 | 一切重来 | 读 plan 接着干 |
| 任务上限 | 一个上下文窗口（约 200k tokens） | 无上限 |
| 跨会话/跨人协作 | 不行 | 把 plan 路径给下一个人就行 |

核心区别：**harness 把任务从 AI 的"记忆"里拿出来，放进可审计、可移交、可断点续跑的文件**。

> **OpenSpec 是 harness 的一种**——lesson 5 的 `openspec/changes/<id>/tasks.md` 里那些 `- [ ]` checkbox 就是一份**给 feature 用的 plan**：写在磁盘上、新会话能读、checkbox 状态记录进度。它和本课要讲的 `plans/<task-name>.md` 是同一类工程产物，只是 OpenSpec 模板**只针对 "spec → 实现" 一种工作场景**。本课讲的是更通用的 plan 形态，可以套用到任何长任务（多策略回测、跨周末的重构、批量数据处理……都行）。

---

## 二、Harness 的四要素

任何一份合格的 harness 都包含四个动作：

| 要素 | 干什么 | 文件落点 |
|---|---|---|
| **init** | 把任务拆成可独立验证的 step，写成 plan | `plans/<task-name>.md` |
| **execute** | 按 plan 一步步跑，每步出结果就回填到 plan | 修改 `plans/<task-name>.md` |
| **checkpoint** | 跑一段后写交接快照（关键中间结果 + 下一步指针） | `plans/HANDOFF.md` |
| **handoff** | 给下一个 session/人/agent 一句话：从哪续 | 写在 `HANDOFF.md` 顶部 |

> **三件套**：init 产物 = plan；execute 过程 = plan 不断被打勾 + 回填；checkpoint + handoff = HANDOFF.md。最终聚合的结论写到 `reports/<task-name>.md`。

只要这三个目录（`plans/`、`HANDOFF.md`、`reports/`）保持同步，任何时候来一个新 session，第一件事都是"读 plan，看哪行还是 `[ ]`"——这就是 harness 的本质：**约定，不是工具**。

---

## 三、Superpowers 的 14 个 skill 速览

`superpowers` 插件由 [obra (Jesse Vincent)](https://github.com/obra/superpowers) 开源、托管在 Claude 插件市场——**不是 Anthropic 官方**，但社区认可度高，是目前讨论 AI 工作流 / harness 时引用最多的标杆插件之一（lesson 2 已装）。目前提供 14 个 skill，按工作流阶段拆开看：

### 3.1 计划与执行（harness 三件套——本课核心）

| Skill | 一句话 | 触发场景 |
|---|---|---|
| `superpowers:writing-plans` | 把一个多步任务展开成 plan 文件（Goal / Architecture / 进度表 / Tasks / Resume Protocol） | 任何"有 spec / 需求、但还没动代码"的任务起点 |
| `superpowers:executing-plans` | 读一份 plan，按 step 跑、每跑完一步回填一笔 | 拿到一份现成 plan、想让 AI 按计划落地 |
| `superpowers:subagent-driven-development` | 每个 task 派一个新 subagent 跑，跑完做 spec + quality 两段 review | 当 plan 里任务彼此独立、可以并行或不污染主上下文 |

> 这三个加起来，就是本课要讲的 **harness**——前两个本课课堂会演示。

### 3.2 思考与设计

| Skill | 一句话 | 触发场景 |
|---|---|---|
| `superpowers:brainstorming` | 用对话式问答把模糊想法磨成可写 spec 的设计 | 你只有一个"想做 X"的念头、还没写 proposal/specs |
| `superpowers:writing-skills` | 用 TDD 的方式写新 skill / 修旧 skill（skill 本身也是产物） | 想把自己的高频流程沉淀成 SKILL.md |

### 3.3 实现纪律

| Skill | 一句话 | 触发场景 |
|---|---|---|
| `superpowers:test-driven-development` | 先写测试看它挂、再写最少代码让它过 | 实现新 feature 或修 bug 之前 |
| `superpowers:systematic-debugging` | 必须找到根因再动手，禁止"症状修复" | 遇到 bug / 测试挂 / 行为异常 |
| `superpowers:verification-before-completion` | 声称"完成"前必须真跑一遍验证命令，证据先于断言 | 准备提交 / 开 PR / 说"搞定了"之前 |

### 3.4 评审与协作

| Skill | 一句话 | 触发场景 |
|---|---|---|
| `superpowers:requesting-code-review` | 派一个 code-reviewer subagent 看本次 diff，提早抓问题 | 完成一个 feature / 关键 commit / merge 前 |
| `superpowers:receiving-code-review` | 收到 review 意见时先技术核实，不机械执行也不强词夺理 | 拿到任何 review 反馈、准备修改之前 |
| `superpowers:dispatching-parallel-agents` | 把 2+ 个相互独立的任务派给不同 subagent 并行跑 | 多个独立 bug / 多个独立模块需要同时调查 |

### 3.5 环境与收尾

| Skill | 一句话 | 触发场景 |
|---|---|---|
| `superpowers:using-git-worktrees` | 用 git worktree 起一个隔离工作区，不打扰当前分支 | 起一段独立 feature 前，或执行 plan 前想隔离 |
| `superpowers:finishing-a-development-branch` | 实现+测试都过了之后，告诉你接下来该 merge / PR / 清理 | 一段工作真正"做完"那一刻 |
| `superpowers:using-superpowers` | Superpowers 的元 skill——告诉你如何找/用其他 skill | 每段会话开始时 AI 自我引导用 |

### 怎么触发

每个 skill 都有两种触发方式：
- **斜杠**：在 Claude Code 里输 `/superpowers:<skill-name>`，例如 `/superpowers:writing-plans`
- **自然语言**：直接说要做的事，AI 会自动匹配，例如 "帮我把这个 5 步任务写成 plan"——AI 会在背后调起 writing-plans

> **关键认知**：Superpowers 的本质是 **"AI 应该按什么纪律工作"的文档集**——SKILL.md 文件里没有代码逻辑，全是 prompt 工程教 AI 把流程做对。你完全可以不装这个插件，自己手写一份"写 plan / 跑 plan / handoff"的规范，效果一样——插件提供的是规范的"门面"，真正起作用的是**纪律**。

---

## 四、演示

本节由讲师在课堂上手动演示——**学员只看，不跟着敲键盘**。具体演示什么、跑到哪一步、按什么节奏，由讲师当场决定，不强求按某个固定脚本走。

课后想自己回看演示用的样本，看这三份就够：

- `lesson6/project/plans/multi-period-backtest.md` —— plan 文件长什么样
- `lesson6/project/plans/HANDOFF.md` —— 一次会话交接快照
- `lesson6/project/reports/multi_period.md` —— 任务终点的聚合报告

或者直接 `cat lesson6/demo/01-plan/` ~ `03-report/` 看副本——内容完全一致。


---

## 五、关键认知

**Plan 是 AI 的外脑**：模型本身没有持久记忆——上下文窗口是"短期记忆"，每次 `/clear` 就清空。Plan 文件是"长期记忆"——磁盘上的 markdown，永远不丢。把任务进度写在 plan 里，AI 的"会话"就从"必须连贯的一次对话"降级为"可以断、可以换人的工作台"。这一步认知翻转之后，你才能让 AI 干超出单上下文容量的长任务。

**每写一笔就回填一笔**：harness 最容易死在"批量回填"上。你跑了 5 个 scenario 想着"等会儿一起填到 plan 里"——只要中间任何一次中断、网络断、误关窗口，那 5 个数字就活在 AI 的脑子里没活在磁盘上。**纪律**：跑一次就 Edit plan 一次，把数字 + 打勾一起改。这条规则没有例外。

**Harness 不是工具，是约定**：Superpowers 14 个 skill 里没有一个写了代码逻辑，全是 prompt 工程——把"先写 plan、跑完一步打勾、写 HANDOFF、聚合 report"这套约定打包成 SKILL.md。你也可以完全不用插件——只要你自己手写一份格式相近的 plan，并在每次会话开头说"读这份 plan，从第一个 `[ ]` 续"，效果一样。skill 提供的是规范的"门面"，真正起作用的是**你坚持把进度落到文件里的纪律**。今天演示的 `writing-plans` + `executing-plans` 只是 14 个 skill 里和 harness 直接相关的两个；其它 12 个（brainstorming / TDD / 系统化 debug / verify-before-complete / code review / subagent-driven-dev …）共同覆盖了 AI 工作流的全部阶段，本课之后你可以按需调用。

记忆口诀：

```
state 不在脑子里，state 在 plan 里
跑一步，回一笔
HANDOFF 写得越具体，下一个会话越省心
```

---

## 六、反模式（3 条）

**1. Plan 写完不维护，跑到一半数字回填漏一行**

写 plan 是一次性脑力支出，但维护 plan 是每一步都要做的肌肉活动。最常见的失败模式：跑完第 1 个 scenario 立刻填上了 plan；跑完第 2 个想"等会儿一起填"；跑完第 3 个发现"等等第 2 个数字是多少来着"——AI 的上下文里还残留，但跨会话之后就再也找不回来了。**修复**：每跑完一个 step 立刻 Edit plan，把"跑命令 / 看输出 / 回填 plan"当成一个原子动作，不允许拆开。

**2. Plan 太抽象，每个 step 都需要解释才能跑**

```markdown
[ ] Step 1: 把回测跑起来    # ❌ 太空
[ ] Step 2: 看一下结果     # ❌ 看到什么算结果？
```

vs.

```markdown
[ ] Step 1: cd lesson6/project && python -c "..."  # ✅ 命令可粘
[ ] Step 2: 把输出的 sharpe / max_dd / win_rate / cum_return 4 个数字填到 plan 表行 1，把 [ ] 改成 [x]  # ✅ 验收明确
```

抽象的 plan 等于没有 plan——AI 看到"跑起来"会回头问"具体怎么跑"，跨会话续接时下一个 AI 又会问一次。**修复**：每个 step 必须包含"做什么命令 + 看什么输出 + 改哪个文件"三段，让 plan 自包含到不需要额外说明。

**3. HANDOFF 不指向具体下一步，下一会话还要自己分析**

```markdown
# HANDOFF
进度：Phase 1 跑完了，准备 Phase 2。              # ❌ "Phase 2" 是什么？怎么开始？
```

vs.

```markdown
# HANDOFF — Phase 1 → Phase 2
**Status:** Scenarios 1-3 完成，4-6 待跑

## Next: paste this into a fresh session
> 请读 plans/multi-period-backtest.md，从第一个 [ ] 续……  # ✅ 整段可粘的 prompt
```

HANDOFF 的全部意义在于：**让下一个 session 不需要思考就能开工**。"看 Phase 2 干啥"是思考，"整段粘贴这段 prompt"不是思考。**修复**：HANDOFF 里必须有一段 fenced 文本块，下一会话第一句**整段粘**就能续。

---

## 七、作业

> **完整任务说明**：[homework/task1-harness/README.md](./homework/task1-harness/README.md)

写一份 minimal plan，跑过一次 **真的 `/clear`** 续接。任务不需要长——3-5 step 的 mini plan 就够演示。

候选方向（任选一个或自选）：
- 把仓库里所有 README.md 翻译成英文（按文件分批）
- 把 lesson 4 backtest 在更多策略上复跑（每 2 个一组）
- 把一个长函数重构成 4 个小函数，每次一个

30 分钟内可完成，**不要求长任务**——你要练的是 harness 的纪律，不是任务长度。

提交：
1. `PLAN.md`（最终版，全部 `[x]`）
2. 一段 200 字感受：续上的体验如何？plan 写到多详细才够？

---

## 学完这课你能做什么

- 解释 harness 是什么、为什么 AI 在长任务里需要 harness、四要素分别落到哪个文件
- 一句话说清楚 Superpowers 14 个 skill 各自负责工作流哪个阶段（计划/思考/纪律/评审/环境）
- 看着 `writing-plans` + `executing-plans` 的演示，理解 "Phase 1 → /clear → Phase 2 续上" 的完整流程长什么样
- 识别 harness 的三大反模式（不维护 / 太抽象 / handoff 不具体），并知道怎么修

下节课（Lesson 7）：plan 跑得起来 → CI 守得住——把"每次都人工跑一遍 verify"升级成"在仓库里钉一道闸门，任何提交都自动跑"。

---

## 延伸阅读

| 来源 | 路径 / URL | 说明 |
|---|---|---|
| 课堂 plan 三件套 | `lesson6/project/plans/multi-period-backtest.md`、`plans/HANDOFF.md`、`reports/multi_period.md` | 完整的真实产物，对照本课每段 |
| Demo 副本 | `lesson6/demo/01-plan/`、`02-handoff/`、`03-report/` | 三件套的副本，方便课堂演示时 cat 出来看 |
| Superpowers 14 个 skill 源码 | `~/.claude/plugins/cache/claude-plugins-official/superpowers/*/skills/` | 每个子目录一份 SKILL.md，可以直接读 |
| Superpowers writing-plans | `/superpowers:writing-plans`（在 Claude Code 里调起） | 演示中 init 阶段的 skill |
| Superpowers executing-plans | `/superpowers:executing-plans` | 演示中 execute 阶段的 skill |
| Anthropic 关于 long-running tasks 的工程实践 | [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) | 包含 harness / plan / checkpoint 的设计哲学 |
