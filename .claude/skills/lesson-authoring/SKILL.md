---
name: lesson-authoring
description: Use when creating, updating, or auditing course materials for "AI 驱动的软件开发提效实战课" — lessonN/README.md (学员讲义), 讲稿.md (讲师口播稿), lessonN.pptx (课件), lessonN.pdf, demo/, homework/. Triggers on "写第 N 课", "做 lesson X 的讲义/讲稿/PPT", "整理这一课的作业", "把课件 build 出来", or any structural change to lesson1..10 artifacts.
---

# Lesson Authoring（项目维度）

## Overview

本课程每一课交付 5 个紧耦合产物（README / 讲稿 / pptx / pdf / demo+homework），它们必须风格一致、内容呼应、可追溯到 `plan_v2.md` 的目标。本 skill 把"怎么造一课"压成一条可执行的流水线，让任何会话拿到题目都能产出与 lesson3/lesson5 同等质量的输出。

**核心原则**：三条主轴同源同节奏。

| 轴 | 受众 | 文件 | 风格 |
|---|---|---|---|
| **学员主轴** | 跟着自己跑的学员 | `README.md` + `homework/**` + `demo/**/prompts/*.md` | 命令行可粘贴、步骤可验证、有排错表 |
| **讲师主轴** | 自己上课口播 | `讲稿.md` | 第一人称、时间块标注、含真实战例 |
| **视觉主轴** | 投影/PDF | `lessonN.pptx` + `lessonN.pdf` | python-pptx 程序化构建、调色板按课区分 |

**README 是 canonical**——讲稿与 pptx 都是它的派生物：讲稿沿章节顺序口播化、pptx 沿章节标题视觉化。改 README → 同步讲稿与 pptx，反之不必。

## When to Use

用：
- 创建新课（lesson6 → lesson10）或新作业
- 改已有课的内容并要保持风格一致
- 在交付前审计某一课是否达到本项目的"可一步步跟随"门槛
- 内容改完后重 build pptx / 重导 pdf

不用：
- `lessonN/` 之外的代码（看 `.cursor/rules/project-conventions.mdc`）
- 一次性草稿、临时记录

## Required Reading（动手前必读）

**会话内只需加载一次**，按顺序：

1. `CLAUDE.md` — 项目级总约定（已在每次启动时自动注入，无需重读）
2. `plan_v2.md` — 10 课主纲，每课的"内容 / 实践 / 作业"段是这一课的输入合同
3. `.cursor/rules/project-conventions.mdc` — UTC、中文注释、"学员文档可一步步跟随"三条硬约束
4. **一份成熟课的全套产物作风格基准**——推荐 `lesson3/`（最简洁）或 `lesson5/`（最完整）

## Canonical File Set

```
lessonN/
├── README.md                    # 学员讲义（必备）
├── 讲稿.md                       # 讲师口播稿（lesson 3+ 起必备）
├── lessonN.pptx                 # 课件（必备）
├── lessonN.pdf                  # PDF 导出（交付前必备）
├── demo/<demo-name>/            # 课堂现场演示物
│   ├── ...                      # 任何配置/脚本
│   └── prompts/*.md             # 给学员粘贴的整段 prompt（命名直白）
├── homework/<task-name>/        # 作业，每个任务一目录
│   ├── README.md                # 任务说明，"step-by-step followable"
│   └── ...                      # 模板/示例文件
└── project/                     # lesson 3+ 才有：本课工作目录
    ├── .mcp.json                # 如有 MCP 接入
    ├── .gitignore
    └── ...
```

## Authoring Pipeline（8 步可粘贴执行）

> 用 `lessonN` 占位实际课号；命令前已假设 cwd = `/mnt/d/培训/ai_lesson`。

### 1. 拉目标
```bash
sed -n '/^## 第 N 课/,/^---$/p' plan_v2.md   # 把 N 替换成课号
```
读到这一课的 内容 / 实践 / 作业 三段，作为 README 与讲稿的内容输入。

### 2. 建目录
```bash
mkdir -p lessonN/{demo,homework}
test "N" -ge 3 && mkdir -p lessonN/project
touch lessonN/README.md lessonN/讲稿.md
```

### 3. 写 README.md（学员讲义）
复制 `templates/lesson-readme.md` → `lessonN/README.md`，按占位符填空。**章节顺序固定**：

| 段 | 标题 | 必含 |
|---|---|---|
| 0 | 开场段（衔接上一课 + 引出本课） | ✅ |
| 1 | 时长 + 主题列表 + 「跟着课件做」引用块 | ✅ |
| 2 | `## 〇、前置确认（30 秒）` —— checkbox 清单，每条要可一行命令验证 | ✅ |
| 3 | `## 一、<概念>` —— 概念讲解 + 类比 + 与上一课能力的对比表 | ✅ |
| 4 | `## 二、动手做（X 分钟）：<动词短语>` —— 步骤 1/2/3 + 期望输出 + 排错表 | ✅ |
| 5 | `## 三、动手做` —— 第二段动手做 | ✅ |
| 6 | `## 四、关键认知` —— 含口诀/记忆框（在代码块里） | ✅ |
| 7 | `## 五、<次要主题>` —— 权限/边界/扩展场景 | 可选 |
| 8 | `## 六、反模式（3 条）` —— **恰好 3 条**，编号 + 粗体标题 + 真实场景 | ✅ |
| 9 | `## 七、作业` —— 链接 `homework/<task>/README.md`，30 分钟内可完成 | ✅ |
| 10 | `## 学完这课，你能做什么` —— 4-6 条可验证的能力点 | ✅ |
| 11 | `## 延伸阅读` —— 表格 + 链接 | ✅ |

