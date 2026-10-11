# quant-trader v1 — Design

**Date:** 2026-05-17
**Status:** Approved for implementation planning
**Scope:** v1（首个能跑通的版本）
**Authors:** locey + Claude (via superpowers:brainstorming)

---

## 1. Purpose

构建一个独立的、可在 Binance Testnet 上跑通"策略 → 回测 → 实时纸交易 / 模拟下单 → 前端展示"完整闭环的小型量化交易系统。v1 不接 Binance 主网（主网适配器代码骨架预留，v2 启用）。

本项目**逻辑上独立**（不是 ai_lesson 的课程内容），物理上落地在 `ai_lesson/lesson6/project/` **原地演进**——保留并扩展现有的 `backtest.py` / `strategies/dual_ma.py` / `seed_db.py`，扫掉课程残留的 `openspec/` / `plans/` / `reports/` / `.claude/skills/backtest/` 等。这意味着 ai_lesson 仓库内的 `lesson6/project/` 从"课程项目快照"被重新定义为"quant-trader 产品代码"。

## 2. v1 范围

### In scope（v1 必交付）

- 策略库扩展：在 `dual_ma` 之外新增 `rsi` / `macd` / `bollinger`，全部满足 `def strategy(df, **params) -> Series` 签名
- 回测：可视化触发 `backtest.run_backtest()`，渲染 Sharpe / max_drawdown / win_rate / cum_return + PNG 曲线
- 实时纸交易：bar-close（分钟级 1m/5m/15m/1h）触发，多 bot 并发，每个 bot 独立纸面账户
- Binance Testnet 适配器：实现同一 `Exchange` 接口，UI 可选 `paper` 或 `binance_testnet` 模式
- 前端：FastAPI + Jinja2 + HTMX 的 server-side rendered web，覆盖 /backtest /bots /bots/{id} /strategies
- 单测 + 集成测覆盖率 ≥ 80%，CI（GitHub Actions）跑全部测试

### Out of scope（推到 v2+）

- Binance 主网（real-money）实际下单
- 风控参数：止损 / 止盈 / 仓位上限 / 最大回撤熔断
- 多账户 / 多用户（v1 单用户）
- WebSocket 实时 tick 行情（v1 用 REST 轮询）
- 独立 worker 进程（v1 monolith；架构上保证可拆）
- 策略参数搜索 / 回测参数扫描
- 手续费可配（v1 硬编码 paper 单边 0.1%）

### 已知 v1 边界（文档披露，不在 v1 修）

1. **多 bot 共享 testnet 账户**：testnet 模式下多个 bot 打到同一 Binance testnet 子账户，订单互相可见，仓位混在一起。v1 在 README 警示"testnet 建议同时只开一个 bot"。
2. **Warmup 期信号 = 0**：策略输入 K 线数 < 参数窗口时，signal=0，无交易。与现有 dual_ma 行为一致。
3. **手续费**：paper 撮合固定 0.1% 单边，写入 `fills.fee`；testnet 走 Binance 实际计费。
4. **回测不入库**：每次回测一次性查询，结果不持久化；如需复跑，重新提交表单。

## 3. 架构概览

**形态**：单 Python 进程 monolith + APScheduler（in-process）+ SQLite。

```
┌────────────────────────── one Python process ──────────────────────────┐
│  FastAPI app                                                             │
│   ├─ Web routes (Jinja2 + HTMX partials)                                │
│   ├─ APScheduler (SQLAlchemyJobStore, persists to quant.db)             │
│   ├─ BotRunner.tick()  ← Scheduler 触发                                  │
│   ├─ Strategy registry (dual_ma / rsi / macd / bollinger)               │
│   ├─ KlineSource (Binance REST 轮询)                                     │
│   ├─ Exchange 接口                                                       │
│   │    ├─ PaperExchange (in-process)                                    │
│   │    └─ BinanceTestnetExchange (REST → testnet.binance.vision)        │
│   └─ SQLite (quant.db)                                                  │
└──────────────────────────────────────────────────────────────────────────┘
```

**关键设计原则**：

- 所有跨边界依赖走接口（`Exchange` Protocol），便于 mock 测试 + 未来拆 worker 进程。
- 时间一律 UTC ISO 字符串（继承 `ai_lesson/CLAUDE.md` 的 UTC 约定）。
- 同一 (symbol, interval) 同分钟拉数据去重（业务层 30s 缓存 + DB UPSERT 兜底）。
- BotRunner.tick 写库走单一事务（orders + fills + positions 同提交）。

## 4. 项目布局

**根路径**：`/mnt/d/培训/ai_lesson/lesson6/project/`（在 ai_lesson 仓库内**原地演进**，先清掉课程残留再加新结构）。

**Pre-impl cleanup**（impl plan 第一步执行）：

```bash
# 在 lesson6/project/ 内
rm -rf openspec/ plans/ reports/         # 课程演示残留
rm -rf .claude/skills/backtest/          # 课程 skill demo
rm    .mcp.json                          # 课程 sqlite MCP 配置
rm -f btc_kline.py                       # lesson1 demo，本项目不用
rm -f prices.db cum_*.png                # 生成产物，会重建
rm -rf __pycache__/ .ruff_cache/ strategies/__pycache__/
# README.md 不删，但会被 impl 第一步重写
```

**最终目录结构**：

```
lesson6/project/
├── README.md            # 重写：从"课程项目快照"换成"quant-trader 项目说明"
├── pyproject.toml            # PEP 621，依赖：FastAPI, APScheduler, SQLModel, httpx,
│                             #          pandas, numpy, matplotlib, mplfinance,
│                             #          jinja2, python-multipart, uvicorn, pydantic-settings
│                             # dev:    pytest, pytest-cov, ruff
├── .env.example              # BINANCE_TESTNET_API_KEY / SECRET / BASE_URL
├── .gitignore                # __pycache__/ *.pyc quant.db *.png .pytest_cache/ .ruff_cache/ .env
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-05-17-quant-trader-v1-design.md  ← 本文档
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI 入口；启动 scheduler、注册 shutdown hook
│   ├── config.py             # pydantic-settings；读 .env
│   ├── db.py                 # SQLModel engine + session 工厂
│   ├── models.py             # SQLModel 实体：Bot, Order, Fill, Position, OHLC, PnLSnapshot, TickLog
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── registry.py       # name → callable + 默认 params
│   │   ├── dual_ma.py        # ⬅ lift from lesson6/project/strategies/dual_ma.py（0 改）
│   │   ├── rsi.py            # 新写
│   │   ├── macd.py           # 新写
│   │   └── bollinger.py      # 新写
│   ├── backtest.py           # ⬅ lift from lesson6/project/backtest.py（轻改：load_ohlc 加 interval 维度）
│   ├── kline_source.py       # ensure_latest_kline(symbol, interval) + 30s in-memory 缓存
│   ├── exchange/
│   │   ├── __init__.py
│   │   ├── base.py           # Exchange Protocol：place_market_order / get_balance / cancel_order
│   │   ├── paper.py          # PaperExchange：当前 bar close 价立即 fill；0.1% 手续费
│   │   └── binance_testnet.py# BinanceTestnetExchange：REST → testnet.binance.vision
│   ├── bot_runner.py         # tick(bot_id, db, exchanges)
│   ├── scheduler.py          # APScheduler 包装：add_bot_job / remove_bot_job / on_startup
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── backtest.py       # GET/POST /backtest
│   │   ├── bots.py           # GET /bots, POST /bots, GET/POST/DELETE /bots/{id}, POST /bots/{id}/start|stop
│   │   └── strategies.py     # GET /strategies
│   └── templates/
│       ├── base.html
│       ├── backtest.html
│       ├── bots_list.html
│       ├── bot_detail.html
│       ├── strategies.html
│       └── partials/
│           ├── bots_table.html
│           ├── bot_status.html
│           ├── fills_table.html
│           └── pnl_card.html
├── static/
│   └── style.css
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # sqlite tmpfile fixture + OHLC fixture loader
│   ├── fixtures/
│   │   └── btc_1d_90.csv     # 锚定数据：BTCUSDT 1d 最近 90 根
│   ├── test_strategies.py
│   ├── test_backtest.py
│   ├── test_paper_exchange.py
│   ├── test_bot_runner.py
│   ├── test_e2e_paper.py
│   ├── test_binance_testnet.py  # @pytest.mark.skipif(no env)
│   └── test_routes.py
├── scripts/
│   └── seed_db.py            # ⬅ lift from lesson6/project/seed_db.py（轻改：加 interval）
└── .github/
    └── workflows/
        └── verify.yml        # ruff + pytest --cov --cov-fail-under=80
```

## 5. 领域模型（SQLite schema）

7 张表，全部在 `quant.db`。SQLModel 实体定义在 `app/models.py`。

### 5.1 ohlc

存历史/最新 K 线，多 symbol × 多 timeframe。

| 字段 | 类型 | 说明 |
|---|---|---|
| symbol | TEXT | `BTCUSDT` / `ETHUSDT` / ... |
| interval | TEXT | `1m` / `5m` / `15m` / `1h` / `1d` |
| open_time | TEXT | UTC ISO，`2026-05-17T08:00:00Z` |
| open / high / low / close / volume | REAL | |

**PK**：`(symbol, interval, open_time)`。

**与 lesson6 的差异**：现有 `prices.db` PK 是 `(symbol, open_time)`，无 interval；v1 重新建库。

### 5.2 bots

每个 bot 实例的配置和当前状态。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT PK | autoincrement |
| name | TEXT UNIQUE | 用户给的名字 |
| strategy_name | TEXT | 必须在 strategy registry 里 |
| strategy_params | JSON | e.g., `{"short_window": 7, "long_window": 14}` |
| symbol | TEXT | |
| interval | TEXT | `1m` / `5m` / `15m` / `1h` |
| exchange | TEXT | `paper` / `binance_testnet` |
| status | TEXT | `stopped` / `running` / `errored` |
| initial_capital | REAL | paper 模式的起始现金；testnet 模式忽略此值 |
| created_at / updated_at | TEXT | UTC ISO |

### 5.3 orders

| id | bot_id | side | type | quantity | status | requested_at |
|---|---|---|---|---|---|---|
| INT PK | FK→bots.id | `buy`/`sell` | `market`（v1 唯一） | REAL | `pending`/`filled`/`rejected` | UTC ISO |

### 5.4 fills

| id | order_id | bot_id | price | quantity | fee | filled_at |
|---|---|---|---|---|---|---|

### 5.5 positions

每个 bot 一行，单一来源真相。

| 字段 | 类型 | 说明 |
|---|---|---|
| bot_id | INT PK | FK→bots.id |
| cash | REAL | 当前现金（quote currency） |
| base_qty | REAL | 当前持仓数量（base currency；v1 ≥ 0，长仓 only，参见 §6.1） |
| avg_entry_price | REAL? | 当前持仓的平均开仓价 |
| updated_at | TEXT | UTC ISO |

### 5.6 pnl_snapshots

每根 bar 收盘后一次。

| id | bot_id | snapshot_at | mark_price | equity | unrealized_pnl | realized_pnl |
|---|---|---|---|---|---|---|

**计算约定**：
- `equity = cash + base_qty * mark_price`
- `unrealized_pnl = (mark_price - avg_entry_price) * base_qty`，base_qty == 0 时为 0
- `realized_pnl = equity_at_snapshot - initial_capital - unrealized_pnl`
  （初始资金算 0 基线；每次平仓时 cash 已经包含了实现收益，所以反推即可）

### 5.7 tick_log

事件日志，UI bot 详情页消费。

| id | bot_id | tick_at | status | message |
|---|---|---|---|---|
| INT PK | FK | UTC ISO | `success`/`skipped`/`errored` | TEXT，最长 500 字 |

## 6. Strategy registry

`app/strategies/registry.py`：

```python
STRATEGY_REGISTRY: dict[str, StrategyEntry] = {
    "dual_ma":   StrategyEntry(fn=dual_ma,   defaults={"short_window": 7, "long_window": 14}),
    "rsi":       StrategyEntry(fn=rsi,       defaults={"period": 14, "oversold": 30, "overbought": 70}),
    "macd":      StrategyEntry(fn=macd,      defaults={"fast": 12, "slow": 26, "signal": 9}),
    "bollinger": StrategyEntry(fn=bollinger, defaults={"period": 20, "std": 2.0}),
}
```

