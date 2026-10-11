# Polymarket BTC 套利信号工具 · Backend PRD

> 文档版本：v1.0
> 编写日期：2026-05-17
> 依赖文档：`PRD.md`（产品级需求与边界）

---

## 0. 文档读法

本文档面向后端开发与测试，按「架构 → 服务 → 适配器 → 数据 → API → 调度 → 错误 → 观测 → 测试 → 配置 → 部署」十一节描述。所有外部接口必描述到「URL + 鉴权 + 请求/响应字段 + 错误处理」一行能落到代码层。

---

## 1. 架构总览

### 1.1 系统拓扑

```
┌────────────────────────────────────────────────────────────────────┐
│                          docker-compose                             │
│                                                                     │
│  ┌─────────────────────┐         ┌────────────────────────────┐    │
│  │  Next.js (3000)     │ ──REST──▶│      FastAPI (8000)        │    │
│  └─────────────────────┘         │                            │    │
│                                  │ ┌────────────────────────┐ │    │
│                                  │ │ API 层 (routers)        │ │    │
│                                  │ │  /markets /predictions  │ │    │
│                                  │ │  /signals /settings     │ │    │
│                                  │ │  /scheduler ...         │ │    │
│                                  │ └────────────────────────┘ │    │
│                                  │ ┌────────────────────────┐ │    │
│                                  │ │ 服务层                  │ │    │
│                                  │ │  MarketDiscoveryService │ │    │
│                                  │ │  PredictionService      │ │    │
│                                  │ │  PriceMonitorService    │ │    │
│                                  │ │  SignalEngine           │ │    │
│                                  │ │  NotificationService    │ │    │
│                                  │ └────────────────────────┘ │    │
│                                  │ ┌────────────────────────┐ │    │
│                                  │ │ 适配器层 (Protocols)    │ │    │
│                                  │ │  PolymarketClient       │ │    │
│                                  │ │  OpenAIClient           │ │    │
│                                  │ │  WebSearchClient        │ │    │
│                                  │ │  BTCSpotClient          │ │    │
│                                  │ │  FeishuWebhookClient    │ │    │
│                                  │ └────────────────────────┘ │    │
│                                  │ ┌────────────────────────┐ │    │
│                                  │ │ APScheduler             │ │    │
│                                  │ │  daily_discovery        │ │    │
│                                  │ │  price_poll (5m)        │ │    │
│                                  │ │  ai_repredict (24h/mkt) │ │    │
│                                  │ │  price_tick_cleanup     │ │    │
│                                  │ └────────────────────────┘ │    │
│                                  └────────┬───────────────────┘    │
│                                           │                        │
│                                  ┌────────▼─────────┐              │
│                                  │   Postgres 16    │              │
│                                  └──────────────────┘              │
└────────────────────────────────────────────────────────────────────┘
        │
        ▼  外网 HTTPS 出站
        Polymarket Gamma + CLOB / OpenAI / Tavily / 飞书 webhook / Binance Spot
```

### 1.2 技术选型

| 维度 | 选型 | 说明 |
|------|------|------|
| 语言/框架 | Python 3.12 + FastAPI 0.115+ | uvicorn 单 worker（个人使用够用） |
| ORM | SQLAlchemy 2.0 + Alembic | async session |
| 数据库 | Postgres 16 | docker-compose 起 |
| 调度 | APScheduler 3.x (async) | 与 FastAPI 同进程 |
| HTTP 客户端 | httpx (async) | 全部外部 API 走它 |
| LLM SDK | openai 官方 Python SDK | Responses API + structured output |
| 数值/统计 | numpy + scipy.stats | 量化模型 |
| 日志 | structlog | JSON 输出 |
| 重试 | tenacity | 装饰器 |
| 配置 | pydantic-settings | env + DB setting 表两层 |
| 测试 | pytest + pytest-asyncio + httpx.AsyncClient + testcontainers | 集成测试用临时 Postgres |
| Lint | ruff | repo 已有 .ruff_cache，沿用默认 |

### 1.3 目录结构

```
backend/
├── pyproject.toml
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── src/
│   └── btc_arb/
│       ├── __init__.py
│       ├── main.py                    # FastAPI app + APScheduler 启动
│       ├── config.py                  # pydantic-settings env 装载
│       ├── db.py                      # SQLAlchemy session & engine
│       ├── models/                    # ORM
│       │   ├── market.py
│       │   ├── prediction.py
│       │   ├── price_tick.py
│       │   ├── signal_event.py
│       │   ├── setting.py
│       │   └── job_run.py
│       ├── schemas/                   # Pydantic
│       │   ├── market.py
│       │   ├── prediction.py
│       │   ├── signal.py
│       │   ├── setting.py
│       │   └── common.py
│       ├── routers/                   # FastAPI 路由
│       │   ├── markets.py
│       │   ├── predictions.py
│       │   ├── signals.py
│       │   ├── settings.py
│       │   ├── scheduler.py
│       │   └── health.py
│       ├── services/
│       │   ├── market_discovery.py
│       │   ├── prediction.py
│       │   ├── quant_model.py
│       │   ├── llm_adjuster.py
│       │   ├── price_monitor.py
│       │   ├── signal_engine.py
│       │   └── notification.py
│       ├── adapters/
│       │   ├── polymarket.py
│       │   ├── openai_client.py
│       │   ├── websearch.py
│       │   ├── btc_spot.py
│       │   └── feishu.py
│       ├── scheduler/
│       │   ├── jobs.py
│       │   └── runner.py
│       ├── card_templates/            # 飞书卡片 JSON 模板
│       │   ├── entry_long.json
│       │   ├── entry_short.json
│       │   ├── exit_long.json
│       │   ├── exit_short.json
│       │   ├── expired.json
│       │   ├── error.json
│       │   └── test.json
│       ├── logging.py
│       └── exceptions.py
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

---

## 2. 服务层详述

### 2.1 MarketDiscoveryService

**接口**：

```python
class MarketDiscoveryService:
    async def discover_daily(self) -> list[Market]: ...
    async def add_by_url(self, polymarket_url: str) -> tuple[Market, Prediction]: ...