**逐字粘贴可执行**：每条命令、每个文件路径、每段 prompt 必须能原样复制运行；含空格的路径要加引号；改 PATH 后要写"新开终端"。禁止"在那个目录下…等等"。

### 4. 写 讲稿.md（讲师口播）
复制 `templates/lesson-jiangshou.md`。规则：

- frontmatter blockquote：`时长` / `配套学员讲义` / `配套课件`
- 章节标题统一格式：`## [mm:ss — mm:ss] §章名（X 分钟）`
- 顺序与 README 主章节**严格对齐**（「〇 前置确认」与「延伸阅读」可融进开场/收束）
- 第一人称、口语化（"好，我们开始"、"你们"、"记住"）
- **至少一段真实战例**（"我去年看过一个团队…"），用以加深记忆
- **收束段必须铺垫下一课**
- 时间预算（25 分钟课）：开场 1.5 min / 概念 2-3 min / 每段动手做 5-7 min / 关键认知 2-3 min / 反模式 2 min / 作业+收束 1.5 min

讲稿 **不**受 "学员文档可一步步跟随" 约束（受众不同），但仍受 UTC + 中文注释约定。

### 5. demo + homework
- **demo**：`demo/<name>/prompts/*.md`，文件名直白（`list-tables.md`、`analyze-btc.md`），每份就是一段可整体粘贴的 prompt
- **homework**：每个任务一目录，README.md 严格按 `templates/homework-readme.md` 骨架——前置 / 步骤 / 提交清单 / 还原命令缺一不可
- 作业里如含 token / 路径 / PAT，提供 `*.example` 文件作占位提交参考，README 里说明脱敏方式

### 6. build pptx
```bash
cp .claude/skills/lesson-authoring/templates/build-slides.py /tmp/build_lessonN_slides.py
# 在 /tmp/build_lessonN_slides.py 里按注释指引：
#   - 改 OUT 路径为 lessonN/lessonN.pptx
#   - 选/调本课调色板（每课换一个，避免视觉雷同）
#   - 按 README 章节填入 cover/agenda/sections/closing 内容
python /tmp/build_lessonN_slides.py
```
**字号下限**：正文 ≥ 14pt，代码块 ≥ 12pt。中文 Microsoft YaHei，等宽 Consolas。
**总页数指引**：~28 页 = 封面 1 + 议程 1 + 每个主题 4-6 页 + 收束 1。

### 7. export PDF
```bash
cd lessonN && libreoffice --headless --convert-to pdf lessonN.pptx
```
若机器没装 LibreOffice：`apt-get install -y libreoffice` 或在 Windows 端用 PowerPoint 另存为 PDF。

### 8. 验收
逐条对照 `checklist.md` 勾选。任何一项不过则不视为完工。

## Style Invariants（不可违反）

| 维度 | 规则 |
|---|---|
| 时间 | UTC + 显式 `Z` 或 `+00:00`，禁止 naive `datetime.now()` |
| 注释 | 中文（标识符英文，字面量按业务） |
| 学员文档（README/homework/demo prompts） | 一步步可跟随、命令可粘贴；过去时叙述禁止 |
| 反模式 | 恰好 3 条，编号 + 粗体小标题 + 真实场景 |
| 作业 | 30 分钟内可完成；提交清单 ≤ 4 条 |
| 衔接 | 开场必须引上一课；收束必须预告下一课 |
| 讲稿 vs README | 同章节顺序，讲稿可口语化但不脱离 README 范围 |

## Common Mistakes

| 现象 | 修法 |
|---|---|
| README 用过去时（"我跑了 X，结果 Y"） | 改命令式（"跑 X，期望看到 Y"） |
| 路径含糊（"在那个目录"） | 写绝对/明确相对路径，必要时 `cd` 显式 |
| 步骤跳跃（假设环境状态） | 在前置确认里 explicit，或本步开头补"先确认…" |
| 讲稿与 README 偏离 | 以 README 为准重写对应段（README 是 canonical） |
| pptx 字号 < 14 | 重 build，整体调字号；不要个别 slide 单独缩 |
| Lesson 无衔接段 | 补开场（引旧）+ 收束（预告新） |
| 作业超 30 分钟 | 砍范围，主任务 + 加分项分层 |
| 把"讲师演示日志"塞进 README | 那是讲稿的地盘，README 删除并搬到讲稿 |

## Files in this skill

| 文件 | 用途 |
|---|---|
| `SKILL.md` | 本文件——总指引 |
| `templates/lesson-readme.md` | 学员讲义骨架（按占位符填空） |
| `templates/lesson-jiangshou.md` | 讲师讲稿骨架 |
| `templates/homework-readme.md` | 作业 README 骨架 |
| `templates/build-slides.py` | python-pptx 课件构建脚手架（含 Ocean 调色板和 4 种已封装的辅助函数） |
| `checklist.md` | 交付前验收清单 |

## When Stuck

- 风格疑问 → 看 `lesson3/README.md`（最简洁）或 `lesson5/README.md`（最完整）
- 节奏疑问 → 看 `lesson3/讲稿.md`
- 视觉疑问 → 打开 `lessonN/lessonN.pptx` 看页面布局，源码不在仓库（每课的 build 脚本在 `/tmp/`，可用本 skill 模板重建）
- 课程目标疑问 → `plan_v2.md` 是合同
