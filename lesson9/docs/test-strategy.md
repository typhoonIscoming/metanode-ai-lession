# Polymarket BTC 套利信号工具 · 测试策略

> 文档版本：v1.0
> 编写日期：2026-05-18
> Owner: QA
> 适用范围：`backend/`、`frontend/`、`scripts/`
> 依赖文档：`PRD.md`、`backend-PRD.md`、`frontend-PRD.md`

---

## 0. 这份文档解决什么问题

这是一个**资金敏感**的套利信号工具：误报 ENTRY 会诱导真金白银下注，漏报 EXIT 会错过平仓时机。同时是**多外部依赖**系统（Polymarket Gamma/CLOB、OpenAI、Tavily、Binance、飞书），任意一个挂掉都要降级而不能让全系统下线。

本文档把团队对「什么必测、怎么测、什么时候测、谁来兜底」的共识固化下来。开发动工前读它；写测试时对照它；评审 PR 时引用它。

---

## 1. 风险优先级（驱动测试投入分配）

按「资金安全 → 价格数据 → 降级路径 → 通道幂等 → 时区」从高到低，所有测试投入都按这个顺序倾斜。

| 优先级 | 风险点 | 关键模块 | 覆盖率门槛 | 备注 |
|---|---|---|---|---|
| P0 | SignalEngine 状态机 transition / 去抖 / 临近结算 / 事务边界 | `services/signal_engine.py` | **≥ 95%** | 误报 ENTRY 直接造成资金损失，最高风险 |
| P0 | 量化概率计算 + clip 范围 | `services/quant_model.py` | **≥ 95%** | 信号源头，算错全盘错 |
| P0 | 飞书推送幂等 + 重试 + 卡片渲染 | `services/notification.py` | **≥ 95%** | 同一信号推两次或丢失都是用户体感 P0 |
| P1 | 外部依赖降级（OpenAI/Binance/Tavily/Polymarket 失败） | `services/llm_adjuster.py`、`adapters/*.py` | ≥ 85% | model_version 后缀与缓存 stale 标记必测 |
| P1 | YES/NO token_id 取错（反向） | `adapters/polymarket.py` | ≥ 85% | 取错则所有信号反向，必须断言 |
| P1 | 时区 / `resolve_at` 边界（59m59s / 60m00s / 60m01s） | `services/signal_engine.py` | 含在 P0 | 全栈强约束 |
| P2 | URL 解析 / strike 提取 / 输入校验 | `adapters/polymarket.py`、`schemas/*.py` | ≥ 85% | 用户输入边界 |
| P2 | API 路由层 happy path + 4xx/422 错误码 | `routers/*.py` | ≥ 80% | 由集成测试主要覆盖 |
| P2 | 调度器 lifecycle（重启、misfire、coalesce） | `scheduler/*.py` | ≥ 80% | |

**底线**：整体仓库覆盖率 ≥ 80%（`--cov-fail-under=80` 硬卡）。

---

## 2. 测试金字塔与每层职责

```
                ┌──────────────────────┐
                │  manual smoke (人工) │  scripts/smoke.sh
                └──────────────────────┘
              ┌───────────────────────────┐
              │ contract tests (3-5 个)   │  tests/contract/  防外部 API schema 漂移
              └───────────────────────────┘
           ┌─────────────────────────────────┐
           │ integration tests (~30 个)      │  tests/integration/  testcontainers-postgres
           └─────────────────────────────────┘
       ┌───────────────────────────────────────────┐
       │ unit tests (≥ 150 个)                     │  tests/unit/  hand-written mocks
       └───────────────────────────────────────────┘
   ┌─────────────────────────────────────────────────────┐
   │ frontend component tests (Vitest + RTL，≥ 60%)      │  frontend/tests/components/
   └─────────────────────────────────────────────────────┘
```

### 2.1 单元测试（`backend/tests/unit/`）

- **职责**：覆盖每个 service / adapter 的纯逻辑分支。
- **数据库**：不用真 DB，必要时用 `pytest-asyncio` + 内存 mock。
- **外部 API**：全部 hand-written mock（mock httpx Response）。
- **优先级**：本层是覆盖率门槛的主战场。`decide_transition` 这种纯函数应该被独立成无 IO 的模块，单独被打满。
- **工具**：pytest, pytest-asyncio, pytest-mock, unittest.mock。