所有策略统一签名：`def strategy(df: pd.DataFrame, **params) -> pd.Series`，返回值 ∈ {-1, 0, +1}（v1 主要用 0 / +1）。

**新增策略的语义**：

- `rsi`：RSI < oversold → +1（超卖做多）；RSI > overbought → 0（平仓）；其他保持。
- `macd`：MACD 线上穿 signal 线 → +1；下穿 → 0。
- `bollinger`：close 跌破下轨 → +1（均值回归）；穿越中线 → 0。

### 6.1 Position sizing 约定（v1 简化）

v1 不做风控参数，仓位规则固定：

- `signal = +1` 时**全仓做多**：用 `position.cash` 的 100%（扣手续费后）以 `mark_price` 买入 base。
- `signal = 0` 时**清仓**：把 `position.base_qty` 全部卖出回 cash。
- `signal = -1` 时**全仓做空**：v1 暂不实现（dual_ma/rsi/macd/bollinger 都不产生 -1）；BotRunner 遇到 -1 则降级为 `signal = 0` 处理 + tick_log 警告。

**`decide_order(latest_signal, position)`** 决策表：

| latest_signal | position.base_qty | 决策 |
|---|---|---|
| +1 | == 0 | buy `cash / mark_price * (1 - fee)` |
| +1 | > 0 | no-op（已持仓） |
| 0 | > 0 | sell `base_qty` |
| 0 | == 0 | no-op |
| -1 | * | 降级为 0，tick_log warn |

## 7. 核心组件

### 7.1 KlineSource (`app/kline_source.py`)

```python
async def ensure_latest_kline(symbol: str, interval: str, db: Session) -> None:
    """确保 ohlc 表里有该 (symbol, interval) 的最新一根 bar。
    30s in-memory TTL 防止同分钟多 bot 重复拉。"""
```

实现：
- 内存 dict cache：`{(symbol, interval): last_fetched_at}`
- 命中 30s 内则跳过
- 否则 GET `https://api.binance.com/api/v3/klines?symbol=...&interval=...&limit=2`
- UPSERT 到 ohlc

### 7.2 Exchange 接口 (`app/exchange/base.py`)

```python
class Exchange(Protocol):
    name: ClassVar[str]
    def place_market_order(self, bot_id: int, side: Side, qty: float, mark_price: float) -> Order: ...
    def get_balance(self, bot_id: int) -> Balance: ...
    def cancel_order(self, order_id: int) -> None: ...
```

`PaperExchange`：
- `place_market_order` 立即 fill at `mark_price`
- 手续费 0.1% 单边写入 fills.fee
- 现金不足时 order.status = `rejected`，position 不变

`BinanceTestnetExchange`：
- 用 `httpx.AsyncClient` 调 testnet.binance.vision
- HMAC-SHA256 签名
- 重试策略：429/5xx 指数退避 3 次

### 7.3 BotRunner.tick (`app/bot_runner.py`)

伪代码已在 §4 给出。关键约束：
- 整个 tick 在单个 DB transaction 里
- 任何异常 → 回滚 + 写 tick_log(status='errored') + bot.status='errored'
- 成功 → 写 tick_log(status='success')
- skip（无数据 / no signal change）→ 写 tick_log(status='skipped')

### 7.4 Scheduler (`app/scheduler.py`)

```python
def add_bot_job(scheduler: AsyncIOScheduler, bot: Bot) -> None:
    """根据 bot.interval 注册一个 CronTrigger。
    1m  → every minute at :05
    5m  → every 5 minutes at :05
    15m → every 15 minutes at :05
    1h  → every hour at HH:00:05
    """

def remove_bot_job(scheduler, bot_id: int) -> None: ...

def restore_running_bots_on_startup(scheduler, db: Session) -> None:
    """app 启动时扫 bots WHERE status='running'，重建所有 jobs。"""
```

APScheduler 用 `SQLAlchemyJobStore(url='sqlite:///quant.db')` 持久化 job 元数据。

### 7.5 Web routes