```

**`discover_daily`**：
1. 读 `setting`，取 `discovery_keywords` 与 `discovery_max_days_to_resolve`
2. 调 `PolymarketClient.list_active_markets(keywords)`
3. 过滤：二元 outcome + resolve_at 在 [now, now + max_days] + condition_id 不存在
4. 对每个新市场：写 `market` (state=WATCHING) → 立即 `await prediction_service.predict(market.id)`
5. 写 `job_run` (job_name='daily_discovery', stats={markets_added: N, predictions_made: N})
6. 触发一次 `SignalEngine.evaluate_all_active()`

**`add_by_url`**：
1. `PolymarketClient.parse_market_url(url)` → 取 `slug`
2. `PolymarketClient.get_market_by_slug(slug)` → 元数据
3. 校验：二元、未结算（422 否则）
4. UNIQUE 冲突 → 409
5. 写 market（source='manual'）→ `prediction_service.predict(market.id)`
6. 返回 `(market, prediction)`

**调度**：`daily_discovery` cron `0 0 * * *` UTC。

### 2.2 PredictionService

**接口**：

```python
class PredictionService:
    async def predict(self, market_id: int) -> Prediction: ...
    async def repredict_due(self) -> int:  # APScheduler 调
        """对所有 last_prediction.created_at < now - predict_ttl_hours 且 state!=EXPIRED 的市场重跑"""
```

**`predict` 流程**：
```
1. 读 market
2. quant = await QuantModel.predict(market)
        → (p_quant, spot_price, realized_vol)
3. news = await WebSearchClient.search(
        query="bitcoin",
        time_range="24h",
        limit=5)
4. llm = await LLMAdjuster.adjust(
        market_question=market.question,
        p_quant=quant.p_quant,
        spot=quant.spot,
        vol=quant.vol,
        news=news)
        → (p_final_raw, adjustment_raw, confidence, rationale)
5. clip adjustment 到 ±0.30 (或 ±0.05 若 news 为空)
6. p_ai = clip(p_quant + adjustment, 0.001, 0.999)
7. model_version = "quant-v1+gpt-5"
   若 llm 失败 → "quant-v1+llm-fail",  adjustment=0,  confidence='low'
   若 spot 来源缓存 → 加 "-stale-spot"
8. 写 prediction, 返回
```

**SignalEngine 调用**：写完 prediction 后立即对该市场跑一次 SignalEngine.evaluate（因为新预测可能立刻满足跃迁条件）。

**`repredict_due`** 由 APScheduler 每小时跑一次（`scheduler.jobs.ai_repredict_check`），不是每市场各自一个 cron——这样 1 个 job 处理所有市场。

### 2.3 PriceMonitorService

**接口**：
```python
class PriceMonitorService:
    async def poll_once(self) -> JobRunStats: ...  # 由 APScheduler 调
    async def poll_single(self, market_id: int) -> PriceTick | None: ...  # 调试用
```

**`poll_once` 流程**：
1. 查所有 `state IN ('WATCHING','ENTERED_LONG','ENTERED_SHORT')` 的 market
2. 并发（信号量限制 max=10）调 `PolymarketClient.get_midpoint(condition_id, yes_token_id)`
3. 成功 → 写 `price_tick` → `SignalEngine.evaluate(market_id)`
4. 失败 → 记 `failed_markets` 列表，连续 6 次（查 `price_tick` 最近 6 条都没有该 market 或 6 次 job_run.stats.failed_markets 都含此 market）→ 在 market.metadata（jsonb）里标 `stale=true`
5. 返回 stats `{polled: N, succeeded: M, failed: K, signals_triggered: S}`

**调度**：interval，间隔 = `setting.price_poll_minutes` 分钟（默认 5）。

### 2.4 SignalEngine

**接口**：
```python
class SignalEngine:
    async def evaluate(self, market_id: int) -> SignalEvent | None: ...
    async def evaluate_all_active(self) -> list[SignalEvent]: ...
```

**`evaluate` 流程**（完整伪码）：
```python
async def evaluate(market_id):
    async with db.transaction():
        market = await get_market(market_id, lock="FOR UPDATE")
        if market.state == 'EXPIRED':
            return None

        latest_pred = await get_latest_prediction(market_id)
        latest_tick = await get_latest_price_tick(market_id)
        if latest_pred is None or latest_tick is None:
            return None

        setting = await get_setting()
        now = datetime.now(tz=UTC)

        # 去抖
        if now - market.last_state_change_at < timedelta(minutes=setting.debounce_minutes):
            return None

        # 临近结算 → 强制 EXPIRED
        if now >= market.resolve_at:
            transition = ('EXPIRED', 'EXPIRED')
        # 临近结算 < 1h → 仅 EXPIRED 跃迁，不再产生入场/兑现
        elif (market.resolve_at - now) < timedelta(hours=1):
            return None
        else:
            transition = decide_transition(
                state=market.state,
                gap=latest_pred.p_ai - latest_tick.p_yes,
                entry_th=setting.entry_threshold)

        if transition is None:
            return None

        to_state, kind = transition

        # 写库
        event = SignalEvent(
            market_id=market.id,
            prediction_id=latest_pred.id,
            kind=kind,
            from_state=market.state,
            to_state=to_state,
            p_ai_at_event=latest_pred.p_ai,
            p_mkt_at_event=latest_tick.p_yes,
            gap=latest_pred.p_ai - latest_tick.p_yes)
        db.add(event)

        market.state = to_state
        market.last_state_change_at = now
        await db.commit()

    # 事务外：异步推送
    await notification_service.push(event.id)
    return event