### 2.2 集成测试（`backend/tests/integration/`）

- **职责**：跨多个 service + 真 DB 的端到端断言。例：`POST /api/v1/markets` 走完 MarketDiscoveryService → PredictionService → SignalEngine → 写表，断言三张表都有正确记录。
- **数据库**：testcontainers 拉真 Postgres 16，每个测试函数独立 transaction（用 `db.begin_nested()` + savepoint，结束 rollback）。
- **外部 API**：全部 mock（hand-written），不打真网络。
- **优先级**：覆盖 PRD §9.2 列举的 4 条端到端流程。

### 2.3 契约测试（`backend/tests/contract/`）

- **职责**：守护「真实外部 API 的 schema」与「我们 parser 假设」的一致性。
- **方式**：3–5 个真实抓回的 JSON fixture（`tests/fixtures/contract/*.json`），喂给我们的 parser，断言能正确解析出关键字段。
- **覆盖端点**（v1）：
  1. Polymarket Gamma `/markets?tag=bitcoin` 一次响应
  2. Polymarket CLOB `/midpoint?token_id=...` 一次响应
  3. Binance `/api/v3/ticker/price?symbol=BTCUSDT` 一次响应
  4. Binance `/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=720` 一次响应
  5. OpenAI Responses API structured output 一次响应（喂给 `AdjusterSchema`，断言 Pydantic 解析成功）
- **刷新策略**：季度刷一次 + smoke.sh 发现真实 API 异常时手动跑 `scripts/refresh_fixtures.py`（详见 §6）。
- **失败处理 SOP**：见 §7「Contract test 红了之后的 SOP」。
- **不做的事**：不用 fixture 作为集成测试的通用 mock 源 —— 那会让 mock 行为僵化，case 难灵活构造。

### 2.4 手动验收（smoke）

- **职责**：docker-compose 全量起，跑 PRD §9.3 的 7 步脚本，真打飞书 webhook 验证最终送达。
- **触发**：每次 release 前一次；外部 API 报警时手动跑一次。
- **脚本**：`scripts/smoke.sh`，输出 PASS/FAIL 行清单。

### 2.5 前端组件测试（`frontend/tests/components/`）

- **职责**：覆盖关键展示组件（`<MarketCard>`、`<PriceChart>`、`<StateBadge>`）和工具函数（`apiFetch`、`PolymarketUrlSchema`）。
- **覆盖率**：整体 ≥ 60%；关键组件 ≥ 80%。
- **工具**：Vitest + React Testing Library。
- **不做**：Playwright E2E、视觉回归、浏览器矩阵。

---

## 3. 覆盖率门槛（硬卡）

### 3.1 数值

| 范围 | 阈值 | 工具 | 落地位置 |
|---|---|---|---|
| backend 整体 | ≥ 80% | `pytest-cov --cov-fail-under=80` | `pyproject.toml` |
| `services/signal_engine.py` | **≥ 95%** | `scripts/check_coverage.py` 解析 coverage.json | `make test-cov-strict` |
| `services/quant_model.py` | **≥ 95%** | 同上 | 同上 |
| `services/notification.py` | **≥ 95%** | 同上 | 同上 |
| 其他 `services/*.py` 与 `adapters/*.py` | ≥ 85% | 同上 | 同上 |
| frontend 整体 | ≥ 60% | `vitest run --coverage` | `vitest.config.ts` |
| frontend 关键组件 | ≥ 80% | 同上 | 同上 |

### 3.2 不计入覆盖率的目录

- `alembic/versions/*` — 自动生成
- `tests/*` — 测试代码本身
- `src/btc_arb/main.py` 的 startup hook（uvicorn 启动入口，由集成测试间接覆盖）
- `src/btc_arb/card_templates/*.json` — 数据文件

具体 exclude 规则写在 `pyproject.toml` 的 `[tool.coverage.run]` 段。

### 3.3 合并统计规则

- 单测 + 集成测试**合并**统计 coverage。
- 命令：`pytest tests/unit tests/integration --cov=src/btc_arb --cov-report=json --cov-report=term-missing`。
- 契约测试单独跑，**不计入**覆盖率（它的目的不是覆盖代码，是验证外部 schema）。

