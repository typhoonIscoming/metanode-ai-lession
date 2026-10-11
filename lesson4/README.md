# 第 4 课：Skill 设计与能力沉淀

> 课程视频回放：[点击观看](https://appibxs98ig9955.h5.xet.pomoho.com/p/course/video/v_6a1d5ad6e4b0694c5bce5b6a?product_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&course_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&sub_course_id=subcourse_3EUmreviThPpAUC2IJ1NTqoDbk5)

上节课你让 Claude 通过 MCP **消费**外部接口（sqlite MCP → AI 直接写 SQL 查行情）。这节课反过来：你来**造接口**，把一个高频任务封装成 Skill，让 Claude 日后按需复用——不需要每次重新解释"我想回测一个策略"是什么意思。这就是从用工具到设计工具的跨越。

时长约 25 分钟，四个主题：
1. Skill 是什么
2. Skill 市场速览
3. 写 backtest skill（10 分钟动手）
4. 用 skill 跑回测对比 + 反模式 + 作业

> **跟着课件做**：每个"动手做"小节都有可直接复制的命令和 prompt。建议第一遍学习时**真打开终端跟着做一次**，不要只读。

---

## 〇、前置确认（30 秒）

开始前，确认以下各项：

- [ ] Claude Code 已安装（`claude --version` 能跑）
- [ ] `python --version` ≥ 3.11
- [ ] `pandas`、`numpy`、`matplotlib` 已装（lesson 1 demo 用过；没装就补一下：`pip install pandas numpy matplotlib`）
- [ ] 跑过 lesson 3 的 `python seed_db.py`，`lesson4/project/prices.db` 存在且 `ohlc` 表有数据（`sqlite3 lesson4/project/prices.db "select count(*) from ohlc"` 应返回 60 或以上）
- [ ] 网络能访问 `api.binance.com`（如果需要重新 seed 数据）

全部打勾，继续。

---

## 一、Skill 是什么

**Skill 是你给 Claude 定义的"标准动作"**。Prompt 是一次性指令：你打字，Claude 处理，对话结束后什么都不留下。Skill 不一样——它是一份 Markdown 文件，放进 `.claude/skills/<name>/SKILL.md` 后，Claude 每次启动都会看到它，一旦对话内容匹配触发条件就会按 Skill 里定义的流程来，不需要你重新解释。

换句话说：**Prompt 是一次性的，Skill 是可复用的**。你把"如何回测一个策略"这件事教给 Claude 一次，之后只需要说"帮我回测这个策略"，它就知道该怎么做。

下面这张表把 Claude Code 里常见的五种扩展方式放在一起对比，帮你找准各自的定位：

| 类型 | 触发 | 上下文 | 谁定义 | 典型例子 |
|---|---|---|---|---|
| **Prompt** | 你打字 | 主线对话 | 你写 | "帮我重命名这个变量" |
| **Rule** | 自动 / 文件 glob | 主线注入 | 你 / 团队 | UTC 约定、commit message 格式 |
| **Subagent** | 你主动派遣 | 独立子上下文 | 你 / 官方 | 探索代码库、独立代码审阅 |
| **MCP** | AI 判断后主动调用 | 主线注入工具 | 第三方 / 你 | sqlite 查询、文件读取 |
| **Skill** | AI 看到匹配时触发 | 主线对话 | 你 / 团队 / 社区 | brainstorming、TDD、backtest |

Skill 和 Prompt 的关键差别：Prompt 写在对话里，一次用完就没了；Skill 写在文件里，Claude 每次会话都带着，触发条件匹配就调用，不触发就静默。

---

## 二、Skill 市场速览

你不需要所有 Skill 都自己从零写。社区和官方已经积累了大量现成的 Skill，可以直接安装使用或作为参考改写。

| 来源 | URL | 一句话定位 |
|---|---|---|
| Anthropic 官方 skills | https://github.com/anthropics/skills | reference skill 集合，最权威 |
| Superpowers | https://github.com/obra/superpowers | 方法论框架（lesson 2 已装），含 brainstorming / TDD / code-review |
| Everything Claude Code (ECC) | https://github.com/affaan-m/everything-claude-code | Claude Code 增强包，含工程类 skill |
| skill.sh | https://skill.sh | 社区聚合站，按主题分类 |
| skillsmp | https://skillsmp.com | 另一个社区聚合站，规模小、垂直领域 |

选哪个？心法：

- 找标准参考实现 → 官方仓库
- 找工作流（brainstorming / TDD / code-review）→ Superpowers
- 找代码审查 / build / lint 类工程 skill → ECC
- 找冷门垂类（量化 / 运维 / 生信）→ skill.sh / skillsmp 搜

---

## 三、Skill 文件结构

一个最小的 SKILL.md 长这样：

```markdown
---
name: skill_name_snake_case
description: <一句话：什么时候用这个 skill。一定要具体。>
---

# 标题

3-5 句话说明 skill 干什么。

## 何时触发

## 输入约定

## 步骤

## 反模式

## 示例
```

**frontmatter 的 `description` 字段最关键**——Claude 是靠这一行判断"当前对话是否需要触发这个 skill"的。一旦这行写得模糊，Claude 要么乱触发，要么根本不触发。

> 对比两个写法：
> - ❌ "代码审查工具"
> - ✅ "当用户给出一段 git diff 并要求 review 时使用——输出风险列表 + 每条风险的严重等级（P0/P1/P2）"
>
> 前者太宽泛；后者告诉 Claude 输入是什么、输出是什么、在什么时机触发。

---

## 四、动手做（10 分钟）：写 backtest skill

> 仓库已经把 backtest skill 文件都备好了——这一节我们把每个文件**逐个看一遍**，理解它们怎么协作。

### 步骤 1：看 `lesson4/project/backtest.py`

```bash
head -50 lesson4/project/backtest.py
```

`backtest.py` 是 Skill 的"底层引擎"。它做的事：

1. 从 `prices.db` 的 `ohlc` 表读历史 K 线
2. 接受一个策略 callable（约定签名：`def strategy(df) -> pd.Series`，返回 +1/0/-1 信号）
3. 计算夏普 / 最大回撤 / 胜率 / 累计收益
4. 画一条累计收益曲线，写到 `cum_BTCUSDT.png`
5. 生成约 100-150 字的中文总结
6. 返回 dict（方便 Skill 消费或 JSON 序列化）

两个关键设计点：

- **策略 callable 是参数，不是硬编码**——backtest 引擎和策略逻辑解耦，这让 Skill 可以接受任意新策略
- **用 `signal.shift(1)`**——今天的信号基于昨天的价格，避免 lookahead bias

### 步骤 2：看 `lesson4/project/.claude/skills/backtest/SKILL.md`

```bash
cat lesson4/project/.claude/skills/backtest/SKILL.md
```

重点看三处：

1. **frontmatter `description`**：写明"何时触发"（用户描述交易策略时）+ "做什么"（翻译成 callable → 调 run_backtest → 解读结果）
2. **步骤段**：把"用户自然语言策略 → Python callable → run_backtest → 解读结果"拆成 5 步，每步一句话，Claude 不需要猜
3. **反模式段**：明确告诉 Claude 不要做什么——不替用户优化策略、不引入 lookahead、不忘告诉用户 PNG 路径

### 步骤 3：看 `lesson4/project/.claude/skills/backtest/example_strategies.py`

```bash
cat lesson4/project/.claude/skills/backtest/example_strategies.py
```

两个起手模板：

- `buy_and_hold`——始终满仓做多，基线对照
- `ma_crossover_7`——收盘价高于 7 日均线时做多，否则空仓；最简单的趋势跟踪示例

Claude 在翻译用户策略时会参考这两个模板的写法（信号 +1/0/-1、用 rolling、fillna 处理 NaN）。

### 步骤 4：直接跑一次 backtest（不通过 skill）

先在 Python 层验证引擎能跑：

```bash
cd lesson4/project && python backtest.py
```

期望输出：一段中文 summary 打印到终端，类似：

```
BTCUSDT 在最近 30 根 K 线上的回测结果：累计上涨 17.37%，年化夏普 4.65，最大回撤 -4.24%，信号触发日胜率 65.52%。夏普 > 1 说明风险调整后收益尚可，配合曲线图可看到回撤分布，建议结合更长历史数据复跑确认稳健性。
PNG: /mnt/d/.../lesson4/project/cum_BTCUSDT.png
```

同时 `lesson4/project/cum_BTCUSDT.png` 应当生成（该文件已在 `.gitignore` 里，不会被提交）。

### 排错表

| 现象 | 原因 | 解决 |
|---|---|---|
| `ModuleNotFoundError: pandas` | 没装 pandas/numpy/matplotlib | `pip install pandas numpy matplotlib` |
| `ValueError: prices.db 没有 BTCUSDT 的数据` | 没跑 seed_db.py | `python seed_db.py` 后重跑 |
| `cum_BTCUSDT.png` 没生成 | matplotlib backend 问题 | 确认 `backtest.py` 里 `matplotlib.use("Agg")` 在 `import matplotlib.pyplot` 之前 |
| `sqlite3.OperationalError: no such table: ohlc` | prices.db 是空文件 | `rm lesson4/project/prices.db && python seed_db.py` |

---

## 五、动手做（5 分钟）：用 skill 跑两个策略对比

确认你在 `lesson4/project/` 目录，然后启动 Claude Code：

```bash
cd lesson4/project && claude
```

在 Claude Code 对话框里整段粘贴下面这条 prompt：

> 在 `lesson4/project/` 下启动 Claude Code 后，整段粘贴下面这条 prompt：

```
用 backtest skill 评估两个 BTC 策略：
1. buy_and_hold（始终满仓做多）
2. ma_crossover_7（close 高于 7 日均线时做多，否则空仓）

各 30 天日 K 线（symbol=BTCUSDT, interval=1d, limit=30），给我对比报告。
```

> Claude 调用 backtest skill 翻译策略 → 跑 run_backtest → 给出对比：

```
⏺ Skill(backtest) — strategy 1: buy_and_hold
  ⎿ {sharpe: 4.6545, max_drawdown: -0.0424, win_rate: 0.6552,
     cumulative_return: 0.1737, rows: 30,
     png_path: ".../.../cum_BTCUSDT.png"}

⏺ Skill(backtest) — strategy 2: ma_crossover_7
  ⎿ {sharpe: 2.2799, max_drawdown: -0.0424, win_rate: 0.6471,
     cumulative_return: 0.0451, rows: 30,
     png_path: ".../.../cum_BTCUSDT.png"}

⏺ 对比两个策略（基于真实数字撰写的中文段落，约 150-200 字）：
  
  在过去 30 天的日 K 线回测中，buy_and_hold 策略明显优于 ma_crossover_7。前者累计收益率达 17.37%，而后者仅 4.51%，领先超过 12 个百分点。在风险调整后的表现上，buy_and_hold 的夏普比为 4.65，远高于 ma_crossover_7 的 2.28，表明前者在单位风险下获得的超额收益更高。两个策略的最大回撤相同（均为 -4.24%），说明回撤风险在这一周期内没有明显差异。胜率方面，buy_and_hold 为 65.52%，ma_crossover_7 为 64.71%，两者接近，但由于后者的总体收益较低，胜率优势未能转化为绝对收益。这表明在这个样本期间，对 BTC 的简单持仓策略优于均线择时，可能由于行情持续上涨，导致频繁空仓的 ma_crossover_7 损失了收益机会。建议后续用更长历史数据、多周期验证。
```

观察三点：

- Claude 调用 backtest skill 时，**自己把策略名翻译成了 Python callable**（参考 `example_strategies.py` 的写法），你没有手动写任何 Python
- 主线对话里只有两次 Skill 调用 + 一段对比文字——**没有把 backtest.py 的代码原文 dump 出来**
- **复用而非重写**——Skill 让 Claude 把"回测能力"作为标准动作；下次你要测新策略，prompt 里直接说"用 backtest skill 评估……"即可，不需要重新解释流程

> **数字说明**：上面的 sharpe / cumulative_return 等数字是基于本课课件制作日（2026-05-05）的 BTC 行情跑出来的。你跑的时候行情已变，数字会不同——这是正常的，重要的是流程走通、各指标有数值。

---

## 六、关键认知

MCP（lesson 3）让 AI **消费**外部接口——sqlite MCP 给了 Claude "执行 SQL" 这个能力，Claude 按需调用，不调用时安静。Skill（lesson 4）让你给 AI **生产**接口——你把"如何回测一个策略"的完整流程写进 SKILL.md，Claude 看到用户意图就执行，不需要你每次解释一遍。两者互补：MCP 负责连接外部系统，Skill 负责封装可复用流程。

**Skill 不是在 Claude 里写代码，是给 Claude 一份"标准动作说明书"**。底层实现（`backtest.py`）是 Python；Skill（`SKILL.md`）是说明书，告诉 Claude 什么时候用这个工具、怎么用、用完怎么解读结果。两者分离，各自可以独立演进。

一个实用判断法则：**当一件事你做过 3 次以上，且每次流程基本不变，就值得考虑做成 Skill**。代码审查、生成 release notes、分析日志、回测策略——这类高频且结构固定的任务，都是好的 Skill 候选。

---

## 七、反模式（3 条）

**1. SKILL.md 写得太长（500+ 行手册）**

SKILL.md 是触发说明书，不是文档库。如果你把"所有可能情况"都写进去，Claude 读到一半就搞混了，触发时也会犹豫不定。保持步骤在 3-7 条，每条一句话描述动作。底层的实现细节放进 Python 代码里，Skill 里只写"调用哪个函数、传什么参数、拿什么结果"。

**2. 让 Skill 决定业务规则**

Skill 是流程封装，不是决策中心。"什么样的夏普比算好策略"是业务判断，应当在 Rule 或 prompt 里告诉 Claude，不应该硬写进 SKILL.md。比如 review skill 不该在文件里写死"100 行以内是好代码"——那是团队规范的事。Skill 只管"拿到 diff → 找风险 → 输出列表"，评判标准由你在对话里给。

**3. SKILL.md 内嵌密钥 / 私有路径**

SKILL.md 是文本文件，会被 commit 进仓库，也会被 Claude 在每次会话里读到。任何 API key、access token、内网 IP、私有路径都不要硬编码在里面。正确做法：密钥通过环境变量（`os.getenv("MY_KEY")`）或 `.env` 文件注入，SKILL.md 里只写变量名，不写值。

---

## 八、作业

> **完整任务说明**：[homework/task1-design-skill/README.md](./homework/task1-design-skill/README.md)

请**从日常工作里挑一个高频任务**设计成 SKILL.md（不要求实现，加分项实现）。30 分钟内可完成，需要提交：
1. 设计说明：3 句话说明这个 Skill 的用途、触发条件、输入输出
2. SKILL.md：按"三、Skill 文件结构"的格式写出完整 SKILL.md（参考 `lesson4/project/.claude/skills/backtest/SKILL.md` 的写法）
3. 可选加分项：把 SKILL.md 装进 `.claude/skills/<name>/SKILL.md`，实际在 Claude Code 里跑一次，提交对话截图

---

## 学完这课，你能做什么

- 用 `SKILL.md` 的 frontmatter + steps 把一个高频任务沉淀给 Claude 复用，不再每次重新解释
- 区分 Prompt / Rule / Subagent / MCP / Skill 五种扩展方式，知道什么场景用什么
- 知道 5 个 Skill 市场（官方 / Superpowers / ECC / skill.sh / skillsmp），不会从零造轮子
- 写出 description 让 Claude 准确触发，避免"写了 Skill 但 Claude 从不用它"的问题

下节课（Lesson 5）：用 OpenSpec 给 backtest 添加新策略——把"双均线策略"作为 feature 走完 proposal → specs → design → tasks → implement 全流程。Skill 会在那节课继续被消费，你会看到"造好接口"的价值在后续 lesson 里不断被兑现。（lesson5 有独立的 `lesson5/project/` 快照，不与 lesson4 共享。）

---

## 延伸阅读

- Anthropic 官方 skills 仓库：https://github.com/anthropics/skills
- Superpowers 方法论（lesson 2 已装）：https://github.com/obra/superpowers
- Everything Claude Code：https://github.com/affaan-m/everything-claude-code
- Skill 设计 best practices：https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- mcp-server-sqlite（lesson 3 用过）：https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite

