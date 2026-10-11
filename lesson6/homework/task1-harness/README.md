# 任务 1：写一份 plan，跑过一次 `/clear` 续接（必做）

## 时长

30 分钟内可完成。**不要求长任务**——3-5 step 的 mini plan 足以演示 harness 纪律。

## 目标

练习 harness 的四个动作：**init → execute → checkpoint → handoff**。任务长度不重要，重要的是：
- 你写的 plan 真的拆到了原子 step（每一步一个具体动作）
- 跑到一半你**真的执行 `/clear`**（不是关掉窗口）
- `/clear` 之后的新会话**只读 plan + HANDOFF** 就能续上，不需要回问"我之前做了什么"

## 候选任务（任选一个，或自选）

下列三个都满足"3-5 step + 中途可暂停"的特征——选一个开始：

| 方向 | 适合人群 | 大致 step |
|---|---|---|
| 把仓库里所有 `README.md` 翻译成英文 | 想练 plan + 文件批处理 | 按文件分批，每批一个 step |
| 把 lesson 4 的 backtest 在更多 sample 策略上复跑（lesson4/project/strategies/ 里有 buy_and_hold、ma_crossover_7） | 想练 plan + 数据回填（最贴近课堂） | 每 1-2 个策略一个 step，结果存到 plan 表 |
| 把一个长函数重构成 4 个小函数 | 想练 plan + 渐进式重构 | 每次重构一个，跑测试验证后再继续 |

自选任务也可以，但必须满足：**至少 3 个独立 step + 每个 step 产出可写到 plan**。

## 步骤

### Step 1：复制 plan 模板

```bash
cp lesson6/homework/task1-harness/PLAN.md.template ~/my-harness-plan.md
```

把 `~/my-harness-plan.md` 改名 + 改路径都行，关键是有一份属于你自己的 plan 文件。

### Step 2：填 plan

按模板里的 Goal / Architecture / Tech Stack 三段，加上 3-5 个 Step——每一步都要包含：
- 具体命令（可粘贴）
- 期望产出（数字 / 文件 / 输出片段）
- 验收方式（怎么算这一步完成）

模板里的 `<...>` 占位都换成你的真实内容。

### Step 3：在 Claude Code 里跑前一半

打开 Claude Code，**第一句**说：

```
读我的 plan 文件 ~/my-harness-plan.md（路径换成你的），按 plan 跑第一步，跑完之后回填 plan 文件，然后停下来。
```

让 AI 跑 1-2 step。每跑完一步，**确认 plan 文件被修改了**（数字 / 状态 / `[x]` 都填好了）——这一步是核心，跳过这一步整个作业作废。

### Step 4：写 HANDOFF.md，然后 `/clear`

在 plan 同目录下新建 `HANDOFF.md`，参考课堂样本（`lesson6/project/plans/HANDOFF.md`），包含：

- **Status**：一句话进度
- **已记录的关键数字/产物**：列出来
- **Next prompt**：一段**整段可粘贴**的下一会话开场白

然后在 Claude Code 输入：

```
/clear
```

**真的 `/clear`**——不是关 UI，是清上下文。

### Step 5：新会话续上

粘贴你刚才在 HANDOFF 里写的 Next prompt。观察 AI 的反应：

- ✅ 它直接读你的 plan 和 HANDOFF，找到第一个 `[ ]` 行，开始干
- ❌ 它回头问"我们之前在做什么"——说明 HANDOFF 写得不够具体，重写

跑完剩下的 step，每一步都**回填 plan**。

### Step 6：提交

把以下两样放到 `lesson6/homework/task1-harness/<你的名字>/` 下：

1. `PLAN.md`（最终版，全部 `[x]`）
2. `REFLECTION.md`——200 字感受：
   - 续上的体验如何？
   - Plan 写到多详细才够？哪一步你低估了？
   - 如果让你再做一次，你会先做什么准备？

## 评分维度

| 维度 | 怎么算合格 |
|---|---|
| Plan 原子度 | 每个 step 都有具体命令 + 验收，不需要额外解释 |
| 回填纪律 | 每 step 完成后，plan 文件**当下**就更新了 |
| /clear 后无缝续接 | 新会话**没有回头问**"之前在做什么" |
| 完成态 plan 可读 | 别人打开 plan 能复盘"做了什么、产出是什么" |

## 参考

- 课堂完整样本：`lesson6/project/plans/multi-period-backtest.md`
- 课堂 HANDOFF 样本：`lesson6/project/plans/HANDOFF.md`
- 课堂 report 样本：`lesson6/project/reports/multi_period.md`
- Superpowers writing-plans skill（lesson 2 已装）：在 Claude Code 里输 `/superpowers:writing-plans`

## 常见问题

**Q: 我没有合适的任务可练怎么办？**
A: 选最朴素的——"把 lesson 6 README.md 翻译成英文，每 3 段为一个 step"。这就足够练完整流程。

**Q: 跑到一半发现 plan 没拆好怎么办？**
A: 暂停、改 plan、再继续。修改 plan 本身是 harness 的合法动作——但每次改完都要把改动 commit 到 git，让历史可追溯。

**Q: `/clear` 之后 AI 真的不记得了吗？**
A: 真的不记得。如果你看到 AI 在 `/clear` 之后还能引用之前对话的细节，说明你没真清掉——可能只是新开了一个 tab。`/clear` 必须**在同一个对话窗口里输入**。
