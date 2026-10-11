# 第 5 课：规则体系与 Spec 驱动开发

> 课程视频回放：[点击观看](https://appibxs98ig9955.h5.xet.pomoho.com/p/course/video/v_6a206798e4b0694c5bd0011e?product_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&course_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&sub_course_id=subcourse_3EUmreviThPpAUC2IJ1NTqoDbk5)

上节课你用 Skill 封装了 backtest 接口——让 Claude 只需要听到"帮我回测"就能调用完整流程。这节课反过来看需求那一侧：你怎么把"我要加一个新策略"表达得足够清楚，让 AI 实现的结果是你真正想要的？答案是 spec——用 OpenSpec 五段流程写一份结构化的变更文档，再把它喂给 AI，让实现阶段只负责落地。

时长约 25-30 分钟，四个主题：
1. vibe coding vs spec-driven
2. rules / guidelines / spec 三者
3. OpenSpec 五段速览
4. 动手做：完整跑一遍 add-dual-ma-strategy

> **跟着课件做**：每个"动手做"小节都有可直接复制的命令和 prompt。建议第一遍学习时**真打开终端跟着做一次**，不要只读。

---

## 〇、前置确认（30 秒）

开始前，确认以下各项：

- [ ] Claude Code 已安装（`claude --version` 能跑）
- [ ] Python ≥ 3.11（`python --version` 确认）
- [ ] `pandas`、`numpy`、`matplotlib` 已装（lesson 1 demo 用过；没装就补：`pip install pandas numpy matplotlib`）
- [ ] lesson 3 的 `prices.db` 已 seed，且含 **90 天** ohlc 数据（检查方法：`sqlite3 lesson5/project/prices.db "select count(*) from ohlc where symbol='BTCUSDT'"`，应 ≥ 90）
  - 如果只有 30 行：`cd lesson5/project && python seed_db.py` 重新拉（脚本默认拉 90 天）
- [ ] lesson 4 的 backtest engine 已就位（`ls lesson5/project/backtest.py` 能找到文件）
- [ ] **Node.js ≥ 18 + npm**（装 OpenSpec CLI 用；`node --version && npm --version` 确认）

全部打勾，继续。

### 安装 OpenSpec CLI（一次性，2 分钟）

```bash
# 全局装
npm install -g openspec

# 进 lesson5/project，初始化 OpenSpec 工件
cd lesson5/project && openspec init
```

`openspec init` 会在 `lesson5/project/` 下落 3 样东西：

| 路径 | 用途 |
|---|---|
| `openspec/config.yaml` | OpenSpec 配置（可在此写项目上下文 / 自定义规则） |
| `.claude/commands/opsx/{propose,explore,apply,archive}.md` | 4 个 slash command：`/opsx:propose` 等 |
| `.claude/skills/openspec-{propose,explore,apply-change,archive-change}/` | 4 个对应 SKILL.md |

验证安装：在 Claude Code 里输 `/opsx:propose` 看是否能被识别（不需要真触发，看到补全提示就行）。如果你跟着课程仓库走，本课 `lesson5/project/` 已经 init 过一遍，跳过 `openspec init` 那一步直接用即可。

> **不装 OpenSpec CLI 也能学**——OpenSpec 的本质是**约定**（5 段 markdown 文件），不是工具。你完全可以手写 `proposal.md / specs.md / design.md / tasks.md / IMPLEMENTATION.md`，不依赖 CLI。**CLI 是把"敲 5 个文件"压缩成"敲一行 slash command"的便利层**，本课样本 `openspec/changes/add-dual-ma-strategy/` 既能被 CLI 生成、也能被你手写——两条路殊途同归。

---

## 一、vibe coding vs spec-driven

**vibe coding 的真实失败案例**：你把"帮我加双均线策略"打进 Claude，它三分钟给了一个看起来完全正确的 Python 文件——金叉买入、死叉卖出、有中文注释、能跑不报错。但上线之后你发现：策略的 `rolling().mean()` 用的是当日 close 算出来的均线，然后当天就开仓了。这是 lookahead bias——用了当天才能知道的价格来决定当天的操作，历史回测看着漂亮，实盘一塌糊涂。另一种情况是参数默认值随 AI 心情给出：`short_window=3, long_window=5` 在过去 30 天行情里频繁抖动，但 3/5 这两个数字没有任何文档支撑。

**spec-driven 的同样需求**：你先写一份 `specs.md`，在里面明确写下："均线用 `df["close"].shift(1).rolling(N).mean()` 计算，确保信号决定时不读今日 close"；"默认 short_window=7, long_window=14"；"金叉给信号 +1，死叉给 0，其他维持上一日"。AI 拿到这份合同之后，实现就只是把这些约定翻译成代码。lookahead 防护不是"看 AI 高不高兴"，而是合同上写了的，AI 不实现就是违约。

**一句话总结**：spec 是 AI 与你之间的合同——没有合同就只能赌运气。

两种方式在代码层面的差距一目了然：

```python
# vibe coding 产物（AI 猜的，有 lookahead）
ma_short = df["close"].rolling(7).mean()     # ❌ 今天的信号用了今天的 close
signal = (ma_short > df["close"].rolling(14).mean()).astype(int)

# spec-driven 产物（合同里写了 shift(1)）
ma_short = df["close"].shift(1).rolling(7).mean()   # ✅ 只读昨日及以前
ma_long  = df["close"].shift(1).rolling(14).mean()
```

这两段代码历史回测的 sharpe 可能差距超过 2 倍——上面那段用了"作弊"数据，下面那段才是真实可部署的。spec 让这个差距变成可审计的：任何人打开 `specs.md` 都能验证实现里有没有 `shift(1)`。

---

## 二、rules / guidelines / spec 三者

三种文档各有定位，叠加使用才能让 AI 稳定输出：

| | rules | guidelines | spec |
|---|---|---|---|
| 适用范围 | 全项目 | 团队风格 | 单 feature |
| 强制度 | 高（违反 = 失败） | 中（违反 = 风格不一致） | 中（违反 = 合同纠纷） |
| 维护成本 | 低（很少改） | 中 | 高（每个 feature 一份） |
| 例子 | UTC 时间 / 中文注释 | 函数命名风格 | dual_ma 接口签名 |

> **三者协作**：rules 划底线——本项目所有代码都必须满足的硬约束（比如 UTC 时间、中文注释）；guidelines 划风格——让代码看起来像一家人写的（命名习惯、目录结构）；spec 描述具体 feature——接口是什么、边界条件是什么、不支持什么。三层叠加，AI 才能稳定输出，不靠猜。

本课的 rules 落地在 `.cursor/rules/strategy-conventions.mdc`（Cursor 的文件级自动注入规则）；spec 落地在 `lesson5/project/openspec/changes/add-dual-ma-strategy/specs.md`。两者在不同粒度上保护同一份实现。

看一下 rules 文件，感受它和 spec 的区别：

```bash
cat .cursor/rules/strategy-conventions.mdc
```

这份文件的 `globs` 匹配 `**/strategies/*.py`（覆盖任意 `lessonN/project/strategies/`）——理解其意图：每次 Claude 在编辑策略文件时，这份约束会自动注入到上下文，不需要你在 prompt 里重复说。Rules 是"设一次用永远"；spec 是"每个 feature 写一份用一次"。

---

## 三、OpenSpec 五段速览

OpenSpec 把每个 feature 拆成 5 个 markdown 文件，放在 `lesson5/project/openspec/changes/<change-id>/` 下：

| 段 | 文件名 | 干啥 | 关键问题 |
|---|---|---|---|
| ① | `proposal.md` | 提案 | 现状有什么问题？要做什么？ |
| ② | `specs.md` | 规范 | 接口怎么定义？边界条件？ |
| ③ | `design.md` | 设计 | 备选方案对比，关键技术决策 |
| ④ | `tasks.md` | 任务 | 拆成 5-10 步可执行清单 |
| ⑤ | `IMPLEMENTATION.md` | 实施记录 | 落地代码 + 与 design 的偏差 |

> **OpenSpec CLI 是可选的便利层**——这套约定本身是纯文件驱动的，`lesson5/project/openspec/` 目录里的 markdown 就是全部，你可以全程手写。但如果想用 `/opsx:propose` 这类 slash command 把"敲 5 个文件"压缩成一行，那就按 §〇 装一下 CLI。本课的实例 `lesson5/project/openspec/changes/add-dual-ma-strategy/` 两种方式产出的结构完全一致。

除了 `changes/`，还有一个 `lesson5/project/openspec/specs/` 目录——这是"项目当前长什么样"的 source of truth。每次 change 落地后，需要把 `changes/<id>/specs.md` 的接口段合并回 `specs/<相关文件>.md`，确保 `specs/` 始终反映现状（详见 §四.6）。

两个目录的关系总结为一句话：**`changes/` 是历史，`specs/` 是现在**。如果你只能维护一个，维护 `specs/`——因为下一个人（包括下一个 AI session）第一眼看的是 `specs/`，不是 `changes/`。

先快速看一下目录结构确认文件都在位：

```bash
ls lesson5/project/openspec/changes/add-dual-ma-strategy/
```

期望看到：`proposal.md  specs.md  design.md  tasks.md  IMPLEMENTATION.md`（五段全齐）。

---

## 四、动手做（约 18 分钟）

跟着课堂的 `add-dual-ma-strategy` change 走一遍五段全流程。每段下面给你**直接看实物文件**的命令 + 关键摘要 + 观察点。

### 4.1 proposal.md（≈ 3 min）

打开看：

```bash
cat lesson5/project/openspec/changes/add-dual-ma-strategy/proposal.md
```

5 行核心：

> lesson 4 backtest skill 已就绪，但 `lesson5/project/strategies/` 里只有 buy_and_hold / ma_crossover_7 两个 example。buy_and_hold 是基线，没有交易决策；ma_crossover_7 是单条均线突破，没有"反转信号"。**提案**：实现双均线交叉策略 `dual_ma`——短均线（7 日）上穿长均线（14 日）给信号 `+1`（做多），下穿给信号 `0`（空仓），其他维持上一日。

观察：proposal 不写代码细节，只写"现状缺什么"和"要解决什么"。一个好的 proposal 30 秒内读完就能抓到痛点。

注意文件里还有"影响范围"和"验收"两段——影响范围告诉协作者"会动哪些文件"，验收告诉 AI"怎么判断做完了"。这三段加起来就是一个完整的 proposal：为什么做、做什么、怎么算完。

### 4.2 specs.md（≈ 4 min）

```bash
cat lesson5/project/openspec/changes/add-dual-ma-strategy/specs.md
```

接口段：

```
dual_ma(df: pd.DataFrame, short_window: int = 7, long_window: int = 14) -> pd.Series
值 ∈ {0, +1}（不做空）
```

信号规则表：

| 状态 | 当日信号 |
|---|---|
| 金叉（短上穿长：`ma_s > ma_l` 且昨日 `ma_s ≤ ma_l`） | `+1` |
| 死叉（短下穿长：`ma_s < ma_l` 且昨日 `ma_s ≥ ma_l`） | `0` |
| 其他（持仓维持） | 与昨日信号相同 |

防 lookahead：均线用 `df["close"].shift(1).rolling(N).mean()` 计算，**只读昨日及以前**。

观察：specs 段是"AI 与你之间的合同"。每条都**可验证**（什么状态 → 什么信号，白纸黑字），不是"AI 你看着办"。

还注意文件里有"不支持"段：明确写出"做空返回 -1 不支持"——这和"支持 +1"一样重要。告诉 AI 哪些**不做**，能防止 AI 过度实现（auto-generalize），加了一堆你不需要的功能。

### 4.3 design.md（≈ 3 min）

```bash
cat lesson5/project/openspec/changes/add-dual-ma-strategy/design.md
```

备选方案对比：

| 方案 | 实现复杂度 | 教学清晰度 | 选择 |
|---|---|---|---|
| A. close vs MA（简单突破） | 低 | 高，但和 lesson 4 ma_crossover_7 雷同 | ❌ |
| B. 短 MA vs 长 MA（金叉死叉，本提案） | 中 | 高，经典量化教科书例 | ✅ |
| C. MACD（DIF/DEA） | 高 | 高，但额外引入 EMA 概念，超出 25 min | ❌ |

关键决策——**两层防御 lookahead**：策略层 `shift(1)` + backtest 层 `signal.shift(1)` 各一次，两层叠加确保不读未来数据。选 B 的原因：不与 lesson 4 已有 example 重复，且不超出 25 分钟教学范围。

观察：design 是给后人看的"why we chose this"——任何一个决策选了 B 没选 A，必须写清楚为什么。三个月后的你看这份文件，不需要猜"当时为啥这么做"。

注意 design 里明确记录了"两层防御 lookahead"——这个决策在 specs 里只说了"用 shift(1)"，但没有解释"为什么是两层"；design 补全了这个 why，让代码审查者知道策略层的 shift(1) 和 backtest 层的 shift(1) 各司其职，不是重复。

### 4.4 tasks.md（≈ 2 min）

```bash
cat lesson5/project/openspec/changes/add-dual-ma-strategy/tasks.md
```

6 步 todo 清单：

```
[x] 1. 在 lesson5/project/strategies/__init__.py 导出 dual_ma
[x] 2. 写 lesson5/project/strategies/dual_ma.py（函数签名 + design 骨架 + 中文注释）
[x] 3. 跑自测：python strategies/dual_ma.py 无 traceback
[x] 4. 把 specs.md 接口段合并到 lesson5/project/openspec/specs/strategies.md
[x] 5. 写 IMPLEMENTATION.md，记录实施日期、数字、与 design 偏差
[x] 6. 提交 commit
```

观察：tasks 是"做的人的视角"——每行都是一个动作（写 X / 跑 Y / 改 Z），不是"设计说明"。AI 拿到这份清单，直接按序执行，不需要猜下一步该干什么。

六步清单里有两步是"非代码工作"（第 4 步合并 specs、第 5 步写 IMPLEMENTATION.md）——这是 OpenSpec 流程强制要求的：实现不只是写代码，还要维护文档状态。这两步如果跳过，specs/ 就会滞后，下一个人就会看到过时的信息。

### 4.5 implement（≈ 4 min）

打开实现：

```bash
cat lesson5/project/strategies/dual_ma.py
```

约 50 行 Python，核心 10 行（短/长均线计算 → 金叉死叉信号 → ffill 持仓维持）：

```python
ma_short = df["close"].shift(1).rolling(short_window).mean()
ma_long  = df["close"].shift(1).rolling(long_window).mean()
ma_short_prev = ma_short.shift(1)
ma_long_prev  = ma_long.shift(1)
cross_up = (ma_short > ma_long) & (ma_short_prev <= ma_long_prev)
cross_dn = (ma_short < ma_long) & (ma_short_prev >= ma_long_prev)
sig = pd.Series(np.nan, index=df.index)
sig[cross_up] = 1.0
sig[cross_dn] = 0.0
sig = sig.ffill().fillna(0).astype(int)
```

现在跑一次自测（**注意：必须用 `limit=90`，默认 limit=30 在强趋势行情里可能全程无金叉，输出 sharpe=0**）：

```bash
cd lesson5/project && python -c "from strategies import dual_ma; from backtest import run_backtest; print(run_backtest(dual_ma, limit=90)['summary'])"
```

期望输出（你的数字会和这里相近，行情每天变动正常）：

```
sharpe=1.1563  max_dd=-0.0938  win_rate=0.5870  cum=0.0911
BTCUSDT 在最近 90 根 K 线上的回测结果：累计上涨 9.11%，年化夏普 1.16，最大回撤 -9.38%，信号触发日胜率 58.70%。夏普 > 1 说明风险调整后收益尚可，配合曲线图可看到回撤分布，建议结合更长历史数据复跑确认稳健性。
```

观察：dual_ma 在过去 90 日累计 +9.11%，输给 lesson 4 的 buy_and_hold（+17.37%），但夏普 1.16 仍然 > 1，回撤 -9.38%——这就是"反转策略在强趋势行情里通常跑不赢简单持仓"的经典现象。buy_and_hold 在 BTC 单边上涨时无从超越，但 dual_ma 的优势在于震荡行情里能空仓规避回撤。

### 排错表

| 现象 | 原因 | 解决 |
|---|---|---|
| 输出 `sharpe=0.0000 cum=0.0000` | 默认 limit=30 且强趋势行情无金叉，全程 0 信号 | 改用 `run_backtest(dual_ma, limit=90)` 显式传 90 天 |
| `ValueError: prices.db 没有 BTCUSDT 的数据` | seed_db.py 未跑或数据库为空 | `cd lesson5/project && python seed_db.py` 重新拉 |
| `from strategies import dual_ma` 报 ImportError | `__init__.py` 未导出 | 检查 `lesson5/project/strategies/__init__.py` 是否有 `from .dual_ma import dual_ma` |
| `ModuleNotFoundError: numpy` / `pandas` | 依赖未安装 | `pip install pandas numpy matplotlib` |
| `sqlite3.OperationalError: no such table: ohlc` | prices.db 是空文件 | `rm lesson5/project/prices.db && python seed_db.py` |

### 4.6 merge specs.md（≈ 2 min）

变更落地后，把 `changes/add-dual-ma-strategy/specs.md` 的接口段**合并**到 `lesson5/project/openspec/specs/strategies.md`，让 `specs/` 始终反映"项目当前长什么样"：

```bash
cat lesson5/project/openspec/specs/strategies.md
```

应该看到"当前已实现的策略"段已经从"暂无"更新为：

| 名称 | 文件 | 简介 |
|---|---|---|
| `dual_ma` | `lesson5/project/strategies/dual_ma.py` | 双均线交叉，short=7 / long=14，金叉做多，死叉空仓 |

观察：`specs/` 是"现状的 source of truth"；`changes/` 是"变更日志"。两者要勤同步——`specs/strategies.md` 是下一个加策略的人的第一份参考，如果这里永远写"暂无"，就没有价值了。

---

## 五、关键认知

**spec 是合同**：把"我以为我说清楚了"变成"白纸黑字"。vibe coding 失败的根本原因不是 AI 不够聪明——而是需求本身就是模糊的，AI 凭概率猜你的意思，猜对了就是好结果，猜错了就是 lookahead bias。

写 spec 的过程本身就是在逼你想清楚：接口入参是什么？出参值域是什么？边界情况怎么处理？这些问题你必须回答，AI 才能照着做。

**rules 是底线**：违反就报警的硬约束，和任何一个 feature 无关。UTC 时间、中文注释是整个项目的规定，写进 `.cursor/rules/` 之后，每次 Claude 修改 `strategies/*.py` 时都会自动看到这份约束，不需要你在每条 prompt 里重复"记得用 UTC"。

rules 的价值在于：你只需要说一次，它就永远有效。

**guidelines 是味道**：让代码看起来像一家人写的。函数命名风格、目录结构约定、注释格式——这些不影响正确性，但影响可维护性。rules 划底线，guidelines 划风格，spec 描述具体 feature——三层叠加，AI 的输出才能从"看着对"升级到"系统性可信"。

三层文档的维护成本也是分层的：rules 你写一次很少改（UTC 时间约定三年不变）；guidelines 跟着团队规范慢慢演化；spec 则是每个 feature 一份，feature 交付后归档到 `changes/`，不需要持续维护。

这个分层设计让你把精力花在刀刃上——只在真正需要约束的粒度上写文档，不做无用功。

---

## 六、反模式（3 条）

**1. 把 spec 写成 200 行的功能手册**

spec 是合同不是百科全书。一个 feature 的 `specs.md` 通常 30-80 行就够——接口签名、行为细则、边界条件、不支持的内容，这些写完基本就是 50 行。如果你发现自己在写第 100 行，停下来问：这是在描述接口，还是在描述实现细节？实现细节属于 `design.md`；"使用场景说明"属于 `proposal.md`。写太多的 spec 和没有 spec 一样有害——AI 读到一半就迷失，你也不知道哪句话是核心约束。

**2. implement 完了不更新 specs/**

`specs/` 是现状的 source of truth；`changes/` 是变更日志。如果你每次 change 实施完都不更新 `specs/`，那 `specs/strategies.md` 永远写着"暂无策略"，下一个要加策略的人打开这份文件拿不到任何信息，只能去翻 `changes/` 里所有变更找现状。同步 `specs/` 的成本很低（通常是改几行表格），但价值是让整个目录始终可信。

**3. 把 spec 当审计而不是沟通工具**

spec 是给同事和 AI 看的"我接下来要做什么"——是沟通文档，不是合规证明。如果你写得像"本系统应当符合 ISO 标准第 X 条第 X 款，实现结果应满足行业规范……"，那 AI 读了也只能机械应付，不会帮你抓边界 case，不会在 design 阶段提出"你有没有想到 NaN 怎么处理"。好的 spec 用第一人称、说人话："输入行数不够时返回全 0"——这句话 AI 能直接翻译成 `if len(df) < long_window: return pd.Series(0, index=df.index)`。

---

## 七、作业

> **完整任务说明**：[homework/task1-spec-flow/README.md](./homework/task1-spec-flow/README.md)

在 `lesson5/homework/` 下选一个 feature（RSI 反转策略 / MACD / 布林带突破 / 年化收益率输出 / 多周期回测，任选其一或自选），按 OpenSpec 五段写一遍。30 分钟内可完成，**不要求实现底层代码**（实现是加分项）。

作业的核心是练习"先写合同再动手"的节奏——从 proposal 开始，逼自己在写代码之前先把接口、边界、备选方案、任务顺序都想清楚。你会发现，写 spec 最费时的地方往往是你认为"已经想清楚"的那些细节。

提交内容：新建 `lesson5/homework/<feature-name>/` 目录，包含 `proposal.md`、`specs.md`、`design.md`、`tasks.md` 四份 markdown（IMPLEMENTATION.md 可选，实现代码放在 `lesson5/project/openspec/changes/<feature-name>/` 目录）。

---

## 学完这课你能做什么

- 区分 rules / guidelines / spec，知道什么场景写哪个，三层叠加怎么协作
- 用 OpenSpec 五段（proposal → specs → design → tasks → implement）为一个 feature 写完整 spec 文件
- 把 spec 当成 AI 的输入合同，让 implement 阶段只负责落地，不再靠猜
- 知道 `specs/` 与 `changes/` 的同步约定，维护项目当前状态的 source of truth

下节课（Lesson 6）：spec 解决 What，Harness 解决 How to keep going——我们用 superpowers 的 writing-plans + executing-plans 跑一个跨上下文的多周期回测长任务。

---

## 延伸阅读

- 课堂完整 change（五段全文 + 实施记录）：`lesson5/project/openspec/changes/add-dual-ma-strategy/`
- OpenSpec 概念：[GitHub - openspec](https://github.com/anthropic-spec/openspec)（如可达）
- Spec-Driven Development 综述：[Anthropic Engineering Blog](https://www.anthropic.com/engineering/claude-code-best-practices)
- 本课用到的 Cursor rule：`.cursor/rules/strategy-conventions.mdc`
- OpenSpec 工作目录说明：`lesson5/project/openspec/specs/README.md`