| Method | Path | 说明 | 模板 / partial |
|---|---|---|---|
| GET | `/` | 重定向到 `/bots` | — |
| GET | `/backtest` | 表单 | `backtest.html` |
| POST | `/backtest` | 跑回测，渲染结果 | `backtest.html` |
| GET | `/bots` | 列表（5s 自动轮询 partial） | `bots_list.html` |
| POST | `/bots` | 创建 bot（HTMX 表单 → 重定向到详情） | — |
| GET | `/bots/{id}` | 详情（持仓 / 最近 20 fills / P&L 曲线 / 最近 20 tick_log） | `bot_detail.html` |
| POST | `/bots/{id}/start` | flip status=running + add scheduler job | `partials/bot_status.html` |
| POST | `/bots/{id}/stop` | flip status=stopped + remove scheduler job | `partials/bot_status.html` |
| DELETE | `/bots/{id}` | 软删除（status='deleted'） | — |
| GET | `/strategies` | 策略库列表 + 默认参数 | `strategies.html` |

**HTMX 用法**：
- `<table hx-get="/bots/partial" hx-trigger="every 5s">`：bots 列表自动刷新
- `<button hx-post="/bots/{id}/start" hx-target="#bot-status-{id}">`：启动按钮局部刷新

## 8. 数据流（关键时序）

### 8.1 Bot 启动

```
User clicks [Start]
  → POST /bots/{id}/start
  → DB: bots.status = 'running'
  → Scheduler.add_bot_job(bot)
  → 初始化 positions 行（如不存在）
  → 返回 HTMX partial → UI 状态变绿
```

### 8.2 Tick lifecycle（1m bar 为例）

```
T = HH:MM:00         bar close (Binance)
T + 5s               APScheduler 触发 bot_runner.tick(bot_id)

tick():
  1. ensure_latest_kline(bot.symbol, bot.interval, db)
     ├─ cache hit (30s)? skip; else REST 拉 + UPSERT ohlc
  2. df = load_ohlc(bot.symbol, bot.interval, limit=200)
  3. signal = STRATEGY_REGISTRY[bot.strategy_name].fn(df, **bot.strategy_params)
  4. latest = int(signal.iloc[-1])          # +1 / 0 / -1
  5. pos = db.get(Position, bot_id)
  6. (side, qty) = decide_order(latest, pos)        # 见 §6.1 决策表
  7. if qty > 0:
       exchange = exchanges[bot.exchange]   # 'paper' or 'binance_testnet'
       order = exchange.place_market_order(bot_id, side, qty, mark_price=df['close'].iloc[-1])
       # 在 transaction 内写：orders, fills, positions
  8. write_pnl_snapshot(db, bot_id, mark=df['close'].iloc[-1])
  9. INSERT tick_log(status='success' | 'skipped')
```

### 8.3 Backtest lifecycle

```
GET /backtest                → 渲染表单（strategy 下拉 + symbol + interval + limit + params JSON 文本框）
POST /backtest (form data)   → 解析 → 调 backtest.run_backtest(strategy_fn, symbol, interval, limit, params)
                              → 渲染 backtest.html：summary + 4 指标卡 + 累计曲线 PNG（fragment image）
不入库。
```

## 9. 异常处理与边界

| 故障 | 处理 |
|---|---|
| Binance REST 429 / 5xx / timeout | 指数退避 3 次（1s/2s/4s）；仍失败 → 跳过本 tick，tick_log.status='skipped' |
| Binance testnet 下单失败 | order.status='rejected'，position 不动，UI banner 红字 |
| 策略函数抛异常 | try/except 兜底，bot.status='errored'，tick_log.message=traceback；UI 告警 |
| DB 写失败 | 整 tick 事务回滚；下一根 bar 自然重试 |
| App 重启 | `restore_running_bots_on_startup` 扫表重建 jobs |
| Scheduler 单 job 卡死 | APScheduler `max_instances=1` 防止上次没跑完下次又起 |
| Ctrl+C | `app.on_event("shutdown")` 调 scheduler.shutdown(wait=True) |

日志：
- `app/logs/app.log`（INFO+）
- `app/logs/error.log`（WARN+）
- DB 表 `tick_log` 喂前端"最近事件"区

## 10. 测试方案

