#!/usr/bin/env bash
# PostToolUse hook：每次 Bash 工具调用结束后，把 AI 跑过的命令记录下来
#
# 设计要点：
# 1. 写日志文件 bash-history.log（持久化审计，可以事后翻）
# 2. 同时打印到 stdout —— 让 Claude 自己也能看到，便于在对话里回忆 / 自我纠错
# 3. 多行命令压成单行、超长截断，保证 log 单行单条好查
# 4. 即使 jq 不可用也优雅降级，不阻断对话

set -uo pipefail

LOG_FILE="${CLAUDE_PROJECT_DIR:-.}/bash-history.log"
TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# stdin 是 Claude Code 注入的事件 JSON，从中抽 .tool_input.command
PAYLOAD="$(cat || true)"
if command -v jq > /dev/null 2>&1 && [ -n "$PAYLOAD" ]; then
    CMD="$(printf '%s' "$PAYLOAD" | jq -r '.tool_input.command // "-"')"
else
    CMD="(jq 未安装，无法解析命令文本——可 brew/apt install jq)"
fi

# 多行命令压成单行；超过 200 字截断（保留可读性，避免日志爆炸）
CMD="${CMD//$'\n'/ }"
CMD="${CMD//$'\t'/ }"
if [ ${#CMD} -gt 200 ]; then
    CMD="${CMD:0:200}…"
fi

# 1) 持久化到文件（审计追溯用）
printf '%s\t%s\n' "$TS" "$CMD" >> "$LOG_FILE"

# 2) 打到 stdout（hook 输出会回到对话里，让 Claude 自己也看到刚跑了什么）
echo "[bash-log] $TS  $CMD"

exit 0
