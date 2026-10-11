#!/usr/bin/env bash
# Polymarket BTC 套利信号工具 · 端到端 smoke 验收脚本
#
# 用途：在干净环境下跑一遍最关键的「发现 → 预测 → 价格 → 信号 → 推送」链路，
#       确认 backend + frontend + 外部依赖都活着，飞书能真实收到卡片。
#
# 适用场景：
#   - 每次发版前一次
#   - 真实外部 API 报错时手动跑一次定位问题
#   - 周一上午 QA 例行跑一次
#
# 依赖：bash 5+, curl, jq, psql (postgresql-client), docker-compose v2
# 前置：项目根 .env 里配齐 OPENAI_API_KEY / TAVILY_API_KEY / FEISHU_WEBHOOK_URL
#       或者 docker-compose 已起好、UI /settings 里已配好密钥

set -euo pipefail

# ─── 配置 ────────────────────────────────────────────────────────────────
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_BASE="${API_BASE:-http://localhost:8000/api/v1}"
FRONT_BASE="${FRONT_BASE:-http://localhost:3000}"
DB_DSN="${DB_DSN:-postgresql://btc_arb:btc_arb@localhost:5432/btc_arb}"
SMOKE_MARKET_URL="${SMOKE_MARKET_URL:-}"   # 必填，运行时传入或在 .env 设置
WAIT_PREDICTION_SECONDS="${WAIT_PREDICTION_SECONDS:-45}"

# 颜色
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
RESULTS=()

log_step()    { echo -e "${CYAN}== STEP $1 ==${NC} $2"; }
log_pass()    { echo -e "  ${GREEN}PASS${NC} $1"; PASS_COUNT=$((PASS_COUNT+1)); RESULTS+=("PASS: $1"); }
log_fail()    { echo -e "  ${RED}FAIL${NC} $1"; FAIL_COUNT=$((FAIL_COUNT+1)); RESULTS+=("FAIL: $1"); }
log_info()    { echo -e "  ${YELLOW}INFO${NC} $1"; }
fatal()       { echo -e "${RED}FATAL${NC}: $1"; exit 2; }

# ─── 前置检查 ────────────────────────────────────────────────────────────
require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fatal "缺少命令：$1（请先安装）"
}

require_cmd curl
require_cmd jq
require_cmd psql
require_cmd docker

if [[ -z "$SMOKE_MARKET_URL" ]]; then
  fatal "必须设置 SMOKE_MARKET_URL 环境变量为一个真实的 Polymarket BTC 二元市场 URL。
示例：SMOKE_MARKET_URL='https://polymarket.com/event/bitcoin-above-on-may-17' bash scripts/smoke.sh"
fi

echo "================================================================"
echo "  Polymarket BTC 套利信号工具 · Smoke Test"
echo "  开始时间: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "  API_BASE:   $API_BASE"
echo "  FRONT_BASE: $FRONT_BASE"
echo "  DB_DSN:     $DB_DSN"
echo "  MARKET_URL: $SMOKE_MARKET_URL"
echo "================================================================"

# ─── STEP 1: docker-compose up & healthcheck ────────────────────────────
log_step 1 "docker-compose 起服务等 healthcheck"

cd "$PROJECT_ROOT"

# 不自动起容器（避免 smoke 跑时把已有环境搞乱）；提示用户先 up
if ! docker compose ps --services --filter "status=running" 2>/dev/null | grep -q backend; then
  log_info "backend 容器未在运行。请先执行 'docker compose up -d' 再跑本脚本。"
  log_fail "docker-compose 服务未就绪"
  echo
  echo "如已 up，但容器名不叫 backend，可手工 export DOCKER_COMPOSE_PROJECT 等环境变量。"
  exit 1
fi

# 等 backend healthcheck（最多 60s）
for i in $(seq 1 30); do
  if curl -fsS "$API_BASE/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if curl -fsS "$API_BASE/healthz" | jq -e '.status == "ok"' >/dev/null 2>&1; then
  log_pass "/healthz 返回 ok"
else
  log_fail "/healthz 60s 内未变绿"
  exit 1
fi

# readyz: 检查外部依赖
READYZ="$(curl -fsS "$API_BASE/readyz" || true)"
if [[ -n "$READYZ" ]]; then
  echo "  readyz components:"
  echo "$READYZ" | jq -r '.components | to_entries[] | "    - " + .key + ": " + .value' || echo "    (parse failed)"
  if echo "$READYZ" | jq -e '.status == "ok"' >/dev/null; then
    log_pass "/readyz 全绿"
  else
    log_fail "/readyz 有 fail 项（见上）"
  fi
