# 任务 1：设计你自己的 Skill（必做）

## 时长

30 分钟内可完成。**只要求设计 SKILL.md，不要求实现底层代码**（实现是加分项）。

## 任务

从你日常工作里挑一个高频任务，把它设计成一个 SKILL.md。候选方向：

| 方向 | 触发场景 | 输入 | 输出 |
|---|---|---|---|
| 代码审查 | "review 这段 diff" | 本地 git diff | 风险列表 + 严重等级 |
| 日志分析 | "看看这份错误日志说啥" | log 文件路径 | 错误分类 + 频次 + 建议 |
| 接口文档生成 | "给这个 router 写文档" | 后端路由定义 | OpenAPI 风格 markdown |
| SQL 审查 | "看这条 SQL 有没有性能问题" | SQL 字符串 | 索引建议 / EXPLAIN 解读 |
| Commit message 生成 | "总结这次 staged change" | git diff --cached | conventional commit 格式标题 |
| 其他 | 你自己工作里高频的任务 | … | … |

## 步骤

1. **复制模板**：把 `SKILL.md.template` 复制到一个临时位置，改个名字。

2. **填 frontmatter**：
   - `name`：snake_case，比如 `code_review`
   - `description`：一句话说明何时触发该 skill。这一句最关键 —— Claude 是靠它判断要不要调用你的 skill 的。

3. **写"何时触发"**：列 3-5 种用户的实际说法（"帮我 review xxx" / "这段代码有问题吗" 等）。

4. **写"输入约定"**：用户给什么、可选参数有什么。

5. **写"步骤"**：3-7 步，每步 1-2 句，描述 Claude 应当做什么。

6. **写"反模式"**：列出 2-3 条这个 skill 不该做的事。

7. **加上"示例"**：1-2 条。

## 提交内容

1. **完整的 SKILL.md** —— 你设计的 skill 文件，可以放在仓库的 `lesson4/homework/task1-design-skill/MY_SKILL.md` 路径
2. **3 句话设计说明** —— 这个 skill 解决你工作里什么具体问题？为什么 prompt 不够、需要 skill？多少天能用上一次？
3. **加分项（可选）**：实际把 skill 装到 `~/.claude/skills/` 或 `lesson4/project/.claude/skills/`，调用一次，提交对话片段截图

## 评分维度

- **frontmatter description 是否清晰**：Claude 看到能不能判断"这个 skill 适合此刻"
- **步骤是否真的可执行**：不是写"做好审查"，而是"读 diff → 找 5 类风险 → 排序 → 输出"
- **反模式是否具体**：避免"不要做不好的事"这种空洞说法

## 参考

- 本课现成的 `backtest` skill：`lesson4/project/.claude/skills/backtest/SKILL.md`
- Anthropic 官方 skill 例子：[anthropics/skills](https://github.com/anthropics/skills)
- Superpowers 的 brainstorming/TDD skill：装 superpowers 后看 `~/.claude/plugins/.../skills/` 目录
