# 任务 1：跑通 Agent Teams 或装通 Hermes（二选一，必做）

## 时长

30 分钟内可完成。**二选一**——选你更想真正用上的那个方向。

## 目标

让 §二、§三 讲的两个工具**至少有一个在你电脑上真正跑起来**，不是停留在"听过"。

---

## A 方向：Claude Code Agent Team

### 前置
- Claude Code ≥ v2.1.32（`claude --version` 确认）
- 至少 Pro / Team / Max plan（Agent Teams 显著耗 token）

### 步骤

**1. 开启 experimental flag**

把这段 merge 到 `~/.claude/settings.json`（参考 `lesson7/demo/01-agent-teams/settings.json`）：

```json
{
  "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" },
  "teammateMode": "in-process"
}
```

或 shell 里 `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 临时启用。

**2. 起 team**

随便挑一个**你自己的真实项目**——开源 repo 也行、你私人项目也行。打开 Claude Code，粘贴下面这条（这是 `lesson7/demo/01-agent-teams/spawn-prompts.md` 范本 1）：

```
帮我起一个 agent team review 这个项目最近一次 commit。spawn 三个 reviewer：
- 一个专看 security implications
- 一个看 performance impact
- 一个 validate test coverage
让他们各自看完后报告 findings，最后给我一个 synthesized 总结。
```

**3. 观察 + 干预**

- Claude 会问你确认起 team（一定问）——确认
- 看着它 spawn 3 个 teammate，等它们跑——可能需要几分钟
- 按 `Shift+Down` 循环切换查看每个 teammate 在干什么
- 在 in-process 模式下按 `Ctrl+T` 查看共享 task list

**4. 收尾**

teammate 全跑完后，让 lead clean up：

```
clean up the team
```

### 提交

把以下三样放到 `lesson7/homework/task1-agent-team/<你的名字>-A/` 下：

1. `SYNTHESIS.md` —— lead 给你的最终 synthesis 文本（直接粘贴）
2. `OBSERVATIONS.md` —— 200 字感受：
   - 哪个 teammate 找到了你自己没想到的问题？
   - 它们之间互相发的消息你看到了几条？message 内容有什么特点？
   - 整轮花了多少 token？（看 `/usage`）
   - 跟你之前一个人用 Claude Code 干同件事相比，agent team 强在哪、弱在哪？
3. `~/.claude/teams/<team-name>/config.json` 的截图或粘贴（团队配置——证明你**真的** spawn 过一次）

---

## B 方向：Hermes Agent

### 前置
- Linux / macOS / WSL2 / Termux 任选（Windows 用 WSL2 比 PowerShell 稳）
- Anthropic 和 OpenAI 各有一个 API key（两家都申请最快的方式：[console.anthropic.com](https://console.anthropic.com) + [platform.openai.com](https://platform.openai.com)）

### 步骤

**1. 装**

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc       # 或 zshrc
hermes --version       # 确认能跑
```

**2. 配两家 provider**

```bash
hermes setup           # 走向导。先配一家（比如 Anthropic）
hermes model           # 再加一家（OpenAI）
```

或直接编辑 `~/.hermes/.env`（参考 `lesson7/demo/02-hermes/env.example`）：

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

**3. 跑通 + 演示 /model 切换**

```bash
hermes
```

进入交互式 CLI 后：

```
/model anthropic:claude-opus-4-7
> 你是谁？
（Claude 回答）

/model openai:gpt-4o
> 你是谁？
（GPT-4o 回答）

/model openrouter:google/gemini-2.0    # 如果你也配了 OpenRouter
```

**4. 接通一个消息入口**（推荐 Telegram，5 分钟搞定）

- Telegram 找 [@BotFather](https://t.me/BotFather)，发 `/newbot` 拿到一个 token
- 加到 `~/.hermes/.env`：`TELEGRAM_BOT_TOKEN=...`
- 编辑 `~/.hermes/config.yaml` enable telegram gateway
- 跑 `hermes gateway`
- 在 Telegram 找你刚建的 bot 私聊，看 Hermes 是不是接上了

**5. 诊断**

```bash
hermes doctor          # 看安装健康度
hermes /usage          # 看本轮 token
```

### 提交

把以下三样放到 `lesson7/homework/task1-agent-team/<你的名字>-B/` 下：

1. `SESSION.md` —— 一段会话截图或 transcript，含 **至少两次 `/model` 切换**，证明你真的在多家 provider 间切过
2. `DOCTOR.txt` —— `hermes doctor` 的完整输出
3. `REFLECTION.md` —— 200 字感受：
   - 配两家 provider 用了多久？哪一步最卡？
   - 切完 `/model` 之后 Claude 和 GPT 的回答风格差异？
   - 如果让你 7×24 跑一个 Hermes 替你管 Telegram，你会让它做什么？
   - 跟 Claude Code 比，Hermes 的优势 / 劣势？

---

## 评分维度

| 维度 | 合格标准 |
|---|---|
| 真跑过 | 提交的文件**真的**是从你电脑捕获的（团队 config / `hermes doctor` 输出有当前时间戳/路径） |
| 观察具体 | OBSERVATIONS / REFLECTION 写出**具体细节**，不是"很有收获"——能引用具体 teammate 名字 / 模型回答差异 |
| 选型清晰 | 你说清楚自己选这个方向（A 或 B）的理由 |

## 参考

- 课堂样本：`lesson7/demo/01-agent-teams/` 和 `lesson7/demo/02-hermes/`
- 官方文档：
  - [Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams)
  - [Hermes Agent GitHub](https://github.com/NousResearch/hermes-agent)
  - [Hermes Docs](https://hermes-agent.nousresearch.com/docs/)

## 常见问题

**Q: A 方向 Claude 不响应"起 team"指令？**
A: 检查三件事——(1) `claude --version` ≥ v2.1.32；(2) `~/.claude/settings.json` 里 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 真的存在；(3) 重启 Claude Code session 让 settings 生效。

**Q: B 方向 `hermes` 命令找不到？**
A: 装完没 `source ~/.bashrc` / `source ~/.zshrc`，或者 PATH 没加。先 `which hermes` 看，没有就重启终端。

**Q: 我没有 OpenAI key 怎么办？**
A: 用 OpenRouter 代替——一个 key 调 200+ 模型，包括 OpenAI 的全部模型。或者用 OpenRouter + 任意国内模型（Kimi、MiniMax）。

**Q: A 和 B 都做完算加分吗？**
A: 算。两个方向都做并写 `COMPARE.md` 对比一下使用体验，自动加 10 分（满分 100）。