else
  log_fail "/readyz 无响应"
fi

# ─── STEP 2: 手动添加市场 ────────────────────────────────────────────────
log_step 2 "POST /markets 手动添加一个真实 BTC 市场"

ADD_RESPONSE="$(
  curl -fsS -X POST "$API_BASE/markets" \
    -H 'Content-Type: application/json' \
    -d "$(jq -n --arg url "$SMOKE_MARKET_URL" '{polymarket_url: $url}')" || echo "{}"
)"

MARKET_ID="$(echo "$ADD_RESPONSE" | jq -r '.market.id // empty')"

if [[ -n "$MARKET_ID" ]]; then
  log_pass "市场已入库，id=$MARKET_ID"
  echo "  market: $(echo "$ADD_RESPONSE" | jq -c '.market | {id, question, state, resolve_at}')"
  echo "  prediction.p_ai: $(echo "$ADD_RESPONSE" | jq -r '.prediction.p_ai')"
else
  ERR_CODE="$(echo "$ADD_RESPONSE" | jq -r '.error.code // "UNKNOWN"')"
  if [[ "$ERR_CODE" == "MARKET_NOT_FOUND" ]] || [[ "$ERR_CODE" == "URL_INVALID" ]]; then
    log_fail "URL 解析失败：$ERR_CODE。换一个真实可用的 BTC 二元市场 URL 再跑。"
  elif [[ "$ERR_CODE" =~ ^MARKET_ ]] && [[ "$ERR_CODE" != "UNKNOWN" ]]; then
    log_fail "市场不合规：$ERR_CODE（非二元 / 已结算 / 不可解析）"
  else
    # 已存在 → 取已有市场 id 继续测
    EXISTING_ID="$(echo "$ADD_RESPONSE" | jq -r '.market.id // empty')"
    if [[ -n "$EXISTING_ID" ]]; then
      MARKET_ID="$EXISTING_ID"
      log_info "市场已存在，复用 id=$MARKET_ID"
      log_pass "已有市场，继续测"
    else
      log_fail "添加失败：$ADD_RESPONSE"
      exit 1
    fi
  fi
fi

# ─── STEP 3: 等预测完成 ─────────────────────────────────────────────────
log_step 3 "等 ${WAIT_PREDICTION_SECONDS}s 让首次预测完成（OpenAI + Tavily + Binance）"

PRED_OK=0
for i in $(seq 1 "$WAIT_PREDICTION_SECONDS"); do
  PRED_COUNT="$(
    curl -fsS "$API_BASE/markets/$MARKET_ID/predictions" 2>/dev/null \
      | jq -r '.items | length' || echo 0
  )"
  if [[ "$PRED_COUNT" -gt 0 ]]; then
    PRED_OK=1
    break
  fi
  sleep 1
done

if [[ "$PRED_OK" -eq 1 ]]; then
  PRED_JSON="$(curl -fsS "$API_BASE/markets/$MARKET_ID/predictions" | jq -c '.items[0]')"
  log_pass "已生成 $PRED_COUNT 条预测；最新 p_ai=$(echo "$PRED_JSON" | jq -r '.p_ai')，model_version=$(echo "$PRED_JSON" | jq -r '.model_version')"

  # 关键断言：model_version 不应包含 -llm-fail 与 -stale-spot（外部依赖应该是正常的）
  MV="$(echo "$PRED_JSON" | jq -r '.model_version')"
  if echo "$MV" | grep -q "llm-fail"; then
    log_fail "model_version 含 'llm-fail' — OpenAI 不可用，请检查 API key 或网络"
  fi
  if echo "$MV" | grep -q "stale-spot"; then
    log_fail "model_version 含 'stale-spot' — Binance 不可用，请检查网络"
  fi
else
  log_fail "${WAIT_PREDICTION_SECONDS}s 内预测仍未生成"
fi

# ─── STEP 4: 手动触发 price_poll ────────────────────────────────────────
log_step 4 "POST /scheduler/trigger 拉一次价格"

POLL_RESP="$(
  curl -fsS -X POST "$API_BASE/scheduler/trigger" \
    -H 'Content-Type: application/json' \
    -d '{"job":"price_poll"}'
)"
JOB_RUN_ID="$(echo "$POLL_RESP" | jq -r '.job_run_id // empty')"

