#!/usr/bin/env bash
# 自定义 hook 脚本：把每次工具调用追加到 .tool-use.log
# 调用约定：log_tool_use.sh <tool_name>
# stdin: Claude Code 注入的 hook 事件 JSON，含 tool_input.command 等字段
#
# 调试用，不上生产。生产场景下应该把日志打到结构化 sink（Loki/CloudWatch 等）。

set -euo pipefail

TOOL_NAME="${1:-unknown}"
LOG_FILE="${CLAUDE_PROJECT_DIR:-.}/.tool-use.log"
TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# stdin 是 JSON 事件，按工具类型抽不同字段（jq 不存在则降级输出原始 stdin 长度）
PAYLOAD="$(cat || true)"
if command -v jq >/dev/null 2>&1 && [[ -n "$PAYLOAD" ]]; then
    case "$TOOL_NAME" in
        Bash)
            DETAIL="$(printf '%s' "$PAYLOAD" | jq -r '.tool_input.command // "-"')"
            ;;
        Edit|Write)
            DETAIL="$(printf '%s' "$PAYLOAD" | jq -r '.tool_input.file_path // "-"')"
            ;;
        *)
            DETAIL="${CLAUDE_FILE_PATHS:--}"
            ;;
    esac
else
    DETAIL="${CLAUDE_FILE_PATHS:--}"
fi

# 把换行/制表符压成空格，避免破坏单行结构；裁到 200 字防止超长命令撑爆日志
DETAIL="${DETAIL//$'\n'/ }"
DETAIL="${DETAIL//$'\t'/ }"
if (( ${#DETAIL} > 200 )); then
    DETAIL="${DETAIL:0:200}…"
fi

printf '%s\t%s\t%s\n' "$TS" "$TOOL_NAME" "$DETAIL" >> "$LOG_FILE"

# 不输出到 stdout —— 避免污染主线对话
exit 0