### 3.4 命令统一

| Make 目标 | 说明 |
|---|---|
| `make test` | 仅跑 unit，快速反馈 |
| `make test-cov` | unit + integration + 整体 ≥ 80% 硬卡 |
| `make test-cov-strict` | 同上 + per-file 95/85 硬卡（CI / pre-merge 用） |
| `make test-contract` | 仅跑契约测试，不计 coverage |

---

## 4. 关键模块测试 case 清单（最低要求）

下面是各 P0 模块的必备 case 清单。开发与 QA 同步落到对应文件，PR 评审时按此清单走。

### 4.1 `signal_engine.decide_transition`（≥ 12 case）

| # | from | gap | resolve_at_distance | debounce_active | 期望 transition |
|---|---|---|---|---|---|
| 1 | WATCHING | +0.20 (≥ th) | > 1h | no | ENTERED_LONG / ENTRY_LONG |
| 2 | WATCHING | -0.20 (≤ -th) | > 1h | no | ENTERED_SHORT / ENTRY_SHORT |
| 3 | WATCHING | +0.15 (= th) | > 1h | no | ENTERED_LONG（含等号） |
| 4 | WATCHING | +0.149 (< th) | > 1h | no | None |
| 5 | WATCHING | +0.20 | < 1h | no | None（临近结算） |
| 6 | WATCHING | +0.20 | > 1h | yes | None（去抖窗口内） |
| 7 | ENTERED_LONG | -0.002 | > 1h | no | WATCHING / EXIT_LONG |
| 8 | ENTERED_LONG | -0.001 (= -ε) | > 1h | no | None（边界不触发） |
| 9 | ENTERED_LONG | +0.20 | > 1h | no | None（已入场不再入场） |
| 10 | ENTERED_SHORT | +0.002 | > 1h | no | WATCHING / EXIT_SHORT |
| 11 | ENTERED_SHORT | +0.001 (= ε) | > 1h | no | None |
| 12 | 任意 | 任意 | now >= resolve_at | n/a | EXPIRED |
| 13 | EXPIRED | 任意 | n/a | n/a | None |
| 14 | WATCHING | +0.20 | = 60m00s | no | None（边界严格 <） |
| 15 | WATCHING | +0.20 | = 60m01s | no | ENTERED_LONG |

**额外**：`decide_transition` 必须是纯函数（无 IO、无 DB、无 datetime.now()），所有时间相关参数从入参取。这样测试不需要 freezegun。

### 4.2 `signal_engine.evaluate`（事务/IO 层，集成测试 ≥ 6 case）

放 `tests/integration/test_signal_engine_evaluate.py`：

1. WATCHING → ENTERED_LONG 写 signal_event + 更新 market.state，同事务。
2. 推送失败不回滚 state（mock notification 抛异常，验证 DB 已 commit）。
3. 并发同一 market 触发 evaluate（asyncio.gather × 2），DB 行锁保证只写一条 event。
4. EXPIRED 后 evaluate 直接 return None，不写表。
5. 去抖窗口内连续两次满足条件，只产生一条 event。
6. 状态变更与 signal_event 写入在同事务（手动 raise 后断言两边都未持久化）。

### 4.3 `quant_model`（≥ 5 case）

1. strike 远高于 spot（如 strike=$200K，spot=$100K，vol=0.5）→ P_above 接近 0。
2. strike 远低于 spot（如 strike=$50K，spot=$100K）→ P_above 接近 1。
3. strike 临近 spot（差 < 1%）→ P_above 接近 0.5。
4. vol 极高（vol=2.0）→ 分布宽，P_above 趋向 0.5。
5. vol 极低（vol=0.01）→ 分布窄，远离 strike 时 P_above 接近 0 或 1。
6. above 与 below 方向互补（同 strike + spot + vol，P_above + P_below = 1）。

### 4.4 `llm_adjuster`（≥ 4 case）