if [[ -n "$JOB_RUN_ID" ]]; then
  log_pass "price_poll 已加入队列，job_run_id=$JOB_RUN_ID"
else
  log_fail "trigger 失败：$POLL_RESP"
fi

# 等 10s 让 job 跑完
sleep 10
TICKS="$(
  curl -fsS "$API_BASE/markets/$MARKET_ID/price_ticks?granularity=raw" \
    | jq -r '.items | length'
)"
if [[ "$TICKS" -gt 0 ]]; then
  log_pass "price_tick 已写入 $TICKS 条"
else
  log_fail "price_tick 仍为空 — 检查 PolymarketClient.get_midpoint 是否能拿数据"
fi

# ─── STEP 5: 改 DB 强制构造价差，让 SignalEngine 触发 ENTRY ──────────
log_step 5 "psql 强制 market.state=WATCHING + p_ai 远离 mid（人为造 ENTRY 信号）"

CURRENT_MID="$(
  curl -fsS "$API_BASE/markets/$MARKET_ID/price_ticks?granularity=raw" \
    | jq -r '.items[0].p_yes'
)"
log_info "当前 mid p_yes=$CURRENT_MID"

# 构造一个 gap = +0.25 的 p_ai（保证 > entry_threshold 0.15）
FORCED_P_AI="$(echo "$CURRENT_MID" | awk '{ v = $1 + 0.25; if (v > 0.99) v = 0.99; printf "%.4f\n", v }')"
log_info "人为设 p_ai=$FORCED_P_AI（gap=$(echo "$FORCED_P_AI $CURRENT_MID" | awk '{ printf "%.4f", $1 - $2 }')）"

psql "$DB_DSN" <<SQL >/dev/null
BEGIN;
UPDATE market SET state='WATCHING', last_state_change_at = now() - interval '1 hour' WHERE id = $MARKET_ID;
UPDATE prediction SET p_ai = $FORCED_P_AI WHERE id = (
  SELECT id FROM prediction WHERE market_id = $MARKET_ID ORDER BY created_at DESC LIMIT 1
);
COMMIT;
SQL

if [[ $? -eq 0 ]]; then
  log_pass "DB 已强制改 state + p_ai"
else
  log_fail "psql 改库失败"
fi

# ─── STEP 6: 再 trigger price_poll，应触发 ENTRY_LONG 信号 ──────────
log_step 6 "再 trigger price_poll，应触发 ENTRY_LONG → 写 signal_event → 推飞书"

curl -fsS -X POST "$API_BASE/scheduler/trigger" \
  -H 'Content-Type: application/json' \
  -d '{"job":"price_poll"}' >/dev/null
sleep 10

LATEST_EVENT="$(
  curl -fsS "$API_BASE/signals?market_id=$MARKET_ID&limit=1" \
    | jq -c '.items[0] // empty'
)"

if [[ -n "$LATEST_EVENT" ]]; then
  KIND="$(echo "$LATEST_EVENT" | jq -r '.kind')"
  PUSHED="$(echo "$LATEST_EVENT" | jq -r '.feishu_pushed')"
  if [[ "$KIND" == "ENTRY_LONG" ]]; then
    log_pass "signal_event ENTRY_LONG 已写入"
  else
    log_fail "kind 不是 ENTRY_LONG（实际 $KIND）— 检查 SignalEngine 跃迁逻辑"
  fi
  if [[ "$PUSHED" == "true" ]]; then
    log_pass "feishu_pushed=true"
  else
    ERR="$(echo "$LATEST_EVENT" | jq -r '.feishu_error // "(无错误信息)"')"
    log_fail "feishu_pushed=false，错误：$ERR"
  fi
else
  log_fail "没有任何 signal_event — 状态机未触发，检查 entry_threshold 与 debounce 设置"
fi

# ─── STEP 7: 人工确认飞书群收到卡片 ─────────────────────────────────────
log_step 7 "人工确认：去飞书群里看是否收到「🟠 入场信号 · 看涨 (买 YES)」卡片"

