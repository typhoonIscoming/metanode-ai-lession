# Hook 加分项参考实现 — 把 AI 跑过的 Bash 命令记下来

> 这是 [README §五加分项](../../README.md#加分项可选) 的参考实现：
> 一个**最直观**的 PostToolUse hook —— **每次 AI 跑 Bash 命令，都自动记一行日志**，
> 同时把这一行回显到对话里，让你和 AI 自己都能看见"刚跑了什么"。
>
> 严格按下面顺序操作，**任何学员 5 分钟内能复现**。

---

## 0. 这个加分项的目录结构

```
lesson2/homework/task1-hook/
├── .claude/
│   ├── settings.json                # PostToolUse hook 配置（仅 Bash）
│   └── scripts/log-bash.sh          # hook 调用的日志脚本
├── .gitignore                       # 忽略 bash-history.log
└── execution-record.md              # 你正在看的这份
```

跑起来后还会生成：

```
└── bash-history.log                 # 审计日志，每行一条命令
```

---

## 1. 前置检查（30 秒）

依次跑这三条命令，每条都必须通过：

```bash
# 1.1 jq 已安装（hook 用它从 JSON 抽命令字段）
jq --version
# 没装 → macOS: brew install jq | Ubuntu/WSL: sudo apt install jq

# 1.2 进入本加分项的子目录
cd lesson2/homework/task1-hook
pwd
# 输出末尾应当是 .../lesson2/homework/task1-hook

# 1.3 确认本目录有自己的 .claude/settings.json
cat .claude/settings.json
# 应当看到 PostToolUse + matcher: "Bash" + 调用 log-bash.sh
```

> **为什么必须 cd 到本目录？**
> Claude Code 把"启动时所在目录"作为 `$CLAUDE_PROJECT_DIR`，从而决定加载哪份 hook。
> 在仓库根启动会加载根目录配置，**看不到本目录的 hook**。
>
> **没装 jq 也能跑**——脚本会优雅降级，但日志里命令字段会写成提示文本，无法看到真正命令。强烈建议装上。

---

## 2. 在本目录启动 Claude Code

```bash
claude
```

启动时 Claude Code 读取 `lesson2/homework/task1-hook/.claude/settings.json`，注册 PostToolUse hook（仅匹配 `Bash` 工具）。

> 启动横幅里看不到额外信息是正常的——这个加分项没配 SessionStart hook，只在 AI 真正跑 Bash 命令时才有动静。

---

## 3. 让 Claude 跑几条 Bash 命令

完整粘贴下面这段到 Claude Code，回车：

```
请跑以下三条命令，每条独立一次 Bash 调用：
1. git status --short
2. ls -la
3. echo "hello from AI"
```

---

## 4. 观察 hook 实时回显

Claude 每跑完一条 Bash，屏幕上**紧接着**就会出现一行 hook 输出：

```
⏺ Bash(git status --short)
  ⎿  ?? bash-history.log

[bash-log] 2026-05-05T03:30:00Z  git status --short

⏺ Bash(ls -la)
  ⎿  total 12
     drwxrwxrwx 1 root root 4096 ...
     ...

[bash-log] 2026-05-05T03:30:02Z  ls -la

⏺ Bash(echo "hello from AI")
  ⎿  hello from AI

[bash-log] 2026-05-05T03:30:04Z  echo "hello from AI"
```

每行 `[bash-log] ...` 就是 `log-bash.sh` 的 stdout 输出 —— **它回到了对话里**，所以你和 Claude 都能看到。

---

## 5. 检查持久化日志

退出 Claude（`Ctrl+D`），打开 `bash-history.log`：

```bash
cat bash-history.log
```

应当看到 TSV 格式（时间戳 + 制表符 + 命令）：

```
2026-05-05T03:30:00Z	git status --short
2026-05-05T03:30:02Z	ls -la
2026-05-05T03:30:04Z	echo "hello from AI"
```

> 注意：这一份日志是**事后审计**用的；每次 Claude 会话期间它都在追加，刻意保留跨会话历史。

---

## 6. 清理（可选）

```bash
rm -f bash-history.log
```

> `bash-history.log` 已在 `.gitignore` 里，不会被误提交。
> 不删也行，下次跑会接着往下追加。

---

## 7. 常见错误排查

| 现象 | 原因 | 解决 |
|---|---|---|
| Claude 跑了 Bash，**没**看到 `[bash-log] ...` | 没在 task1-hook 子目录启动 claude | 退出 → `cd lesson2/homework/task1-hook` → 重新 `claude` |
| `[bash-log]` 出现了，但命令字段写着"jq 未安装" | 全局没装 jq | `brew install jq` 或 `apt install jq` |
| `bash-history.log` 没生成 | hook 没触发，或 `$CLAUDE_PROJECT_DIR` 为空 | 用 `claude --debug` 启动看 hook 是否跑了 |
| 有 hook 输出但没在对话里看到（仅落到日志文件） | 老版本 Claude Code 不把 stdout 回流到对话 | 升级 Claude Code：`curl -fsSL https://claude.ai/install.sh \| bash` |

---

## 8. 把它当模板搬到自己的项目

想让自己的项目也"看着 AI 跑命令"？复制这两个文件 + 一行 .gitignore：

```bash
mkdir -p <你的项目>/.claude/scripts
cp .claude/settings.json     <你的项目>/.claude/
cp .claude/scripts/log-bash.sh <你的项目>/.claude/scripts/
chmod +x <你的项目>/.claude/scripts/log-bash.sh
echo 'bash-history.log' >> <你的项目>/.gitignore
```

进阶玩法：
- **加 cwd 字段**：脚本里读 `.tool_input.description` 或在 jq 里抽 `$CLAUDE_PROJECT_DIR`，记录每条命令的执行环境
- **过滤敏感命令**：识别到 `aws`/`gcloud`/`token` 等关键词时记 `[REDACTED]` 而不是原文
- **改成报警**：检测到 `rm -rf`、`git push --force` 等危险命令时 `exit 1` 阻塞执行（变成 PreToolUse hook）
