# Agent Team 生命周期速查

从开 team 到清理的 6 个阶段——每阶段一句话 + 关键命令。

```
[开启 flag]
   ↓
[起 team]                  自然语言一句话给 lead
   ↓                       Claude 自动落盘 ~/.claude/teams/<name>/config.json
                          自动落盘 ~/.claude/tasks/<name>/
   ↓
[spawn teammates]          每个 teammate 独立 Claude Code 实例
   ↓                       默认 in-process / 可切 split-pane
   ↓
[teammates 工作]           共享 task list、mailbox 互相发消息
   ↓                       Shift+Down 切换查看
   ↓                       Ctrl+T 看 task list
   ↓
[plan approval（可选）]    teammate 在 read-only mode 等 lead 批
   ↓                       lead 按你设的标准自动批
   ↓
[teammate 报告 idle]       自动 notify lead，lead 收口 synthesize
   ↓
[clean up]                  让 lead 跑：clean up the team
                          ❌ 不能让 teammate 跑 cleanup
```

## 关键路径文件

| 路径 | 内容 | 能不能手动改 |
|---|---|---|
| `~/.claude/teams/<name>/config.json` | team 配置 + members + runtime state | **❌ 不能**——会被下次状态更新覆盖 |
| `~/.claude/tasks/<name>/` | 共享 task list 文件 | 可以读，但**别手动改**——破坏状态机 |
| `.claude/teams/teams.json`（项目级） | **不识别** | 项目根放这个文件 Claude 当普通文件，不当 team config |

## 排错速查

| 现象 | 大概率原因 | 解 |
|---|---|---|
| 让 Claude "起 team" 它说不懂 | 没开 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | 改 settings.json 后**重启** session |
| split-pane 没起效 | tmux / iTerm2 不可用 | `which tmux` 看，没有装一下；或者用 in-process |
| `/resume` 后 lead 找不到 teammate | 实验性 limitation：session resume 不恢复 in-process teammate | 让 lead 重新 spawn |
| Task 状态卡 in_progress 不变 completed | teammate 忘记 mark；偶尔会发生 | 手动改 task 状态或让 lead 推一把 |
| Lead 自己开始干活而不等 teammate | "Wait for your teammates to complete their tasks before proceeding" | 直接对 lead 这么说 |
| 多 teammate 改同一文件覆盖了 | prompt 没分文件所有权 | 重起 team 时显式说"A 只改 X 目录，B 只改 Y" |