1. 正常响应：adjustment 在 ±0.30 内，p_final = clip(p_quant + adjustment) 正确写入。
2. 越界：mock OpenAI 返回 adjustment=0.45 → clip 到 0.30，rationale 加注「越界 clip」。
3. JSON 非法：mock 返回非 schema 形状 → 视为 5xx → 回退纯量化 + `model_version` 后缀 `-llm-fail`、`adjustment=0`、`confidence='low'`。
4. news 为空：adjustment 上限收紧到 ±0.05；mock 返回 0.20 → clip 到 0.05。
5. OpenAI 5xx：重试 3 次后回退（断言 retry 次数 + 最终落到纯量化）。

### 4.5 `polymarket.parse_market_url`（≥ 6 case）

1. `https://polymarket.com/event/bitcoin-above-on-may-17` → slug 正确。
2. `https://polymarket.com/zh/event/bitcoin-above-on-may-17` → slug 正确。
3. `https://polymarket.com/market/bitcoin-above-on-may-17` → slug 正确。
4. 带 query `?utm_source=x` → slug 不含 query。
5. 带 fragment `#section` → slug 不含 fragment。
6. 非 polymarket.com 域名 → 抛 `UrlInvalidError`。
7. 路径不含 `/event/` 或 `/market/` → 抛 `UrlInvalidError`。
8. 空字符串 / None → 抛 `UrlInvalidError`。

### 4.6 `polymarket._extract_strike`（≥ 5 case）

1. `Bitcoin above $108,000 on May 17?` → 108000 / above。
2. `Bitcoin above $1,234,567 on May 17?` → 1234567 / above。
3. `Bitcoin below $90,000 on May 31?` → 90000 / below。
4. `Bitcoin above $108K on May 17?` → 108000（K 后缀支持，如不支持则抛 `MarketNotParsableError`，二选一并断言）。
5. 无 `$` → `MarketNotParsableError`。
6. 含多个 `$`（如 `$108K to $112K`）→ `MarketNotParsableError`。
7. 小数 `$108,000.50` → 108000.50。

### 4.7 `polymarket.get_midpoint` YES token 选取（≥ 2 case）

1. `outcomes = ["Yes", "No"]`, `clobTokenIds = ["t_yes", "t_no"]` → 取 t_yes（index 0）。
2. `outcomes = ["No", "Yes"]`, `clobTokenIds = ["t_no", "t_yes"]` → 取 t_yes（index 1，按 outcome 名称匹配，不是 hardcoded 0）。
3. `outcomes = ["Up", "Down"]` → 抛 `MarketNotBinaryError`（非标准 YES/NO 命名）。

### 4.8 `feishu.render_card`（7 case，全部 JSON 快照）

每种 kind 准备一个 fixture event，渲染后断言：
- 顶部颜色字段（amber/rose/emerald/slate）正确
- 标题中文文案匹配
- 「打开仪表盘详情」按钮 URL 含 `/markets/{id}`
- 「查看市场」按钮 URL 是 Polymarket event URL
- LLM rationale 折叠展开标记存在
- 风险声明 footer 存在

kind 列表：ENTRY_LONG、ENTRY_SHORT、EXIT_LONG、EXIT_SHORT、EXPIRED、test、error。

### 4.9 `notification.push`（≥ 4 case）

1. 一次成功：mock webhook 返回 `{code:0,msg:ok}` → `feishu_pushed=true`、`feishu_push_at` 写入。
2. 失败重试一次成功：第 1 次 5xx、第 2 次 200 → `feishu_retry_count=1`、`feishu_pushed=true`。
3. 失败 3 次：3 次都 5xx → `feishu_error` 含原因、`feishu_pushed=false`、`feishu_retry_count=3`。
4. 并发推送同一 event 幂等：asyncio.gather 调两次 push，断言 webhook 只被 POST 一次（DB 行锁 + `feishu_pushed=true` 短路）。
5. `retry_failed` job：插入 `feishu_pushed=false, feishu_retry_count=2, occurred_at=23h ago` 的 event → 再试 1 次。`occurred_at=25h ago` 的不再扫。

### 4.10 setting 校验（≥ 6 case）

PATCH /settings 各字段越界，断言 422 + 错误信息：

