#!/usr/bin/env bash
# Polymarket BTC 套利信号工具 · Phase 0 骨架冒烟脚本（B-03 雏形）
#
# 用途：docker compose up 后，最小化确认 backend 活着 + 6 个路由都挂上了。
# 真实「发现 → 预测 → 信号 → 推送」端到端 smoke 见 ./smoke.sh（Phase 1+ 后启用）。
#
# 用法：
#   ./scripts/smoke-phase0.sh                    # 默认 localhost:8000
#   API_BASE=http://1.2.3.4:8000/api/v1 ./scripts/smoke-phase0.sh

set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000/api/v1}"

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'

pass=0; fail=0

run() {
  local label="$1" expected="$2" method="$3" path="$4" body="${5:-}"
  local url="$API_BASE$path"
  local code
  if [[ -n "$body" ]]; then
    code=$(curl -sS -o /dev/null -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$body" "$url")
  else
    code=$(curl -sS -o /dev/null -w "%{http_code}" -X "$method" "$url")
  fi
  if [[ "$code" == "$expected" ]]; then
    echo -e "  ${GREEN}PASS${NC}  $label  (got $code)"
    pass=$((pass+1))
  else
    echo -e "  ${RED}FAIL${NC}  $label  (expected $expected got $code)"
    fail=$((fail+1))
  fi
}

echo -e "${CYAN}== Phase 0 smoke @ $API_BASE ==${NC}"

run "GET  /healthz"                   200 GET  /healthz
run "GET  /markets (list)"            200 GET  /markets
run "GET  /markets/999999 (single)"   404 GET  /markets/999999
run "GET  /markets/1/predictions"     200 GET  /markets/1/predictions
run "GET  /markets/1/price_ticks"     200 GET  /markets/1/price_ticks
run "POST /markets (stub)"            422 POST /markets '{"polymarket_url":"https://polymarket.com/event/x"}'
run "POST /predict (stub)"            422 POST /predict '{"polymarket_url":"https://polymarket.com/event/x"}'
run "GET  /signals (list)"            200 GET  /signals
run "GET  /signals/1"                 404 GET  /signals/1
run "GET  /settings"                  200 GET  /settings
run "PATCH /settings (stub)"          422 PATCH /settings '{"entry_threshold":"0.2"}'
run "POST /settings/test_feishu"      422 POST /settings/test_feishu
run "GET  /scheduler/jobs"            200 GET  /scheduler/jobs
run "GET  /scheduler/runs"            200 GET  /scheduler/runs
run "POST /scheduler/trigger"         422 POST /scheduler/trigger '{"job":"price_poll"}'

echo
echo -e "  ${GREEN}$pass PASS${NC}  ${RED}$fail FAIL${NC}"
[[ $fail -eq 0 ]] && exit 0 || exit 1
