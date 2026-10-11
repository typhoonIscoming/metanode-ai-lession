# Hermes 命令速查

打印出来贴桌上、或者 `cat lesson7/demo/02-hermes/commands-cheatsheet.md` 随时回看。

## 安装

```bash
# Linux / macOS / WSL2 / Termux
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc       # 或 ~/.zshrc

# Windows PowerShell（early beta）
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

## CLI 层命令（在 shell 里跑）

| 命令 | 用途 |
|---|---|
| `hermes` | 启动交互式 CLI |
| `hermes setup` | 完整向导（首次推荐） |
| `hermes model` | 切换 LLM 提供商 / 模型 |
| `hermes tools` | 启用 / 禁用工具 |
| `hermes gateway` | 启动消息网关 |
| `hermes config set <key> <value>` | 改单条配置 |
| `hermes doctor` | 诊断当前安装状态 |
| `hermes claw migrate` | 从 OpenClaw 迁移会话 |
| `hermes --version` | 看版本 |

## 会话内 slash 命令（在 `hermes` 里跑）

| 命令 | 用途 |
|---|---|
| `/new` 或 `/reset` | 新建会话 |
| `/model` | 弹出 provider 选择器 |
| `/model <provider>:<model>` | 直接切，如 `/model openai:gpt-4o` |
| `/personality [name]` | 切人格（基于 SOUL.md） |
| `/skills` | 浏览所有技能 |
| `/<skill-name>` | 直接调用某个技能 |
| `/retry` | 重试上一轮 |
| `/undo` | 撤销上一轮 |
| `/compress` | 压缩 context |
| `/usage` | 看本会话 token 用量 |
| `/insights --days N` | 看 N 天行为洞察 |
| `/stop` | 中断当前工作 |

## 切模型的 3 种方式（最常用）

```bash
# 方式 1：交互向导（加新 provider 必走）
hermes model

# 方式 2：CLI 启动时指定
hermes chat --provider anthropic --model claude-opus-4-7

# 方式 3：会话内一句话
/model openai:gpt-4o
/model anthropic:claude-opus-4-7
/model openrouter:google/gemini-2.0
/model custom:local:qwen-2.5
```

## 常见任务

```bash
# 装完先跑这个检查
hermes doctor

# 配 Telegram 网关（5 分钟）
# 1. @BotFather 拿 token
# 2. 写到 ~/.hermes/.env: TELEGRAM_BOT_TOKEN=...
# 3. 跑：
hermes gateway

# 让 Hermes 帮你做日报（自然语言描述 cron）
hermes
> 每天早 8 点给我推送昨天的 GitHub PR 列表到 Telegram
```