1. `entry_threshold=0.001` → 拒绝（< 0.01）
2. `entry_threshold=0.6` → 拒绝（> 0.50）
3. `debounce_minutes=0` → 拒绝（< 1）
4. `price_poll_minutes=0` → 拒绝
5. `discovery_keywords=[]` → 拒绝（不可为空）
6. `discovery_max_days_to_resolve=400` → 拒绝（> 365）
7. `web_search_provider="unknown"` → 拒绝（不在 enum）

---

## 5. 测试数据 & Fixture 约定

### 5.1 目录结构

```
backend/tests/
├── fixtures/
│   ├── contract/                       # 真实 API capture，schema canary
│   │   ├── polymarket_gamma_btc.json
│   │   ├── polymarket_clob_midpoint.json
│   │   ├── binance_ticker_btcusdt.json
│   │   ├── binance_klines_btcusdt_1h.json
│   │   └── openai_adjuster_response.json
│   ├── builders.py                     # 工厂函数：build_market(), build_prediction(), build_tick()
│   └── conftest.py                     # pytest 通用 fixture（db_session, mock_httpx 等）
├── unit/
├── integration/
└── contract/
```

### 5.2 命名

- 测试文件：`test_<module>.py`（与被测模块同名）。
- 测试类：`Test<Behavior>`（不用 Test 前缀也行，pytest 自动发现就行，统一用 class 分组）。
- 测试函数：`test_<scenario>_<expected>`，例：`test_watching_gap_at_threshold_enters_long`。
- 中文 docstring 描述场景：每个 test 函数第一行 `"""WATCHING + gap = +th，应跃迁 ENTERED_LONG"""`。

### 5.3 工厂模式

`fixtures/builders.py` 提供 `build_market(state="WATCHING", **kwargs)`、`build_prediction(p_ai=0.7, **kwargs)`、`build_tick(p_yes=0.5, **kwargs)`。所有字段都有合理默认，case 只覆盖需要变动的字段。**禁止**每个测试自己构造 dict —— 字段一改全部 case 都得动。

### 5.4 时间处理

- **永远不用** `datetime.now()`：所有时间从测试入参传入，或用 `freezegun.freeze_time("2026-05-17T00:00:00Z")` 装饰器。
- **统一用 UTC aware**：`datetime(2026, 5, 17, tzinfo=timezone.utc)`。
- 断言时间字段时用 `pytest.approx` 容忍 ms 级误差（DB roundtrip 会有微秒丢失）。

---

## 6. Contract Test Fixture 刷新

### 6.1 `scripts/refresh_fixtures.py`

一次性脚本，用真实 API key 跑一遍 5 个端点，把响应写到 `tests/fixtures/contract/*.json`。运行需要：
- `OPENAI_API_KEY`（生产 key，仅读 + 一次调用）
- 公网出站（Polymarket、Binance、OpenAI 都不需 key 也能 read）

执行：

```bash
cd backend
python scripts/refresh_fixtures.py
```

输出：覆盖原 fixture 文件 + 打印差异摘要。**人工 review diff 后再 commit**，不要无脑覆盖。

### 6.2 刷新触发条件

- 每季度定时一次（Q1/Q2/Q3/Q4 第一周 QA 负责）
- smoke.sh 发现某个外部 API 报 schema 解析错误
- 升级 OpenAI 模型版本（`gpt-5` → `gpt-X`）时

### 6.3 fixture commit 规范

每个 fixture 顶部 metadata 字段：

```json
{
  "_metadata": {
    "captured_at": "2026-05-18T03:21:00Z",
    "endpoint": "GET https://gamma-api.polymarket.com/markets?tag=bitcoin&active=true",
    "captured_by": "qa",
    "schema_version": "v1"
  },
  "_payload": { ... 真实响应 ... }
}
```

parser 测试只读 `_payload` 字段。

---

## 7. SOP：Contract Test 红了之后

contract test 红了不是 bug，是**信号**：外部 API 改了，我们要决定是「跟改」还是「忽略」。

1. **第一步：定位**
   - 看哪个 contract test 红：是 schema 字段缺失、改名、还是 enum 值变化？
   - 跑 `git log -- tests/fixtures/contract/<file>.json` 看 fixture 上次刷新时间。