def decide_transition(state, gap, entry_th):
    if state == 'WATCHING':
        if gap >=  entry_th: return ('ENTERED_LONG',  'ENTRY_LONG')
        if gap <= -entry_th: return ('ENTERED_SHORT', 'ENTRY_SHORT')
    if state == 'ENTERED_LONG'  and gap <  -0.001: return ('WATCHING', 'EXIT_LONG')
    if state == 'ENTERED_SHORT' and gap >   0.001: return ('WATCHING', 'EXIT_SHORT')
    return None
```

> 注：`ENTERED_LONG` 的兑现条件原文是 `p_mkt > p_ai`（市场涨到/超过预测点），等价于 `gap = p_ai - p_mkt < 0`，加 ε=0.001 防边界抖动 → `gap < -0.001`。`ENTERED_SHORT` 对称。

### 2.5 NotificationService

**接口**：
```python
class NotificationService:
    async def push(self, signal_event_id: int) -> bool: ...
    async def push_test(self) -> bool: ...
    async def retry_failed(self) -> int: ...  # APScheduler 每 10 分钟跑一次
```

**`push` 流程**：
1. 读 `signal_event` + 关联的 `market` + `prediction`
2. 根据 `kind` 选模板（`card_templates/*.json`），按字段插值
3. `FeishuWebhookClient.send(card_json)`
4. 成功 → 更新 `feishu_pushed=true, feishu_push_at=now()`，返回 True
5. 失败 → 重试 3 次（间隔 10/30/60s 用 tenacity）
6. 重试仍失败 → 更新 `feishu_error=<reason>`，仪表盘 KPI 显示「未推送 N」

**`retry_failed`**：扫 `signal_event WHERE feishu_pushed=false AND feishu_error IS NOT NULL AND feishu_retry_count < 3 AND occurred_at > now() - INTERVAL '24 hours'`，每条最多再试 3 次（用 `signal_event.feishu_retry_count` 列累加，超 3 不再尝试）。

**`push_test`**：发 `card_templates/test.json` 到当前 webhook，不依赖 signal_event。

---

## 3. 适配器层详述

### 3.1 PolymarketClient

**职责**：封装 Polymarket Gamma + CLOB 公共读接口。

**接口**（Protocol）：
```python
class PolymarketClient(Protocol):
    async def list_active_markets(self, keywords: list[str]) -> list[GammaMarket]: ...
    async def get_market_by_slug(self, slug: str) -> GammaMarket: ...
    async def get_midpoint(self, condition_id: str, token_id: str) -> Decimal: ...
    def parse_market_url(self, url: str) -> str: ...  # → slug
```

**实现要点**：

- **Gamma base URL**: `https://gamma-api.polymarket.com`
  - `GET /markets?active=true&closed=false&limit=500&offset=0`（分页全拉，本地按 keyword 过滤；Gamma 不提供全文搜索）
  - 关心字段：`id`, `slug`, `question`, `description`, `outcomes`, `outcomePrices`, `clobTokenIds`, `endDate`, `conditionId`, `active`, `closed`

- **CLOB base URL**: `https://clob.polymarket.com`
  - `GET /midpoint?token_id={token_id}` → `{ "mid": "0.52" }`
  - 用 YES outcome 对应的 `clobTokenIds[0]`（YES 一般是第 0 个，需对照 `outcomes` 数组验证）

- **URL 解析**：支持
  - `https://polymarket.com/event/{slug}`
  - `https://polymarket.com/zh/event/{slug}`
  - `https://polymarket.com/market/{slug}`
  - 末尾 `?`/`#` 切掉

- **Strike 解析**：market.question 通常形如 `Bitcoin above $108,000 on May 17?`。用正则提取 `\$(\d{1,3}(,\d{3})*)` → 解析为数字；direction 关键词 `above` / `below`；解析失败 → 拒绝（422，`MARKET_NOT_PARSABLE`）。

- **Rate limit**：Gamma 公开接口约 60 req/min，本地节流 30 req/min；CLOB midpoint 单市场单次 < 100ms，并发 10 个即可。

- **超时**：httpx default 5s；重试用 tenacity 3 次（指数退避）。

### 3.2 OpenAIClient

**职责**：封装 OpenAI Responses API + structured output + web_search tool（仅当 setting.web_search_provider='openai' 时启用，v1 默认 Tavily，所以这里不开 web_search tool）。

**接口**：
```python
class OpenAIClient(Protocol):
    async def call_adjuster(
        self,
        market_question: str,
        p_quant: float,
        spot: float,
        vol: float,
        news: list[NewsItem],
    ) -> AdjusterOutput: ...
```

**Prompt 结构**（System + User）：

System:
```
You are a quantitative trading analyst evaluating Polymarket binary prediction markets
on Bitcoin price events. Given a quantitative baseline probability and recent news,
output an adjusted probability with rationale.

Constraints:
- adjustment ∈ [-0.30, 0.30] if news provided, else [-0.05, 0.05]
- p_final = clip(p_quant + adjustment, 0.001, 0.999)
- rationale: 100-300 chars Chinese
- confidence: low (news weak/contradictory) | medium | high (multiple corroborating signals)
```

User:
```
Market: {market_question}
Quant baseline P(YES): {p_quant:.4f}  (BTC spot ${spot:.2f}, annualized realized vol {vol:.2%})
Recent news (last 24h):
1. [{news[0].title}] {news[0].snippet}
2. ...
```

**Response format**: `response_format = {"type": "json_schema", "json_schema": AdjusterSchema}`。
**Model**: `setting.openai_model`（默认 `gpt-5`，可改）。
**Temperature**: 0.3。
**Timeout**: 30s。
**Retry**: 3 次（1/4/16s 退避），失败抛 `LLMUnavailableError`（上层回退到纯量化）。

### 3.3 WebSearchClient

**职责**：抽象 Web 搜索接口；v1 默认 Tavily。

**接口**：
```python
class WebSearchClient(Protocol):
    async def search(self, query: str, time_range: str = "24h", limit: int = 5) -> list[NewsItem]: ...

class NewsItem(BaseModel):
    title: str
    url: str
    snippet: str
    published_at: datetime | None
```

**Tavily 实现**：
- `POST https://api.tavily.com/search`
- Headers: `Authorization: Bearer {api_key}`
- Body: `{ "query": "bitcoin", "days": 1, "max_results": 5, "search_depth": "basic" }`
- 失败 → 返回 `[]`（不抛异常，触发 LLM 走「无新闻」路径）

### 3.4 BTCSpotClient

**职责**：拉 BTC 现货价 + 历史 K 线，算实现波动率。

**接口**：
```python
class BTCSpotClient(Protocol):
    async def get_spot(self) -> Decimal: ...
    async def get_realized_vol(self, lookback_days: int = 30, interval: str = "1h") -> Decimal:
        """年化对数收益率标准差"""
```

**Binance 实现**：
- Spot: `GET https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT` → `{ "symbol":"BTCUSDT","price":"..." }`
- K 线: `GET https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=720`（30 天 = 720 小时）
- 算法：
  ```
  closes = [float(k[4]) for k in klines]
  log_returns = np.diff(np.log(closes))
  sigma_hourly = np.std(log_returns)
  sigma_annual = sigma_hourly * sqrt(24 * 365)
  ```

**缓存**：每次 spot/vol 取后写 redis-less 的本地 dict（TTL 60s）；外部 API 失败时返回最近一次缓存值，并通知调用方 `stale=True`。

### 3.5 FeishuWebhookClient

**职责**：把卡片 JSON POST 到飞书自定义机器人。

**接口**：
```python
class FeishuWebhookClient(Protocol):
    async def send(self, card: dict) -> FeishuSendResult:
        """raises FeishuPushError on 4xx/5xx after retries"""
```

**飞书自定义机器人 webhook**：
- URL 由 `setting.feishu_webhook_url` 提供（用户在飞书群里「添加机器人 → 自定义机器人」拿）
- POST body: `{ "msg_type": "interactive", "card": {...} }`
- 返回: `{ "code": 0, "msg": "ok" }` 表示成功；非 0 视为失败
- 重试 3 次（10/30/60s）；超出抛 `FeishuPushError`
- 卡片模板见 `card_templates/*.json`，含 `${variable}` 占位符，发送前用 Python `string.Template` 替换

---

## 4. 数据模型（完整 DDL）

```sql
-- 1. setting (single-row global config)
CREATE TABLE setting (
    id                              integer PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    entry_threshold                 numeric(4,3)   NOT NULL DEFAULT 0.150,
    debounce_minutes                integer        NOT NULL DEFAULT 10 CHECK (debounce_minutes >= 1),
    price_poll_minutes              integer        NOT NULL DEFAULT 5  CHECK (price_poll_minutes >= 1),
    predict_ttl_hours               integer        NOT NULL DEFAULT 24 CHECK (predict_ttl_hours >= 1),
    discovery_keywords              text[]         NOT NULL DEFAULT ARRAY['bitcoin','btc'],
    discovery_max_days_to_resolve   integer        NOT NULL DEFAULT 30,
    feishu_webhook_url              text,
    openai_api_key                  text,
    openai_model                    text           NOT NULL DEFAULT 'gpt-5',
    web_search_provider             text           NOT NULL DEFAULT 'tavily' CHECK (web_search_provider IN ('tavily','exa','brave','openai')),
    web_search_api_key              text,
    updated_at                      timestamptz    NOT NULL DEFAULT now()
);

-- 2. market
CREATE TABLE market (
    id                          bigserial PRIMARY KEY,
    condition_id                text NOT NULL UNIQUE,
    slug                        text NOT NULL,
    question                    text NOT NULL,
    description                 text,
    strike_price                numeric(20,8),
    direction                   text CHECK (direction IN ('above','below')),
    resolve_at                  timestamptz NOT NULL,
    outcome_yes_token_id        text NOT NULL,
    outcome_no_token_id         text NOT NULL,
    state                       text NOT NULL DEFAULT 'WATCHING'
                                CHECK (state IN ('WATCHING','ENTERED_LONG','ENTERED_SHORT','EXPIRED')),
    source                      text NOT NULL CHECK (source IN ('discovery','manual')),
    metadata                    jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at                  timestamptz NOT NULL DEFAULT now(),
    last_state_change_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX market_state_active_idx ON market (state) WHERE state <> 'EXPIRED';
CREATE INDEX market_resolve_at_idx ON market (resolve_at);

-- 3. prediction
CREATE TABLE prediction (
    id              bigserial PRIMARY KEY,
    market_id       bigint NOT NULL REFERENCES market(id) ON DELETE CASCADE,
    p_ai            numeric(5,4) NOT NULL CHECK (p_ai BETWEEN 0 AND 1),
    p_quant         numeric(5,4) NOT NULL CHECK (p_quant BETWEEN 0 AND 1),
    llm_adjustment  numeric(6,4) NOT NULL,
    llm_confidence  text CHECK (llm_confidence IN ('low','medium','high')),
    llm_rationale   text,
    news_sources    jsonb NOT NULL DEFAULT '[]'::jsonb,
    spot_price      numeric(20,8),
    realized_vol    numeric(8,6),
    model_version   text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX prediction_market_created_idx ON prediction (market_id, created_at DESC);

-- 4. price_tick
CREATE TABLE price_tick (
    id              bigserial PRIMARY KEY,
    market_id       bigint NOT NULL REFERENCES market(id) ON DELETE CASCADE,
    p_yes           numeric(5,4) NOT NULL CHECK (p_yes BETWEEN 0 AND 1),
    p_no            numeric(5,4),
    midpoint_source text NOT NULL DEFAULT 'clob_midpoint',
    fetched_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX price_tick_market_fetched_idx ON price_tick (market_id, fetched_at DESC);

-- 5. signal_event
CREATE TABLE signal_event (
    id              bigserial PRIMARY KEY,
    market_id       bigint NOT NULL REFERENCES market(id) ON DELETE CASCADE,
    prediction_id   bigint NOT NULL REFERENCES prediction(id),
    kind            text NOT NULL CHECK (kind IN ('ENTRY_LONG','ENTRY_SHORT','EXIT_LONG','EXIT_SHORT','EXPIRED')),
    from_state      text NOT NULL,
    to_state        text NOT NULL,
    p_ai_at_event   numeric(5,4) NOT NULL,
    p_mkt_at_event  numeric(5,4) NOT NULL,
    gap             numeric(6,4) NOT NULL,
    feishu_pushed   boolean NOT NULL DEFAULT false,
    feishu_push_at  timestamptz,
    feishu_error    text,
    feishu_retry_count integer NOT NULL DEFAULT 0,
    occurred_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX signal_event_market_occurred_idx ON signal_event (market_id, occurred_at DESC);
CREATE INDEX signal_event_unpushed_idx ON signal_event (occurred_at) WHERE feishu_pushed = false;

-- 6. job_run
CREATE TABLE job_run (
    id           bigserial PRIMARY KEY,
    job_name     text NOT NULL,
    status       text NOT NULL CHECK (status IN ('running','success','failed')),
    started_at   timestamptz NOT NULL DEFAULT now(),
    finished_at  timestamptz,
    stats        jsonb NOT NULL DEFAULT '{}'::jsonb,
    error        text
);
CREATE INDEX job_run_name_started_idx ON job_run (job_name, started_at DESC);
```

**Seed**：`alembic` 第一个 revision 创建表后立即插入 `setting (id=1)` 默认行。

---

## 5. REST API 详细 spec

> 所有响应 JSON；UTF-8；时间字段 ISO8601 + `Z`；错误统一格式：
> ```json
> {"error": {"code": "MARKET_NOT_FOUND", "message": "...", "details": {...}}}
> ```

### 5.1 markets

#### `GET /api/v1/markets`

Query:
- `state` (optional): `WATCHING|ENTERED_LONG|ENTERED_SHORT|EXPIRED`
- `source` (optional): `discovery|manual`
- `limit` (default 50, max 200)
- `offset` (default 0)

200:
```json
{
  "items": [
    {
      "id": 1,
      "condition_id": "0x...",
      "slug": "bitcoin-above-on-may-17",
      "question": "Bitcoin above $108,000 on May 17?",
      "strike_price": "108000.00000000",
      "direction": "above",
      "resolve_at": "2026-05-17T12:00:00Z",
      "state": "ENTERED_LONG",
      "source": "discovery",
      "created_at": "2026-05-10T00:00:00Z",
      "last_state_change_at": "2026-05-15T08:30:00Z",
      "latest_prediction": {
        "p_ai": "0.7200",
        "model_version": "quant-v1+gpt-5",
        "created_at": "2026-05-15T00:00:00Z"
      },
      "latest_price": {
        "p_yes": "0.5500",
        "fetched_at": "2026-05-15T08:35:00Z"
      },
      "gap": "0.1700"
    }
  ],
  "total": 23
}
```

#### `GET /api/v1/markets/{id}`

200: 同上单条 + 额外 `metadata` 字段。
404: market not found.

#### `POST /api/v1/markets`

Body:
```json
{ "polymarket_url": "https://polymarket.com/event/bitcoin-above-on-may-17" }
```

200:
```json
{ "market": {...}, "prediction": {...} }
```

422 错误码：
- `URL_INVALID` (URL 解析失败)
- `MARKET_NOT_FOUND` (Polymarket 返回 404)
- `MARKET_NOT_BINARY` (outcomes != 2)
- `MARKET_RESOLVED` (closed=true 或 resolve_at < now)
- `MARKET_NOT_PARSABLE` (无法解析 strike/direction)

409: 已存在（返回现有 market.id）

#### `DELETE /api/v1/markets/{id}`

软删：`UPDATE market SET state='EXPIRED' WHERE id=$1`。
204 No Content.

#### `GET /api/v1/markets/{id}/price_ticks`

Query: `from` (ISO), `to` (ISO), `granularity` (raw|hourly, default raw)

200:
```json
{
  "items": [
    {"p_yes": "0.5500", "fetched_at": "2026-05-15T08:35:00Z"},
    {"p_yes": "0.5520", "fetched_at": "2026-05-15T08:40:00Z"}
  ]
}
```

`granularity=hourly` 时后端按小时聚合（最后一个 tick）。

#### `GET /api/v1/markets/{id}/predictions`

200:
```json
{
  "items": [
    {
      "id": 12,
      "p_ai": "0.7200",
      "p_quant": "0.6800",
      "llm_adjustment": "0.0400",
      "llm_confidence": "medium",
      "llm_rationale": "近期...",
      "news_sources": [{"title": "...", "url": "...", "snippet": "..."}],
      "spot_price": "107500.00000000",
      "realized_vol": "0.450000",
      "model_version": "quant-v1+gpt-5",
      "created_at": "2026-05-15T00:00:00Z"
    }
  ]
}
```

#### `POST /api/v1/markets/{id}/repredict`

立即重跑预测（不等 24h TTL）。

200: 新 prediction。

### 5.2 signals

#### `GET /api/v1/signals`

Query: `kind` (optional), `market_id` (optional), `from`, `to`, `limit` (default 50)

200:
```json
{
  "items": [
    {
      "id": 88,
      "market": {"id": 1, "question": "...", "slug": "..."},
      "prediction": {"p_ai": "0.7200", "model_version": "..."},
      "kind": "ENTRY_LONG",
      "from_state": "WATCHING",
      "to_state": "ENTERED_LONG",
      "p_ai_at_event": "0.7200",
      "p_mkt_at_event": "0.5500",
      "gap": "0.1700",
      "feishu_pushed": true,
      "feishu_push_at": "2026-05-15T08:35:12Z",
      "feishu_error": null,
      "occurred_at": "2026-05-15T08:35:10Z"
    }
  ]
}
```

#### `GET /api/v1/signals/{id}`

200: 单条详情（含完整 prediction.rationale 与 news_sources）。

### 5.3 predict

#### `POST /api/v1/predict`

「试一次不入库」。

Body: `{ "polymarket_url": "..." }`

200:
```json
{
  "market_preview": {
    "question": "...",
    "strike_price": "108000.00000000",
    "direction": "above",
    "resolve_at": "..."
  },
  "prediction": {
    "p_ai": "0.7200",
    "p_quant": "0.6800",
    "llm_adjustment": "0.0400",
    "llm_confidence": "medium",
    "llm_rationale": "...",
    "news_sources": [...],
    "spot_price": "107500",
    "realized_vol": "0.4500",
    "model_version": "quant-v1+gpt-5"
  }
}
```

错误码同 `POST /markets`，但不含 409（不入库自然不冲突）。

### 5.4 settings

#### `GET /api/v1/settings`

200（敏感字段 mask）：
```json
{
  "entry_threshold": "0.150",
  "debounce_minutes": 10,
  "price_poll_minutes": 5,
  "predict_ttl_hours": 24,
  "discovery_keywords": ["bitcoin","btc"],
  "discovery_max_days_to_resolve": 30,
  "feishu_webhook_url": "https://open.feishu.cn/...***hidden***",
  "openai_api_key": "sk-...***hidden***",
  "openai_model": "gpt-5",
  "web_search_provider": "tavily",
  "web_search_api_key": "tvly-...***hidden***",
  "updated_at": "2026-05-10T12:00:00Z"
}
```

#### `PATCH /api/v1/settings`

Body 部分字段，全部可选。校验：
- `entry_threshold` ∈ [0.01, 0.50]
- `debounce_minutes` ≥ 1
- `price_poll_minutes` ≥ 1
- `predict_ttl_hours` ≥ 1
- `discovery_keywords` 非空 list[str]
- `discovery_max_days_to_resolve` ∈ [1, 365]
- `web_search_provider` ∈ enum

200: 同 GET（含变更后的 masked 版本）。

变更后立即生效：`price_poll_minutes` 变化时 `apscheduler.reschedule_job('price_poll', interval=...)`。

#### `POST /api/v1/settings/test_feishu`

无 body。返回:
```json
{ "ok": true, "status": 200, "response": {"code": 0, "msg": "ok"} }
```
或
```json
{ "ok": false, "status": 400, "error": "Invalid webhook URL" }
```

### 5.5 scheduler

#### `GET /api/v1/scheduler/jobs`

200:
```json
{
  "items": [
    {"name": "daily_discovery", "trigger": "cron", "next_run_at": "2026-05-16T00:00:00Z"},
    {"name": "price_poll",      "trigger": "interval", "interval_minutes": 5, "next_run_at": "2026-05-15T08:40:00Z"},
    {"name": "ai_repredict_check","trigger": "interval", "interval_minutes": 60, "next_run_at": "2026-05-15T09:00:00Z"},
    {"name": "feishu_retry",    "trigger": "interval", "interval_minutes": 10, "next_run_at": "2026-05-15T08:45:00Z"},
    {"name": "price_tick_cleanup","trigger": "cron", "next_run_at": "2026-05-16T03:00:00Z"}
  ]
}
```

#### `GET /api/v1/scheduler/runs`

Query: `job_name` (optional), `status` (optional), `limit` (default 50)

200:
```json
{
  "items": [
    {
      "id": 102,
      "job_name": "price_poll",
      "status": "success",
      "started_at": "2026-05-15T08:35:00Z",
      "finished_at": "2026-05-15T08:35:08Z",
      "stats": {"polled": 23, "succeeded": 23, "failed": 0, "signals_triggered": 1},
      "error": null
    }
  ]
}
```

#### `POST /api/v1/scheduler/trigger`

Body:
```json
{ "job": "daily_discovery" }
```
或
```json
{ "job": "ai_repredict", "market_id": 5 }
```

200: `{ "job_run_id": 103 }`。job 在后台跑，前端可轮询 `/scheduler/runs`。

### 5.6 health

`GET /api/v1/healthz` → `{"status":"ok"}` (200, 用于 docker healthcheck)

`GET /api/v1/readyz` → 检查 DB + Polymarket + OpenAI + Feishu webhook + Binance 可达（并发 ping），返回每项状态：
```json
{
  "status": "degraded",
  "components": {
    "db": "ok",
    "polymarket_gamma": "ok",
    "polymarket_clob": "ok",
    "openai": "ok",
    "tavily": "ok",
    "feishu": "fail: 404",
    "binance": "ok"
  }
}
```
任意 fail → HTTP 503；全 ok → 200。

---

## 6. 调度任务详细 spec

| 名称 | 触发器 | 默认时间 | 行为 | 失败处理 |
|------|--------|---------|------|---------|
| `daily_discovery` | cron `0 0 * * *` UTC | 每日 00:00 UTC | 调 MarketDiscoveryService.discover_daily | 写 job_run failed；下次 cron 自动再试 |
| `price_poll` | interval | 每 5 分钟（`setting.price_poll_minutes`） | 调 PriceMonitorService.poll_once | 单市场失败不影响其他；6 次连续失败标 stale |
| `ai_repredict_check` | interval | 每 1 小时 | 查所有 `last_prediction < now - predict_ttl_hours` 的 market，依次跑预测 | 单市场失败写 job_run、继续下一个 |
| `feishu_retry` | interval | 每 10 分钟 | 调 NotificationService.retry_failed | 静默失败 |
| `price_tick_cleanup` | cron `0 3 * * *` UTC | 每日 03:00 UTC | `DELETE FROM price_tick WHERE fetched_at < now() - INTERVAL '30 days'` | 写 job_run |

**APScheduler 配置**：
- jobstore: `MemoryJobStore`（单实例，重启从代码注册重建）
- executor: `AsyncIOExecutor`
- coalesce: `True`（重启后只补一次落下的）
- max_instances: 1（同一 job 不重叠）
- misfire_grace_time: 60s

**job_run 生命周期**：进入 job 时插一条 `status='running'`；正常退出更新为 `success`；抛异常更新为 `failed` + `error`。

---

## 7. 错误处理矩阵

| 错误源 | 类型 | 影响 | 处理 | 用户感知 |
|--------|------|------|------|----------|
| Polymarket Gamma | 5xx / timeout | discovery 失败 | tenacity 重试 3×；仍失败 job_run failed；连续 3 次 daily 失败 → 推送「工具异常」飞书卡片 | UI 调度页红条 |
| Polymarket CLOB | 5xx / 空 mid | 单 tick 失败 | 本市场本轮跳过；连续 6 次 → market.metadata.stale=true | 卡片灰显 + 悬停提示 |
| OpenAI | 5xx / rate limit | 预测 LLM 阶段失败 | tenacity 3×（1/4/16s）；仍失败 → 纯量化预测 + model_version `-llm-fail` | 详情页标「LLM 调整不可用」 |
| OpenAI 非合法 JSON | 输出错乱 | 同上 | structured output 已强约束；万一失败按 5xx | 同上 |
| Web 搜索 | 5xx / 空 | LLM 输入缺失 | 返回空 list；LLM 走「无新闻」路径，adjustment clip ±0.05 | UI 详情页「无近期新闻」 |
| Binance | 5xx / timeout | QuantModel 输入缺失 | 用 60s 缓存值；标 `model_version` `-stale-spot` | 详情页「现货数据滞后」 |
| 飞书 webhook | 4xx/5xx | 信号已生成未送达 | 同步重试 3×（10/30/60s）；仍失败标 `feishu_error`；后台 `feishu_retry` job 每 10 分钟扫一次，最多再试 3 次 | 仪表盘 KPI「未推送 N」红色 |
| DB 连接断开 | Postgres 异常 | 全系统下线 | uvicorn healthcheck 失败 → docker-compose 自动重启 | 前端 502 |
| 手动 URL 解析失败 | 用户输入异常 | 单请求失败 | 422 + 错误码 | 前端表单 inline 错误 |
| APScheduler 抛异常 | 框架异常 | 单 job 漏跑 | misfire_grace_time + coalesce 兜底；记 job_run failed | 调度面板红条 |
| 同时跑两个 backend | 状态竞争 | 状态机不一致 | DB 行锁部分缓解，但 v1 不支持 | README 注明「单实例」 |

**统一异常体系**（`exceptions.py`）：

```python
class AppError(Exception): code: str
class PolymarketError(AppError): code = "POLYMARKET_UNAVAILABLE"
class LLMUnavailableError(AppError): code = "LLM_UNAVAILABLE"
class WebSearchEmptyError(AppError): code = "WEBSEARCH_EMPTY"  # 非异常，info 级别
class SpotUnavailableError(AppError): code = "SPOT_UNAVAILABLE"
class FeishuPushError(AppError): code = "FEISHU_PUSH_FAILED"
class MarketNotSupportedError(AppError): code = "MARKET_NOT_SUPPORTED"
class MarketNotBinaryError(AppError): code = "MARKET_NOT_BINARY"
class MarketResolvedError(AppError): code = "MARKET_RESOLVED"
class MarketNotParsableError(AppError): code = "MARKET_NOT_PARSABLE"
class UrlInvalidError(AppError): code = "URL_INVALID"
```

FastAPI 全局异常处理器把 `AppError` 转 422 + `{error: {code, message}}`，其它 5xx 转 500 + `INTERNAL_ERROR`。

---

## 8. 日志与观测

### 8.1 结构化日志

- structlog JSON 输出到 stdout
- 必带字段：`timestamp`(UTC ISO+Z), `level`, `event`, `logger`
- 上下文字段：`request_id`(FastAPI middleware 注入), `job_run_id`, `market_id`, `condition_id`
- 关键事件单独 event 名：`market.discovered`, `prediction.completed`, `signal.fired`, `feishu.pushed`, `feishu.failed`, `job.started`, `job.finished`

示例：
```json
{"timestamp":"2026-05-15T08:35:12Z","level":"info","event":"signal.fired","market_id":1,"condition_id":"0x...","kind":"ENTRY_LONG","p_ai":0.72,"p_mkt":0.55,"gap":0.17,"signal_event_id":88}
```

### 8.2 日志输出与轮转

- docker stdout/stderr → docker logs（默认 json-file driver）
- 单文件 max 50MB，保留 7 个文件（docker-compose 配置 logging driver options）
- 不接 ELK / Loki（v1 个人范围）

### 8.3 业务可观测面板

- 仪表盘 KPI 区：监控中市场数 / 今日发现 / 今日推送 / 未推送（红字）/ 距下次 daily_discovery
- 调度页：所有 job 当前状态 + 最近 50 次 job_run
- 历史页：所有 signal_event + 推送状态

---

## 9. 测试策略

### 9.1 单元测试（pytest）

覆盖率目标 ≥ 80%（pytest-cov），关键服务 ≥ 90%。

**关键 case 清单**：

| 模块 | case 数量 | 说明 |
|------|----------|------|
| `quant_model.py` | ≥ 5 | strike 远高/远低/临近 spot；vol 极高/极低；direction above/below |
| `llm_adjuster.py` | ≥ 4 | 正常响应；越界 clip；JSON 非法；news 为空 |
| `signal_engine.decide_transition` | ≥ 12 | 所有 from×to 跃迁 + 边界（gap < ε、临近结算、去抖窗口内） |
| `polymarket.parse_market_url` | ≥ 6 | en/zh 路径、market/event 路径、带 query、空 URL、非 polymarket 域名 |
| `polymarket._extract_strike` | ≥ 5 | `$108,000` / `$1,234,567` / 无 $ / 多个 $ / 小数 |
| `feishu.render_card` | 7 | 5 种 kind + 测试卡 + error 卡，每种 JSON 结构快照 |
| `notification.push` | ≥ 4 | 成功、重试成功、重试 3 次后失败、并发推送同一 event 幂等 |
| `setting` 校验 | ≥ 6 | 各字段越界拒绝 |

### 9.2 集成测试

- TestClient + testcontainers-postgres 起临时 DB
- `PredictionService.predict()` 端到端：mock OpenAI、Tavily、Binance 适配器 → 真跑 quant_model + llm_adjuster → 断言 prediction 写表正确
- `POST /api/v1/markets` 端到端：mock Polymarket Client → 真跑 service → 断言 market + prediction 都入库
- `price_poll` 一轮：插 3 个 market + mock CLOB → 跑 job → 断言 3 条 tick + 1 条 signal_event（设置满足）
- 飞书推送 mock httpx 端口 → 验证 retry/失败标记

### 9.3 手动验收脚本

`scripts/smoke.sh`：
1. `docker-compose up -d` 等 healthcheck 绿
2. `curl -X POST http://localhost:8000/api/v1/markets -d '{"polymarket_url":"<真实 BTC 市场 URL>"}'`
3. 等 30s，查 `/markets/{id}/predictions` 有结果
4. 调 `/scheduler/trigger { job: 'price_poll' }`
5. 直接改 DB 把 market.state 改 WATCHING、把最新 prediction.p_ai 改成远离 market mid 的值
6. 再 trigger price_poll
7. 检查飞书群是否收到 ENTRY 卡片

### 9.4 不做

- E2E UI 自动化（Playwright 等）
- 性能/压测
- AI 预测准确率回测（Future Scope）

---

## 10. 配置与环境变量

### 10.1 `.env.example`

```bash
# Postgres
DATABASE_URL=postgresql+asyncpg://btc_arb:btc_arb@db:5432/btc_arb

# Web
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=info

# 仅用于 bootstrap（首次启动写入 setting 表），运行时改设置走 PATCH /settings
BOOTSTRAP_OPENAI_API_KEY=
BOOTSTRAP_WEB_SEARCH_API_KEY=
BOOTSTRAP_FEISHU_WEBHOOK_URL=
```

### 10.2 配置加载优先级

1. ENV 变量（pydantic-settings）：仅 infra 类（DATABASE_URL、APP_HOST、LOG_LEVEL）
2. `setting` 表（DB 单行）：所有业务参数（阈值、密钥、调度间隔等）
3. 首次启动时 ENV `BOOTSTRAP_*` 写入 `setting` 表（仅在该字段为 NULL 时）

### 10.3 密钥处理

- DB 字段明文存储（v1 个人本地使用，简单优先）；不入 git；docker volume 挂出 `pgdata` 自管
- GET /settings 返回时 mask（保留前 6 / 后 4 字符）
- 日志/异常 message 中绝不打印密钥（structlog filter 拦截 `api_key`/`webhook_url` 字段）

---

## 11. 部署

### 11.1 docker-compose.yml

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: btc_arb
      POSTGRES_PASSWORD: btc_arb
      POSTGRES_DB: btc_arb
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U btc_arb"]
      interval: 5s
      retries: 10
    ports: ["127.0.0.1:5432:5432"]

  backend:
    build: ./backend
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    ports: ["127.0.0.1:8000:8000"]
    command: >
      sh -c "alembic upgrade head &&
             uvicorn btc_arb.main:app --host 0.0.0.0 --port 8000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3

  frontend:
    build: ./frontend
    env_file: .env
    depends_on:
      backend:
        condition: service_healthy
    ports: ["127.0.0.1:3000:3000"]
    environment:
      NEXT_PUBLIC_API_BASE: http://localhost:8000/api/v1
    restart: unless-stopped

volumes:
  pgdata:
```

### 11.2 backend Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic
ENV PYTHONPATH=/app/src
```

### 11.3 启动顺序

1. `docker-compose up -d db` → 等 healthy
2. `docker-compose up -d backend` → `alembic upgrade head` 自动跑，建表 + seed setting
3. `docker-compose up -d frontend`
4. 浏览器开 `http://localhost:3000` → /settings 配 OpenAI/Tavily/Feishu key
5. /settings 点「发送测试卡片」验证飞书可达
6. /scheduler 点 daily_discovery 手动触发一次，等数据

### 11.4 升级/迁移

- DB schema 改动统一走 alembic
- v1 不做蓝绿/滚动；停容器 → 升级镜像 → 重启
- 数据备份：`pg_dump btc_arb` 写出 cron（README 注明）

---

文档结束。前端实现见 `frontend-PRD.md`。