| 层 | 文件 | 测什么 |
|---|---|---|
| Strategy 单测 | `tests/test_strategies.py` | 每个策略喂 fixture OHLC，断言 signal 关键位置 |
| Backtest 单测 | `tests/test_backtest.py` | run_backtest(buy_and_hold) 指标；shift(1) 防 lookahead |
| PaperExchange 单测 | `tests/test_paper_exchange.py` | place_market_order → fills + positions 正确；现金不足 reject |
| BotRunner.tick 单测 | `tests/test_bot_runner.py` | mock Exchange + 注入 OHLC，断言 tick 后 DB 产物 |
| 集成测 | `tests/test_e2e_paper.py` | 端到端：建 bot → 投喂 50 根 OHLC → 跑 50 次 tick → equity 一致性 |
| Binance testnet smoke | `tests/test_binance_testnet.py` | `@pytest.mark.skipif(no env)`：连通性、下单、查余额 |
| Web 路由 | `tests/test_routes.py` | FastAPI TestClient：GET/POST 路由 + HTMX partial 渲染 |

**目标**：`pytest --cov=app --cov-fail-under=80`。

**CI**：`.github/workflows/verify.yml`：
1. `pip install -e ".[dev]"`
2. `ruff check .`
3. `pytest --cov=app --cov-fail-under=80`

testnet smoke 在 CI 中自动跳过（无 secret）。

## 11. 现有 lesson6/project/ 文件的就地处理

由于本项目在 lesson6/project/ 原地演进，所有现有文件都要决定"保留 / 改写 / 移动 / 删除"。

| 现有文件/目录 | 处理 | 备注 |
|---|---|---|
| `strategies/dual_ma.py` | `mv → app/strategies/dual_ma.py` | 0 改动 |
| `strategies/__init__.py` | `mv → app/strategies/__init__.py` | 改：直导各 fn + 暴露 `STRATEGY_REGISTRY`（在 `registry.py`） |
| `backtest.py` | `mv → app/backtest.py` | 轻改：`load_ohlc` 增 `interval` 参数 + 字段；保留旧 `run_backtest` 签名 |
| `seed_db.py` | `mv → scripts/seed_db.py` | 轻改：多 interval 默认拉 1d + 1h |
| `README.md` | 重写 | 课程项目快照说明 → quant-trader 项目说明 |
| `btc_kline.py` | `rm` | lesson1 demo CLI；本项目用不到 |
| `openspec/` | `rm -rf` | lesson5 openspec 演示，课程残留 |
| `plans/` | `rm -rf` | lesson6 plan 演示，课程残留 |
| `reports/` | `rm -rf` | lesson6 report 演示，课程残留 |
| `.claude/skills/backtest/` | `rm -rf` | lesson4 skill demo |
| `.claude/settings.local.json` | 保留/视情况改 | 之后看 v1 是否需要本地权限设置 |
| `.mcp.json` | `rm` | 课程的 sqlite MCP 配置；本项目不依赖 MCP |
| `prices.db` | `rm` | 旧 schema 缺 interval，会重建 |
| `cum_*.png` | `rm` | backtest 演示产物 |
| `__pycache__/` `.ruff_cache/` 等 | `rm -rf` | 缓存 |
| `.gitignore` | 保留 + 追加 | 已有的基础上加 `.env` `quant.db` `app/logs/` |

## 12. 未来（v2+，非本 spec 范围）

下面这些 v1 明确不做，仅记录架构上需要为之留位的事项：

- **真钱主网**：`BinanceMainnetExchange` 复用 testnet 适配器、改 base_url；UI 增主网开关 + 二次确认；引入 risk_limits 表
- **风控**：止损 / 止盈 / 单笔最大金额 / 单日最大亏损熔断，作为 Strategy 包装层
- **WebSocket 行情**：替换 KlineSource 的 REST 轮询
- **独立 worker 进程**：scheduler 拆 `worker.py` 独立运行，web 只读 DB
- **多用户 / 多账户**：bots 加 user_id，引入登录态
- **回测历史 + 参数扫描**：回测结果入库 + 可重复运行 + 参数网格扫描 UI

## 13. Open questions（设计已锁定，仅备忘）

无（所有问题已在 brainstorming 阶段决议）。

---

**Approved by**: locey, 2026-05-17
**Next step**: superpowers:writing-plans → 产出 implementation plan