2. **第二步：判断**
   - 是不是真实 API 改了？手动 curl 一次同端点对比 fixture：
     ```bash
     curl 'https://gamma-api.polymarket.com/markets?tag=bitcoin' | jq . > /tmp/now.json
     diff <(jq '._payload' tests/fixtures/contract/polymarket_gamma_btc.json) /tmp/now.json
     ```
   - 真改了 → 第三步。
   - 没改（fixture 老化、capture 时点是边界）→ 跑 `scripts/refresh_fixtures.py` 刷新 + commit fixture，**不改 parser**。

3. **第三步：parser 跟改**
   - 如果是新字段 + 我们用得着 → schemas/Pydantic 加字段、parser 加映射。
   - 如果是字段缺失 + 我们必须有 → 检查是不是 API 把此字段移走了；找新位置或降级。
   - 如果只是不影响我们字段的变动 → 更新 fixture 即可，不动 parser。

4. **第四步：回归**
   - parser 改了 → 跑 `make test-cov-strict` 确保单测仍过。
   - fixture 改了 → 跑 `make test-contract` 确保所有 contract test 绿。
   - 把改动写进 PR 描述：「fixture refresh: Polymarket Gamma 在 X 字段加了 Y 子字段，我们忽略」/「parser 跟改：新增 endDate_iso 替换 endDate（旧的仍兼容）」。

5. **第五步：告知**
   - 在 team-lead 群里 @backend：「Polymarket 改了 schema，已跟改 / 已忽略，详见 PR #X」。
   - 让大家知道这种变动发生过，避免下次重复定位。

---

## 8. 何时跑哪种测试

| 场景 | 跑什么 |
|---|---|
| 改了一个 service 的逻辑 | `pytest tests/unit/test_<service>.py -v` 快速反馈 |
| 准备 PR | `make test-cov-strict` 通过才推 |
| 改了 adapter / 改了 Pydantic schema | 额外跑 `make test-contract` |
| 改了 docker-compose / Dockerfile / 调度配置 | 额外跑 `scripts/smoke.sh`（人工） |
| 每周一上午 | QA 跑一次 `scripts/smoke.sh`，记录 PASS/FAIL |
| OpenAI 升级模型版本 | 跑 `scripts/refresh_fixtures.py` + `make test-contract` + smoke |

---

## 9. 不做的事（明确划界）

- **不引 Playwright / E2E UI 自动化**：v1 个人工具，人工 smoke 够用。
- **不做性能 / 压测**：单机 100 个市场是设计上限，没必要压。
- **不做 AI 预测准确率回测**：Future Scope。
- **不引 mutation testing（mutmut/cosmic-ray）**：v1 不引，覆盖率分级门槛 + 评审兜底已足够。
- **不引 property-based testing（hypothesis）**：v1 不引，但 `quant_model` 与 `decide_transition` 是潜在候选；如果后期发现 hand-written case 漏了边界，可补 hypothesis。
- **不在测试里打真实外部 API**：所有真打都在 smoke.sh 或 contract refresh 脚本里，**主测试套件零网络出站**。
- **不引 vcrpy 自动 capture**：契约测试人工 refresh 更可控，避免 fixture 无序膨胀。

---

## 10. 责任分工

| 范围 | 主负责 | 协作 |
|---|---|---|
| 测试策略文档（本文） | QA | team-lead 评审 |
| 单元测试 case 设计 + 覆盖率达标 | QA | backend 提供「易测」的代码结构（纯函数分离、依赖注入） |
| 集成测试（testcontainers） | QA | backend 协助 fixture 数据准备 |
| 契约测试 + fixture 刷新 | QA | — |
| 前端组件测试 | frontend + QA | QA 评审、QA 提供约定 |
| 手动 smoke.sh | QA | backend 修 bug |
| API schema 漂移响应（SOP §7） | QA 发现 → backend 跟改 | — |

---

## 11. 与 PRD 对照

本文档与 PRD 的关系：

- **backend-PRD §9** 给了 case 数量目标，本文档给了**具体 case 列表 + 优先级 + 覆盖率分级门槛**。
- **frontend-PRD §10** 给了组件测试范围，本文档**承接不细化**。
- 本文档**优先级高于** PRD 的「≥80% 覆盖率」描述：核心模块按 95/85 分级硬卡，整体 80% 是底线不是目标。

---

文档结束。
