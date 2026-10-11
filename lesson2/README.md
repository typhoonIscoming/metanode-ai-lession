# 第 2 课：Claude Code × Cursor 高级技巧

> 课程视频回放：[点击观看](https://appibxs98ig9955.h5.xet.pomoho.com/p/course/video/v_6a1c5563e4b0694c5bcddab0?product_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&course_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&sub_course_id=subcourse_3EUmreviThPpAUC2IJ1NTqoDbk5)

第 1 课讲了"工具地图 + 20 条基础技巧"，这一课往进阶走：**让工具替你做更多事，而不是你不停指挥工具**。

时长约 30 分钟，四个主题各 6–7 分钟。

> **跟着课件做**：每节都有"**动手做（X 分钟）**"的小节——直接复制命令、粘贴 prompt 就能跑。建议第一遍学的时候**真打开终端跟着做一次**，不要只读。

---

## 一、Subagents：派分身干脏活，主线只接收摘要

### 动手做（3 分钟）

**前置**：在仓库根目录启动 Claude Code

```bash
cd <你克隆 ai_lesson 仓库的位置>
claude
```

**步骤 1**：把下面这句话**完整粘贴**到 Claude Code 主线对话里，回车。

```
派一个 explore subagent 去摸底 lesson1/demo/ 的结构，
返回 10 行以内的摘要，不要贴源码原文。
```

**步骤 2**：屏幕上你会看到一个**折叠框**（不是一长串 Read 调用）：

```
⏺ Task(subagent_type=Explore)
  ⎿  [一段 8-10 行的摘要，文件清单 + 结构判断]
```

**步骤 3**：观察三个关键点 ——

- 主线**只显示一个 Agent 调用框**，不是 5 个 Read
- 摘要里**只有结论**，没有源代码原文
- 你的主对话上下文**没有被几千 token 文件内容污染**——下一轮还能干别的事

**对比一下**：试着说"读一下 lesson1/demo/ 然后告诉我结构"（**不**用 subagent），观察主线会跑一串 Read 调用、屏幕被刷得很长。这就是为什么需要 subagent。

### 这是什么

Claude Code 干 20 分钟之后会变笨——读了 50 个文件之后，它对最初的目标已经记不清了。Subagent 解决这个问题：**把一个独立任务派到一个全新的上下文里跑，结束后只把结论返回主线**。

### 三种典型用法

| 用法 | 干什么 | 例子 prompt |
|---|---|---|
| 探索 | 代码库摸底，不污染主线 | [`prompts/explore-codebase.md`](./demo/01-subagents/prompts/explore-codebase.md) |
| 审阅 | 独立第二意见，避免 AI 给自己写的代码"打高分" | [`prompts/review-diff.md`](./demo/01-subagents/prompts/review-diff.md) |
| 研究 | 外部信息汇总，主线不被参考资料淹没 | [`prompts/research-libs.md`](./demo/01-subagents/prompts/research-libs.md) |

### 铁律：Prompt 必须自包含

Subagent **看不到主线上下文**。写 prompt 时目标 + 背景 + 关注点 + 输出格式 **全部写进去**。

```
❌ "审阅刚才那个函数"          ← 它不知道"刚才"是哪个
✅ "审阅 src/auth/login.ts 中的 verifyToken。
    背景：JWT 校验入口，被 5 个 API 调用。
    重点：时间常数比较 / 过期时间 / 错误信息泄露。
    输出：风险列表 + 严重等级"
```

### 项目级配置（团队共享）

把常用的 subagent 角色固化进 `.claude/agents/<name>.md`，提交进 git——见范例 [`code-reviewer.md`](./demo/01-subagents/.claude/agents/code-reviewer.md)。

### 反模式

- ❌ 派 subagent 去做顺手就能干的小事——分身启动开销 > 自己干
- ❌ 把 subagent 当"省 token"工具——返回 200 行垃圾摘要不如自己读
- ❌ Prompt 里写"刚才那个函数"——分身没有"刚才"的概念

---

## 二、Hooks：把"每次都得做"变成自动执行

### 动手做（5 分钟）

**前置**：本仓库已经把完整的三事件 hook 配置放在 `.claude/settings.json` 里了，你直接克隆下来就能用，**不需要拷贝任何文件**。如果之前跟着练过、改脏过样本，先还原：

```bash
git restore lesson2/demo/02-hooks/samples/bad_format.py
```

**步骤 1**：在 `ai_lesson` 仓库根目录**新开**一个 Claude Code 会话——hook 只在会话启动那一刻加载，旧会话不会回溯生效。

```bash
cd <你克隆 ai_lesson 仓库的位置>
claude
```

**步骤 2**：验证 `SessionStart` 已生效——会话启动时屏幕上应当能看到这一段（hook 的 stdout 被注入到 Claude 的上下文）：

```
SessionStart:resume hook success: --- 当前 git 状态 ---
 ...
--- 当前分支 ---
main
--- 最近 3 次提交 ---
...
```

> 看不到这段，说明 hook 没生效——通常是你在已开会话里改了 settings，必须**新开**会话；或者是 JSON 写坏了，可以用 `claude --debug` 启动看 hook 报错。

**步骤 3**：在新会话里**整段粘贴**下面这条 prompt，触发 PostToolUse 自动修复闭环：

```
把 lesson2/demo/02-hooks/samples/bad_format.py 里的 calculate_total
函数实现改成：输入是 list[dict]，每项有 price 和 quantity 字段，
返回总金额。
```

**步骤 4**：盯紧屏幕，观察这个序列（**最戏剧性的一段**）——

1. Claude 用 `Edit` 改文件 → 屏幕显示 Edit 调用框
2. **紧接着自动出现** `[hook] ruff 检查 lesson2/demo/02-hooks/samples/bad_format.py` 的输出 → **hook 在跑**
3. ruff 把 `import os` / `import sys` 这类未使用 import 直接 `--fix` 删掉，剩余风格问题以诊断信息回流到对话——Claude 看到后**主动再发一次 Edit / Read** 把状态对齐，**你没有催它**

**0 次人工干预，AI 自己闭环。**

**步骤 5**：练完想还原样本文件方便下次再练，**不要动 `.claude/settings.json`**（它是仓库的一部分）：

```bash
git restore lesson2/demo/02-hooks/samples/bad_format.py
```

### 这是什么

`.claude/settings.json` 里配一段 hook，Claude Code 在指定事件触发时**强制执行** shell 命令——AI 不能跳过。

跟 subagent 的区别：**subagent 是主动派遣，hook 是被动触发**。

### 三个最常用的事件

| 事件 | 触发时机 | 典型用途 |
|---|---|---|
| `SessionStart` | 会话启动 | 注入 git status + 当前分支 + 最近提交 |
| `UserPromptSubmit` | 用户提交 prompt 前 | 预处理输入 / 注入项目状态 |
| `PostToolUse` | 工具调用结束后 | Edit 完跑 lint / Bash 完记日志 |

完整三事件配置示例见 [`settings.json`](./demo/02-hooks/settings.json)。

### 关键认知：Hook 输出回到对话里

这不是副作用，**这是 feature**——你不是在写自动化脚本，**你是在给 AI 装传感器**。lint 报错被 AI 看到 → 它自动再发一次 Edit 修。

### 反模式

- ❌ 在 `PostToolUse` 里跑全项目测试——每次 Edit 都等几十秒，体验崩
- ❌ hook 输出动辄几百行——污染主线上下文
- ❌ 用 `exit 1` 阻塞工具调用——除非真的需要

---

## 三、Cursor 进阶：Composer + Background Agents + 分层 Rules

### 动手做（3 分钟）

> ⚠️ **这一节切到 Cursor**，不是 Claude Code。

**步骤 1**：在 Cursor 里打开 `ai_lesson` 仓库根目录（File → Open Folder）。

**步骤 2**：按 `Ctrl+I`（Mac 是 `Cmd+I`）启动 Composer 面板。

**步骤 3**：打开 [`demo/03-cursor-advanced/composer-task.md`](./demo/03-cursor-advanced/composer-task.md)，**复制文件中两个 `---` 之间的任务正文**（不含 markdown 标题，也不含末尾的 cleanup 段），粘到 Composer 输入框，回车。

**步骤 4**：观察 Composer 的反应——

- 它先列出"会动到的文件清单"：`lesson1/demo/claude-demo/btc_kline.py`、`lesson1/demo/cursor-demo/btc_kline.py`、`lesson1/README.md`
- 然后给出**跨文件 diff**，每个文件一段，逐个 review
- **关键：不要点 Apply / Accept All**——这一步只是体验流程。看完直接关掉 Composer 或点 Reject

> 这就是 Composer 和 `Ctrl+K` 的核心差异：Ctrl+K 只改你选中那段；Composer 跨文件 + 自己定位 + 自己改。

**步骤 5**：在 Cursor 左侧文件树打开 `.cursor/rules/project-conventions.mdc`，看 frontmatter 第一行 `alwaysApply: true`——这就是"每次对话都注入"。

再打开 [`demo/03-cursor-advanced/rules-examples/`](./demo/03-cursor-advanced/rules-examples/) 下三个 `.mdc` 文件，对比 frontmatter 差异——一个是 `alwaysApply`、一个是 `globs:`、一个是手动调用，三种生效方式一眼对照。

> ⚠️ `rules-examples/` 下的文件**不要**移到 `.cursor/rules/`——只是样本，移过去会真的生效。

### 三件武器各自的定位

**Composer（Ctrl+I）多文件 Agent**：跨文件改动用它。`@文件夹` / `@docs` / `@git` 添加上下文。

**Background Agents**：把长任务（200 个组件批量重构）丢到 Cursor 云端跑。**本课不实操**——要登录后台 + 跑 5+ 分钟，时长不允许。

**`.cursor/rules/` 分层**：

| 类型 | 何时生效 | 适合 |
|---|---|---|
| `alwaysApply: true` | 每次对话 | 全局编码规范、UTC 约定 |
| `globs:` | 编辑匹配文件时 | 语言 / 框架特有规则 |
| 手动 `@rule-name` | 显式 @ 调用 | 不常用的提示模板 |

### 关键认知

> **全部 alwaysApply 等于全部都不重要**。真正高频的规则才放 alwaysApply，按场景的用 globs，偶发的留 manual。

### 反模式

- ❌ 把 Composer 当万能锤——跨文件改动用它，单点问答用 `Ctrl+L`
- ❌ rules 写成几百行规章制度——AI 不会记得，5–10 条铁律即可

---

## 四、Plugins 生态：装一个，用一个

### 前置：装好 Superpowers

> 切回 **Claude Code**。这一节是 Claude Code 独有，Cursor 没有对应物。

在 Claude Code 里输入：

```
/plugin
```

进入插件管理器，按提示添加 Superpowers marketplace 并安装 `superpowers` 插件。装完后在斜杠菜单（输入 `/` 时弹出）里能看到 `/superpowers:brainstorming` 这一类命令，就说明就绪。

> marketplace 拉取 + 插件下载有时会等几十秒，**建议上课前先装好**，避免课堂上等下载。

### 动手做（4 分钟）—— 反例 vs 正例对比

**步骤 1**：跑**反例**——不走 skill。先清上下文：

```
/clear
```

然后整段粘贴：

```
我想给 lesson1/demo/claude-demo/btc_kline.py 加一个新功能——
支持同时绘制多个币种的 K 线对比图。帮我加一下。
```

**观察**：AI 大概率第 1–2 轮就开始动手 Edit 代码，**没问**"对比哪些币种 / 叠加还是子图 / 时间窗对齐"。等它写出第一段代码就**主动喊停**——这一步不是要让它真把功能做完，重点是体会"**它没问需求边界，它在猜你想要什么**"这件事。

**步骤 2**：跑**正例**——走 brainstorming skill。先清上下文：

```
/clear
```

然后整段粘贴（**注意第一行就是 skill 触发命令**）：

```
/superpowers:brainstorming

我想给 lesson1/demo/claude-demo/btc_kline.py 加一个新功能——
支持同时绘制多个币种的 K 线对比图。
```

**观察**：AI **不动手**，先问收敛性问题——例如"对比哪些币种？固定还是用户传参？" / "叠加还是子图？" / "现有单币种功能要不要保留？"。等需求清楚了才进入实现。**这就是 skill 的强制流程在起作用。**

跟着 AI 走 2–3 轮问答就够了，**不必真把功能实现完**——重点是体会两条轨迹的差异。

**步骤 3**：练完无需清理——`/clear` 已经把上下文丢掉了，没有文件改动。

### 这是什么

> **Plugin 不是给你多十个工具，是给你多十种思维范式**。每个 skill = "高水平工程师的标准动作"，你不用自己摸索。

两个明星生态：

- **Everything Claude Code (ECC)**：增强包——优化的 agent 配置 + 一组专用 skill
- **Superpowers**：方法论框架——brainstorming / TDD / systematic-debugging / code-review 等 skill，**每个 skill 都是一套强制流程**

### 关键认知

强制走流程的代价是"刚开始觉得啰嗦"，收益是"避免和 AI 一起 vibe coding 跑偏 30 分钟"。

### 关于 Cursor

> Plugins 是 Claude Code 独有能力，Cursor 没有直接对应物。

### 反模式

- ❌ 装一堆 plugin 但从不调用——调用入口是 `/plugin:skill-name`，不熟就废了
- ❌ 把 skill 当死规则——它强制流程是好事，但**判断"这个流程适不适合当前任务"是你的责任**

---

## 五、作业

两件小事，加起来 30 分钟内能搞定。**不要求写新代码**。

### 任务 1：跑通一次 Bash 命令记录 hook（必做）

仓库已经在 [`lesson2/homework/task1-hook/`](./homework/task1-hook/) 备好一份 PostToolUse hook —— **每次 AI 跑 Bash 命令都会自动记一行**，回显到对话里 + 落盘到 `bash-history.log`。**你不用自己写**。

1. **进入**子目录：`cd lesson2/homework/task1-hook`
2. **在该目录下**启动 Claude Code（hook 只在该目录的 `.claude/settings.json` 生效）
3. 让 Claude 跑 3 条命令，整段粘贴：
   > 请独立分别跑：`git status --short`、`ls`、`echo hello`
4. **观察**：每跑一条 Bash，对话里立刻出现一行 `[bash-log] <UTC 时间>  <命令>`
5. 退出 Claude（`Ctrl+D`）后跑 `cat bash-history.log`，看持久化的 TSV 日志
6. **提交**：对话片段（含三条 `[bash-log]` 输出）+ **2 句话**写你看到了什么

> 完整 walkthrough + 排错表见 [`task1-hook/execution-record.md`](./homework/task1-hook/execution-record.md)。
>
> 练完 `rm -f lesson2/homework/task1-hook/bash-history.log` 清理（已在 `.gitignore` 里，不删也行）。

### 任务 2：派一个 Subagent 审阅一段你自己的代码（必做）

挑一段**你最近写的真实代码**（哪个项目都行，几十行就够），派一个 subagent 独立审阅。

提交三样：

1. **Prompt**：完整粘出你派给 subagent 的 prompt（必须自包含——目标 + 背景 + 重点 + 输出格式都写进去）
2. **结果**：subagent 返回的原文
3. **3 句话判断**：哪条最值得做？哪条你不会采纳？为什么？

> 重点不是"派了 subagent"这个动作，而是 **怎么对待它返回的建议**。Subagent 不是法官，是同事。3 句话写不出取舍的，等于没派。

### 加分项（可选）

**扩展 task1-hook 的 hook**：在必做任务的 `log-bash.sh` 基础上加点料，提交修改后的文件。点子任选其一：

- **扩展 matcher** 到 `Edit|Write|MultiEdit`，让脚本也记录 AI 改了哪些文件
- **危险命令拦截**：识别到 `rm -rf` / `git push --force` 等命令时 `exit 1` 阻断（PreToolUse hook）
- **敏感词脱敏**：命令里出现 `aws_*` / `gcloud` / `token=` / `Bearer ` 等关键词时记成 `[REDACTED]` 而不是原文

参考实现见 [`homework/task1-hook/execution-record.md`](./homework/task1-hook/execution-record.md) §8 "把它当模板搬到自己的项目"。

[`homework/task2-subagent-review/`](./homework/task2-subagent-review/) 是任务 2 的深度参考（含逐条判断），同样**不要求模仿那个深度**。

---

## 学完这课，你能做什么

- 在主线干活时随手 `派一个 explore subagent` 摸底陌生代码，主线不被刷屏
- 给项目加 PostToolUse hook，写完代码自动 lint，AI 看到错误自我修复
- 用 Composer 一次跑跨多文件的重构
- 装上 Superpowers，遇到"想加个新功能"先走 `brainstorming` skill 把需求收敛再动手

---

## 延伸阅读

- Claude Code 官方文档（subagents / hooks / plugins 章节）
- Cursor 官方文档（Composer / Background Agents / Rules 章节）
- Superpowers 仓库（搜索 GitHub `claude superpowers`）