echo
echo -e "${YELLOW}请打开你配置 webhook 的飞书群，检查：${NC}"
echo "  - 是否收到一条橙底标题「🟠 入场信号 · 看涨 (买 YES)」卡片"
echo "  - 卡片字段：市场名链接、AI 预测 vs 市场价、价差、置信度、LLM 理由"
echo "  - 底部两个按钮「查看市场」「打开仪表盘详情」"
echo "  - 「打开仪表盘详情」按钮点击应跳到 $FRONT_BASE/markets/$MARKET_ID"
echo
read -r -p "  飞书卡片收到并字段无误？(y/n): " FEISHU_OK
if [[ "$FEISHU_OK" =~ ^[Yy]$ ]]; then
  log_pass "人工确认：飞书卡片渲染正确"
else
  log_fail "人工确认：飞书卡片有问题"
fi

# ─── STEP 8: 6 个场景自检（按 PRD §2.2）────────────────────────────────
log_step 8 "S1–S6 关键场景自检（人工跑前端 UI）"

cat <<'CHECKLIST'

请按以下场景到 http://localhost:3000 逐一验证，回到终端按 y/n：

  S1 起床看信号
     /dashboard 应能看到刚才造出来的 ENTERED_LONG 卡片（橙边框、gap 显示正确）
     点击卡片应跳 /markets/{id}

  S2 手动预测
     /predict 贴一个新的 BTC 市场 URL → 点「试一次」→ 30s 内出预测面板
     非法 URL（如 https://example.com）应被前端 inline 拒绝

  S3 信号兑现（模拟）
     psql 把 prediction.p_ai 调到等于当前 mid → 再 trigger price_poll
     应推 EXIT_LONG 卡片，market.state 回 WATCHING

  S4 调参
     /settings 把 entry_threshold 从 0.150 改成 0.250 → 保存
     下一轮 price_poll 应按 0.250 判断，gap +0.20 不再触发

  S5 看历史复盘
     /history 应看到刚才造的 ENTRY_LONG 与 EXIT_LONG（如做了 S3）两条
     筛选「近 7 天」「ENTRY_LONG」类型应工作正常

  S6 排错
     /settings → ⑤ 调度状态 应显示 5 个 job 的下次运行时间
     点「发送测试卡片」→ 飞书群应收到样板卡片
     点 daily_discovery「手动触发」→ /scheduler/runs 应新增一行

CHECKLIST

read -r -p "  S1 完成？(y/n): " S1; [[ "$S1" =~ ^[Yy]$ ]] && log_pass "S1 起床看信号" || log_fail "S1 起床看信号"
read -r -p "  S2 完成？(y/n): " S2; [[ "$S2" =~ ^[Yy]$ ]] && log_pass "S2 手动预测" || log_fail "S2 手动预测"
read -r -p "  S3 完成？(y/n): " S3; [[ "$S3" =~ ^[Yy]$ ]] && log_pass "S3 信号兑现" || log_fail "S3 信号兑现"
read -r -p "  S4 完成？(y/n): " S4; [[ "$S4" =~ ^[Yy]$ ]] && log_pass "S4 调参" || log_fail "S4 调参"
read -r -p "  S5 完成？(y/n): " S5; [[ "$S5" =~ ^[Yy]$ ]] && log_pass "S5 历史复盘" || log_fail "S5 历史复盘"
read -r -p "  S6 完成？(y/n): " S6; [[ "$S6" =~ ^[Yy]$ ]] && log_pass "S6 排错" || log_fail "S6 排错"

# ─── STEP 9: 清理（可选）────────────────────────────────────────────────
log_step 9 "（可选）清理本次测试构造的数据"
echo
read -r -p "  是否软删本次测试市场 id=$MARKET_ID？(y/n): " CLEAN
if [[ "$CLEAN" =~ ^[Yy]$ ]]; then
  curl -fsS -X DELETE "$API_BASE/markets/$MARKET_ID" -o /dev/null -w "%{http_code}\n" | grep -q "204" \
    && log_pass "DELETE 返回 204"
fi

# ─── 总结 ────────────────────────────────────────────────────────────────
echo
echo "================================================================"
echo -e "  结果：${GREEN}$PASS_COUNT PASS${NC}, ${RED}$FAIL_COUNT FAIL${NC}"
echo "  结束时间: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "================================================================"
for r in "${RESULTS[@]}"; do
  if [[ "$r" == FAIL* ]]; then
    echo -e "  ${RED}$r${NC}"
  else
    echo -e "  ${GREEN}$r${NC}"
  fi
done
echo

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  exit 1
fi
exit 0
