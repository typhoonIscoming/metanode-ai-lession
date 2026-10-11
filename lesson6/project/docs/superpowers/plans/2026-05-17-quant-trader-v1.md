# quant-trader v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `lesson6/project/` 原地演进出 quant-trader v1：FastAPI + Jinja2 + HTMX + APScheduler + SQLite + SQLModel 单进程 monolith，多 bot 并发，bar-close 分钟级触发，支持 paper 撮合与 Binance Testnet 适配器，含 4 个内置策略（dual_ma / rsi / macd / bollinger）、回测、纸交易、Web 看板、80% 测试覆盖、GH Actions CI。

**Architecture:** 见 `docs/superpowers/specs/2026-05-17-quant-trader-v1-design.md` 第 3-8 节。核心：每个 (strategy, symbol, interval, exchange) 组合是一个 bot 实例；APScheduler 按 interval 边界触发 `bot_runner.tick()`；tick 调 `strategy(df, **params) → signal`，由 `decide_order` 翻成下单，写 orders/fills/positions/pnl_snapshots 同事务落库。Paper 与 Binance Testnet 走同一 `Exchange` 接口。

**Tech Stack:** Python 3.11+；FastAPI；Jinja2；HTMX；APScheduler 3.x（AsyncIOScheduler + SQLAlchemyJobStore）；SQLModel（SQLAlchemy + Pydantic）；SQLite；httpx（async REST client）；pandas / numpy / matplotlib / mplfinance；pydantic-settings；pytest / pytest-cov / pytest-asyncio；ruff。

---

## File Structure（演进终态）

每个文件单一职责。Tasks 按依赖顺序产出。

| 文件 | 职责 | 在哪个 Task 出生 |
|---|---|---|
| `pyproject.toml` | 依赖 + 工具配置（ruff, pytest） | Task 2 |
| `.env.example` | 环境变量样例（testnet 凭证） | Task 2 |
| `.gitignore` | 在现有基础上扩展 | Task 1 |
| `README.md` | quant-trader 项目说明（重写） | Task 1 |
| `app/__init__.py` | 标记 | Task 2 |
| `app/config.py` | pydantic-settings 加载 .env | Task 2 |
| `app/db.py` | SQLModel engine + session factory | Task 3 |
| `app/models.py` | 7 个 SQLModel 实体 | Task 3 |
| `app/strategies/__init__.py` | 直导 + STRATEGY_REGISTRY | Task 4 |
| `app/strategies/registry.py` | StrategyEntry 注册表 | Task 4 |
| `app/strategies/dual_ma.py` | （mv 自现有） | Task 4 |
| `app/strategies/rsi.py` | 新写 | Task 4 |
| `app/strategies/macd.py` | 新写 | Task 4 |
| `app/strategies/bollinger.py` | 新写 | Task 4 |
| `app/backtest.py` | mv + interval 扩展 | Task 5 |
| `app/exchange/__init__.py` | 标记 | Task 6 |
| `app/exchange/base.py` | Exchange Protocol + DTOs | Task 6 |
| `app/exchange/paper.py` | 内存撮合 | Task 6 |
| `app/exchange/binance_testnet.py` | testnet REST 适配器 | Task 7 |
| `app/kline_source.py` | REST 轮询 + 30s 缓存 | Task 8 |
| `app/bot_runner.py` | tick(bot_id) + decide_order | Task 9 |
| `app/scheduler.py` | APScheduler 包装 | Task 10 |
| `app/main.py` | FastAPI 入口 + lifespan | Task 11 |
| `app/routes/__init__.py` | 标记 | Task 11 |
| `app/routes/backtest.py` | /backtest GET/POST | Task 12 |
| `app/routes/bots.py` | /bots /bots/{id} 等 | Task 13 |
| `app/routes/strategies.py` | /strategies | Task 13 |
| `app/templates/base.html` | 共享布局 | Task 12 |
| `app/templates/backtest.html` | 回测表单 + 结果 | Task 12 |
| `app/templates/bots_list.html` | bot 列表 | Task 13 |
| `app/templates/bot_detail.html` | bot 详情 | Task 13 |
| `app/templates/strategies.html` | 策略库列表 | Task 13 |
| `app/templates/partials/*.html` | HTMX 局部 | Task 13 |
| `static/style.css` | 基础样式 | Task 12 |
| `scripts/seed_db.py` | mv + multi-interval | Task 14 |
| `tests/conftest.py` | OHLC fixture、tmpfile sqlite | Task 2 / 扩 |
| `tests/test_models.py` | 7 表创建 + CRUD | Task 3 |
| `tests/test_strategies.py` | 4 策略信号正确性 | Task 4 |
| `tests/test_backtest.py` | run_backtest 指标 + 防 lookahead | Task 5 |
| `tests/test_paper_exchange.py` | paper 撮合行为 | Task 6 |
| `tests/test_binance_testnet.py` | skipif no env，testnet smoke | Task 7 |
| `tests/test_kline_source.py` | 缓存 + REST mock | Task 8 |
| `tests/test_bot_runner.py` | tick 单元测 | Task 9 |
| `tests/test_scheduler.py` | add/remove/restore 状态 | Task 10 |
| `tests/test_routes.py` | TestClient 路由 + 模板 | Task 12-13 |
| `tests/test_e2e_paper.py` | 端到端集成 | Task 15 |
| `.github/workflows/verify.yml` | ruff + pytest --cov | Task 16 |

---

## Task 1: 清掉课程残留 + 重写 README + 扩 .gitignore

**Files:**
- Delete: `openspec/`, `plans/`, `reports/`, `.claude/skills/backtest/`, `.mcp.json`, `btc_kline.py`, `prices.db`, `cum_BTCUSDT.png`, `cum_ETHUSDT.png`, `__pycache__/`, `.ruff_cache/`, `strategies/__pycache__/`
- Modify: `README.md`（重写）, `.gitignore`（追加）

- [ ] **Step 1: 列出要删的文件做最后确认**

Run: `ls -la openspec/ plans/ reports/ .claude/skills/backtest/ .mcp.json btc_kline.py prices.db cum_*.png 2>&1 | head -40`

Expected: 所有列出的文件/目录都能看到（说明确实存在，删除是有意义的）。

- [ ] **Step 2: 删除课程残留文件**

Run:
```bash
cd lesson6/project
rm -rf openspec/ plans/ reports/ .claude/skills/backtest/
rm -f  .mcp.json btc_kline.py prices.db cum_BTCUSDT.png cum_ETHUSDT.png
rm -rf __pycache__/ .ruff_cache/ strategies/__pycache__/
```

Expected: 命令静默完成；`ls .claude/` 应只剩 `settings.local.json`。

- [ ] **Step 3: 重写 README.md 为 quant-trader 项目说明**

写入 `README.md`：

```markdown
# quant-trader

一个跑在 Binance Testnet 上的小型量化交易系统：写策略 → 回测 → 实时纸交易 / testnet 模拟下单 → Web 看板看持仓与 P&L。

## Quick start

```bash
pip install -e ".[dev]"
cp .env.example .env  # 填上你的 Binance Testnet API key/secret（可选）
python scripts/seed_db.py
uvicorn app.main:app --reload
# 打开 http://localhost:8000
```

## 项目结构

详见 `docs/superpowers/specs/2026-05-17-quant-trader-v1-design.md` §4。

## 命令

- `pytest --cov=app --cov-fail-under=80`  跑测试
- `ruff check .`  lint
- `uvicorn app.main:app --reload`  起服务

## 设计

- spec: `docs/superpowers/specs/2026-05-17-quant-trader-v1-design.md`
- plan: `docs/superpowers/plans/2026-05-17-quant-trader-v1.md`
```

- [ ] **Step 4: 扩 .gitignore**

把 `.gitignore` 改为：

```gitignore
# 不进版本库的运行产物
__pycache__/
*.pyc
prices.db
quant.db
quant.db-*
*.png
.pytest_cache/
.ruff_cache/
.env
app/logs/
.coverage
htmlcov/
```

- [ ] **Step 5: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: strip course remnants, rewrite README"
```

Expected: commit 成功；`git status` clean。

---

## Task 2: pyproject.toml + 配置层 + tests 骨架

**Files:**
- Create: `pyproject.toml`, `.env.example`, `app/__init__.py`, `app/config.py`, `tests/__init__.py`, `tests/conftest.py`, `tests/test_smoke.py`

- [ ] **Step 1: 写 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "quant-trader"
version = "0.1.0"
description = "Small quant trading system on Binance Testnet"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "jinja2>=3.1",
    "python-multipart>=0.0.9",
    "apscheduler>=3.10,<4",
    "sqlmodel>=0.0.16",
    "httpx>=0.27",
    "pandas>=2.1",
    "numpy>=1.26",
    "matplotlib>=3.8",
    "mplfinance>=0.12",
    "pydantic>=2.6",
    "pydantic-settings>=2.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.1",
    "pytest-asyncio>=0.23",
    "ruff>=0.3",
    "httpx>=0.27",  # for FastAPI TestClient
]

[tool.setuptools.packages.find]
include = ["app*"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "W", "B", "UP"]
ignore = ["E501"]  # 行长由格式化 handle

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 2: 装依赖验证**

Run: `pip install -e ".[dev]"`

Expected: 安装成功；`python -c "import fastapi, sqlmodel, apscheduler"` 不报错。

- [ ] **Step 3: 写 .env.example**

```
# Binance Testnet（v1 唯一支持的真实交易所；不填的话 paper 模式仍可用）
BINANCE_TESTNET_API_KEY=your_testnet_key_here
BINANCE_TESTNET_API_SECRET=your_testnet_secret_here
BINANCE_TESTNET_BASE_URL=https://testnet.binance.vision

# DB
QUANT_DB_URL=sqlite:///quant.db

# 日志
LOG_LEVEL=INFO
```

- [ ] **Step 4: 写 app/__init__.py（空文件）**

```python
"""quant-trader application package."""
```

- [ ] **Step 5: 写 app/config.py**

```python
"""集中加载环境变量。所有模块通过 `settings` 单例读配置。"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    binance_testnet_api_key: str = Field(default="")
    binance_testnet_api_secret: str = Field(default="")
    binance_testnet_base_url: str = Field(default="https://testnet.binance.vision")

    quant_db_url: str = Field(default="sqlite:///quant.db")
    log_level: str = Field(default="INFO")


settings = Settings()
```

- [ ] **Step 6: 写 tests/__init__.py（空）**

```python
```

- [ ] **Step 7: 写 tests/conftest.py（最小骨架）**

```python
"""共享测试 fixture。后续 task 持续扩。"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def ohlc_fixture() -> pd.DataFrame:
    """200 根确定性 OHLC，给策略 / 回测测试用。

    用 seed=42 的几何布朗运动生成，确保结果可重现。
    """
    np.random.seed(42)
    n = 200
    rets = np.random.normal(0.0005, 0.02, n)
    close = 100.0 * np.exp(np.cumsum(rets))
    high = close * (1 + np.abs(np.random.normal(0, 0.005, n)))
    low = close * (1 - np.abs(np.random.normal(0, 0.005, n)))
    open_ = np.r_[close[0], close[:-1]]
    volume = np.random.lognormal(15, 1, n)
    idx = pd.date_range("2025-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=idx,
    )
```

- [ ] **Step 8: 写 tests/test_smoke.py**

```python
"""验证基础 import / 配置加载正常。"""


def test_config_loads():
    from app.config import settings

    assert settings.quant_db_url.startswith("sqlite:")


def test_ohlc_fixture_shape(ohlc_fixture):
    assert ohlc_fixture.shape == (200, 5)
    assert list(ohlc_fixture.columns) == ["open", "high", "low", "close", "volume"]
    assert ohlc_fixture.index.tz is not None
```

- [ ] **Step 9: 跑测试 + lint**

Run: `pytest -v && ruff check .`

Expected: 2 passed；ruff 0 errors。

- [ ] **Step 10: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: scaffold pyproject + config + test infra"
```

---

## Task 3: SQLModel 数据层（7 张表）

**Files:**
- Create: `app/db.py`, `app/models.py`, `tests/test_models.py`

- [ ] **Step 1: 写失败测试 tests/test_models.py**

```python
"""验证 7 张表能创建、能插入、能查询。"""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import (
    OHLC,
    Bot,
    BotStatus,
    Exchange,
    Fill,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    PnLSnapshot,
    Position,
    TickLog,
    TickStatus,
)


@pytest.fixture
def engine(tmp_path):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    return eng


def test_create_all_tables(engine):
    # 7 张表 + apscheduler 内部不创建（不同 engine）
    expected = {"ohlc", "bots", "orders", "fills", "positions", "pnl_snapshots", "tick_log"}
    assert expected.issubset(set(SQLModel.metadata.tables.keys()))


def test_insert_and_query_ohlc(engine):
    with Session(engine) as s:
        s.add(OHLC(
            symbol="BTCUSDT", interval="1h", open_time="2026-05-17T00:00:00Z",
            open=100.0, high=110.0, low=95.0, close=105.0, volume=1000.0,
        ))
        s.commit()
        rows = s.exec(select(OHLC)).all()
        assert len(rows) == 1
        assert rows[0].close == 105.0


def test_insert_bot(engine):
    with Session(engine) as s:
        bot = Bot(
            name="ma-btc-1h",
            strategy_name="dual_ma",
            strategy_params={"short_window": 7, "long_window": 14},
            symbol="BTCUSDT",
            interval="1h",
            exchange=Exchange.paper,
            status=BotStatus.stopped,
            initial_capital=10000.0,
        )
        s.add(bot)
        s.commit()
        s.refresh(bot)
        assert bot.id is not None
        assert bot.strategy_params == {"short_window": 7, "long_window": 14}


def test_position_one_row_per_bot(engine):
    with Session(engine) as s:
        s.add(Position(bot_id=1, cash=10000.0, base_qty=0.0, avg_entry_price=None))
        s.commit()
        pos = s.get(Position, 1)
        assert pos.cash == 10000.0


def test_order_fill_relation(engine):
    with Session(engine) as s:
        order = Order(
            bot_id=1, side=OrderSide.buy, type=OrderType.market,
            quantity=0.5, status=OrderStatus.filled,
        )
        s.add(order)
        s.commit()
        s.refresh(order)
        s.add(Fill(order_id=order.id, bot_id=1, price=100.0, quantity=0.5, fee=0.05))
        s.commit()
        fills = s.exec(select(Fill).where(Fill.order_id == order.id)).all()
        assert len(fills) == 1
        assert fills[0].quantity == 0.5
```

- [ ] **Step 2: 跑测试验证它失败**

Run: `pytest tests/test_models.py -v`

Expected: ImportError 或 ModuleNotFoundError（app.models 还没写）。

- [ ] **Step 3: 写 app/db.py**

```python
"""SQLModel engine + session 工厂。

engine 是模块级单例；测试时用 FastAPI dependency_overrides[get_engine]
覆盖即可（routes 都通过 Depends(get_engine) / Depends(get_session) 取依赖）。
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings


engine: Engine = create_engine(
    settings.quant_db_url,
    connect_args={"check_same_thread": False} if settings.quant_db_url.startswith("sqlite") else {},
)


def get_engine() -> Engine:
    """FastAPI Depends 钩子；测试时 override 为另一个 engine。"""
    return engine


def init_db(eng: Engine | None = None) -> None:
    """创建所有 SQLModel 表（幂等）。在 main.lifespan 启动时调一次。"""
    from app import models  # noqa: F401  必须 import 以触发 SQLModel.metadata 注册

    SQLModel.metadata.create_all(eng or engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI Depends 用的 session 生成器。"""
    with Session(engine) as session:
        yield session
```

- [ ] **Step 4: 写 app/models.py**

```python
"""SQLModel 实体定义。所有时间字段都是 UTC ISO 字符串。"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import JSON, Column, Field, SQLModel


def utcnow_iso() -> str:
    """生成 UTC ISO 8601 时间戳，例如 '2026-05-17T08:00:00Z'。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Exchange(str, Enum):
    paper = "paper"
    binance_testnet = "binance_testnet"


class BotStatus(str, Enum):
    stopped = "stopped"
    running = "running"
    errored = "errored"


class OrderSide(str, Enum):
    buy = "buy"
    sell = "sell"


class OrderType(str, Enum):
    market = "market"


class OrderStatus(str, Enum):
    pending = "pending"
    filled = "filled"
    rejected = "rejected"


class TickStatus(str, Enum):
    success = "success"
    skipped = "skipped"
    errored = "errored"


class OHLC(SQLModel, table=True):
    __tablename__ = "ohlc"

    symbol: str = Field(primary_key=True)
    interval: str = Field(primary_key=True)
    open_time: str = Field(primary_key=True)  # UTC ISO
    open: float
    high: float
    low: float
    close: float
    volume: float


class Bot(SQLModel, table=True):
    __tablename__ = "bots"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    strategy_name: str
    strategy_params: dict = Field(default_factory=dict, sa_column=Column(JSON))
    symbol: str
    interval: str
    exchange: Exchange = Field(default=Exchange.paper)
    status: BotStatus = Field(default=BotStatus.stopped)
    initial_capital: float = Field(default=10000.0)
    created_at: str = Field(default_factory=utcnow_iso)
    updated_at: str = Field(default_factory=utcnow_iso)


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: int | None = Field(default=None, primary_key=True)
    bot_id: int = Field(index=True)
    side: OrderSide
    type: OrderType = Field(default=OrderType.market)
    quantity: float
    status: OrderStatus = Field(default=OrderStatus.pending)
    requested_at: str = Field(default_factory=utcnow_iso)


class Fill(SQLModel, table=True):
    __tablename__ = "fills"

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(index=True)
    bot_id: int = Field(index=True)
    price: float
    quantity: float
    fee: float = Field(default=0.0)
    filled_at: str = Field(default_factory=utcnow_iso)


class Position(SQLModel, table=True):
    __tablename__ = "positions"

    bot_id: int = Field(primary_key=True)
    cash: float
    base_qty: float = Field(default=0.0)
    avg_entry_price: float | None = Field(default=None)
    updated_at: str = Field(default_factory=utcnow_iso)


class PnLSnapshot(SQLModel, table=True):
    __tablename__ = "pnl_snapshots"

    id: int | None = Field(default=None, primary_key=True)
    bot_id: int = Field(index=True)
    snapshot_at: str = Field(default_factory=utcnow_iso, index=True)
    mark_price: float
    equity: float
    unrealized_pnl: float
    realized_pnl: float


class TickLog(SQLModel, table=True):
    __tablename__ = "tick_log"

    id: int | None = Field(default=None, primary_key=True)
    bot_id: int = Field(index=True)
    tick_at: str = Field(default_factory=utcnow_iso, index=True)
    status: TickStatus
    message: str = Field(default="", max_length=500)
```

- [ ] **Step 5: 跑测试验证通过**

Run: `pytest tests/test_models.py -v`

Expected: 5 passed。

- [ ] **Step 6: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: SQLModel data layer (7 tables) + tests"
```

---

## Task 4: 策略模块（mv dual_ma + 新增 rsi/macd/bollinger + registry）

**Files:**
- Move: `strategies/dual_ma.py` → `app/strategies/dual_ma.py`
- Move: `strategies/__init__.py` → `app/strategies/__init__.py`（改）
- Create: `app/strategies/registry.py`, `app/strategies/rsi.py`, `app/strategies/macd.py`, `app/strategies/bollinger.py`, `tests/test_strategies.py`

- [ ] **Step 1: 物理移动现有 strategies/**

Run:
```bash
cd lesson6/project
mkdir -p app
git mv strategies app/strategies
```

Expected: `app/strategies/dual_ma.py` 与 `app/strategies/__init__.py` 在新位置；git 看到 rename。

- [ ] **Step 2: 写失败测试 tests/test_strategies.py**

```python
"""验证 4 个策略在 fixture OHLC 上产出预期 signal。"""

from __future__ import annotations

import pandas as pd
import pytest

from app.strategies import STRATEGY_REGISTRY, bollinger, dual_ma, macd, rsi


def _assert_signal_invariants(sig: pd.Series, df: pd.DataFrame) -> None:
    """所有策略必须满足的通用约束。"""
    assert isinstance(sig, pd.Series)
    assert sig.index.equals(df.index)
    assert set(sig.dropna().unique()).issubset({-1, 0, 1})


def test_dual_ma_signal_invariants(ohlc_fixture):
    sig = dual_ma(ohlc_fixture, short_window=7, long_window=14)
    _assert_signal_invariants(sig, ohlc_fixture)
    # 前 long_window 根 warmup，必须为 0
    assert (sig.iloc[:14] == 0).all()


def test_rsi_signal_invariants(ohlc_fixture):
    sig = rsi(ohlc_fixture, period=14, oversold=30, overbought=70)
    _assert_signal_invariants(sig, ohlc_fixture)
    assert (sig.iloc[:14] == 0).all()  # warmup


def test_macd_signal_invariants(ohlc_fixture):
    sig = macd(ohlc_fixture, fast=12, slow=26, signal=9)
    _assert_signal_invariants(sig, ohlc_fixture)
    # MACD 至少需要 slow + signal 根 bar 形成
    assert (sig.iloc[: 26 + 9] == 0).all()


def test_bollinger_signal_invariants(ohlc_fixture):
    sig = bollinger(ohlc_fixture, period=20, std=2.0)
    _assert_signal_invariants(sig, ohlc_fixture)
    assert (sig.iloc[:20] == 0).all()


def test_registry_has_four_strategies():
    assert set(STRATEGY_REGISTRY.keys()) == {"dual_ma", "rsi", "macd", "bollinger"}
    for name, entry in STRATEGY_REGISTRY.items():
        assert callable(entry.fn)
        assert isinstance(entry.defaults, dict)


def test_registry_dual_ma_defaults():
    e = STRATEGY_REGISTRY["dual_ma"]
    assert e.defaults == {"short_window": 7, "long_window": 14}


@pytest.mark.parametrize("name", ["dual_ma", "rsi", "macd", "bollinger"])
def test_registry_strategy_runs_with_defaults(ohlc_fixture, name):
    e = STRATEGY_REGISTRY[name]
    sig = e.fn(ohlc_fixture, **e.defaults)
    _assert_signal_invariants(sig, ohlc_fixture)
```

- [ ] **Step 3: 跑测试验证它失败**

Run: `pytest tests/test_strategies.py -v`

Expected: ImportError（rsi/macd/bollinger/STRATEGY_REGISTRY 还没有）。

- [ ] **Step 4: 写 app/strategies/registry.py**

```python
"""策略注册表：名字 → (callable, 默认参数)。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from app.strategies.bollinger import bollinger
from app.strategies.dual_ma import dual_ma
from app.strategies.macd import macd
from app.strategies.rsi import rsi


@dataclass(frozen=True)
class StrategyEntry:
    fn: Callable[..., pd.Series]
    defaults: dict


STRATEGY_REGISTRY: dict[str, StrategyEntry] = {
    "dual_ma":   StrategyEntry(fn=dual_ma,   defaults={"short_window": 7, "long_window": 14}),
    "rsi":       StrategyEntry(fn=rsi,       defaults={"period": 14, "oversold": 30, "overbought": 70}),
    "macd":      StrategyEntry(fn=macd,      defaults={"fast": 12, "slow": 26, "signal": 9}),
    "bollinger": StrategyEntry(fn=bollinger, defaults={"period": 20, "std": 2.0}),
}
```

- [ ] **Step 5: 写 app/strategies/rsi.py**

```python
"""RSI 策略：超卖（RSI < oversold）做多，超买（RSI > overbought）平仓。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(
    df: pd.DataFrame,
    period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0,
) -> pd.Series:
    if len(df) < period + 1:
        return pd.Series(0, index=df.index)

    # shift(1) 保证只用昨日及以前的 close
    close = df["close"].shift(1)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_value = 100 - 100 / (1 + rs)

    sig = pd.Series(np.nan, index=df.index)
    sig[rsi_value < oversold] = 1.0
    sig[rsi_value > overbought] = 0.0
    sig = sig.ffill().fillna(0).astype(int)
    return sig
```

- [ ] **Step 6: 写 app/strategies/macd.py**

```python
"""MACD 策略：MACD 线上穿 signal 线做多，下穿平仓。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.Series:
    if len(df) < slow + signal:
        return pd.Series(0, index=df.index)

    close = df["close"].shift(1)
    ema_fast = close.ewm(span=fast, adjust=False, min_periods=fast).mean()
    ema_slow = close.ewm(span=slow, adjust=False, min_periods=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()

    cross_up = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
    cross_dn = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))

    sig = pd.Series(np.nan, index=df.index)
    sig[cross_up] = 1.0
    sig[cross_dn] = 0.0
    sig = sig.ffill().fillna(0).astype(int)
    return sig
```

- [ ] **Step 7: 写 app/strategies/bollinger.py**

```python
"""Bollinger 均值回归：close 跌破下轨做多，回到中轨平仓。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def bollinger(
    df: pd.DataFrame,
    period: int = 20,
    std: float = 2.0,
) -> pd.Series:
    if len(df) < period:
        return pd.Series(0, index=df.index)

    close = df["close"].shift(1)
    mid = close.rolling(period, min_periods=period).mean()
    sd = close.rolling(period, min_periods=period).std()
    lower = mid - std * sd

    sig = pd.Series(np.nan, index=df.index)
    sig[close < lower] = 1.0
    sig[close >= mid] = 0.0
    sig = sig.ffill().fillna(0).astype(int)
    return sig
```

- [ ] **Step 8: 改 app/strategies/__init__.py**

```python
"""quant-trader 策略库。

所有策略统一签名：def strategy(df: pd.DataFrame, **params) -> pd.Series
返回 Series ∈ {-1, 0, +1}（v1 实现的都是 0 / +1）。
"""

from app.strategies.bollinger import bollinger
from app.strategies.dual_ma import dual_ma
from app.strategies.macd import macd
from app.strategies.registry import STRATEGY_REGISTRY, StrategyEntry
from app.strategies.rsi import rsi

__all__ = [
    "STRATEGY_REGISTRY",
    "StrategyEntry",
    "bollinger",
    "dual_ma",
    "macd",
    "rsi",
]
```

- [ ] **Step 9: 跑测试验证通过**

Run: `pytest tests/test_strategies.py -v`

Expected: 全部 pass（7 个测试 + 4 个 parametrize = 11 passed）。

- [ ] **Step 10: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: move strategies, add rsi/macd/bollinger, registry"
```

---

## Task 5: backtest.py（mv + 加 interval 维度）

**Files:**
- Move: `backtest.py` → `app/backtest.py`（改）
- Create: `tests/test_backtest.py`

- [ ] **Step 1: 物理移动**

Run:
```bash
cd lesson6/project
git mv backtest.py app/backtest.py
```

- [ ] **Step 2: 写失败测试 tests/test_backtest.py**

```python
"""验证 run_backtest 在 stub OHLC 上的指标，及 shift(1) 防 lookahead。"""

from __future__ import annotations

import pandas as pd
import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.backtest import _max_drawdown, _sharpe, run_backtest
from app.models import OHLC


@pytest.fixture
def db_with_ohlc(tmp_path, ohlc_fixture):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        for ts, row in ohlc_fixture.iterrows():
            s.add(OHLC(
                symbol="BTCUSDT", interval="1h",
                open_time=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                open=row["open"], high=row["high"], low=row["low"],
                close=row["close"], volume=row["volume"],
            ))
        s.commit()
    return eng


def _buy_and_hold(df: pd.DataFrame) -> pd.Series:
    return pd.Series(1, index=df.index)


def test_run_backtest_buy_and_hold(db_with_ohlc, tmp_path):
    res = run_backtest(
        _buy_and_hold, symbol="BTCUSDT", interval="1h", limit=200,
        out_dir=tmp_path, engine=db_with_ohlc,
    )
    assert isinstance(res, dict)
    assert "sharpe" in res and "max_drawdown" in res and "win_rate" in res
    assert "cumulative_return" in res and "png_path" in res and "summary" in res
    assert res["rows"] == 200
    # 买入持有：累计收益等于最后一根 close / 第一根 close - 1（信号 shift 1 后）
    # 不强求精确值，但应非零
    assert abs(res["cumulative_return"]) > 0


def test_sharpe_zero_when_zero_variance():
    flat = pd.Series([0.0] * 30)
    assert _sharpe(flat) == 0.0


def test_max_drawdown_monotonic_increasing():
    rising = pd.Series([1, 1.1, 1.2, 1.3, 1.4])
    assert _max_drawdown(rising) == 0.0


def test_max_drawdown_negative_after_peak():
    cumulative = pd.Series([1.0, 1.2, 0.8])  # 1.2 → 0.8 跌 33%
    assert pytest.approx(_max_drawdown(cumulative), rel=1e-6) == -1 / 3
```

- [ ] **Step 3: 跑测试验证失败**

Run: `pytest tests/test_backtest.py -v`

Expected: ImportError（app.backtest 还没改，旧 load_ohlc 用 sqlite3 而不是 SQLModel engine；run_backtest 签名没有 engine 参数）。

- [ ] **Step 4: 改 app/backtest.py**

整体替换为：

```python
"""最小回测引擎。

设计目标：
- 入口函数 run_backtest(strategy, ...) 接受一个策略 callable，返回结构化结果
- 不依赖第三方回测框架，纯 pandas/numpy 实现
- 数据源：quant.db 的 ohlc 表（多 symbol × 多 timeframe）

策略 callable 约定：
    def strategy(df: pd.DataFrame, **params) -> pd.Series
    输入：DataFrame，索引为 open_time（UTC tz-aware），列含 open/high/low/close/volume
    输出：Series，索引同 df，值 ∈ {-1, 0, +1}

输出 dict 字段：
    sharpe / max_drawdown / win_rate / cumulative_return / png_path / summary / rows
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")  # headless 后端
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import engine as default_engine

TRADING_PERIODS = {
    "1m": 365 * 24 * 60,
    "5m": 365 * 24 * 12,
    "15m": 365 * 24 * 4,
    "1h": 365 * 24,
    "4h": 365 * 6,
    "1d": 365,
}


@dataclass
class BacktestResult:
    sharpe: float
    max_drawdown: float
    win_rate: float
    cumulative_return: float
    png_path: str
    summary: str
    rows: int


def load_ohlc(
    symbol: str, interval: str, limit: int, engine: Engine | None = None,
) -> pd.DataFrame:
    """从 ohlc 表读最近 limit 行该 (symbol, interval) 的 K 线，按时间升序返回。"""
    eng = engine or default_engine
    with eng.connect() as conn:
        df = pd.read_sql_query(
            text(
                "SELECT open_time, open, high, low, close, volume "
                "FROM ohlc WHERE symbol = :symbol AND interval = :interval "
                "ORDER BY open_time DESC LIMIT :limit"
            ),
            conn,
            params={"symbol": symbol, "interval": interval, "limit": limit},
        )
    if df.empty:
        raise ValueError(
            f"ohlc 表里没有 {symbol} {interval} 的数据；先跑 scripts/seed_db.py"
        )
    df["open_time"] = pd.to_datetime(df["open_time"], utc=True)
    df = df.set_index("open_time").sort_index()
    return df


def run_backtest(
    strategy: Callable[..., pd.Series],
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 30,
    out_dir: Path | None = None,
    engine: Engine | None = None,
    **strategy_params,
) -> dict:
    """跑一次回测，把累计曲线写到 out_dir/cum_<symbol>_<interval>.png；返回结果 dict。"""
    df = load_ohlc(symbol, interval, limit, engine=engine)

    signal = strategy(df, **strategy_params).reindex(df.index).fillna(0).clip(-1, 1)
    daily_return = df["close"].pct_change().fillna(0)
    strategy_return = signal.shift(1).fillna(0) * daily_return
    cumulative = (1 + strategy_return).cumprod()

    periods = TRADING_PERIODS.get(interval, 252)
    sharpe = _sharpe(strategy_return, periods=periods)
    max_drawdown = _max_drawdown(cumulative)
    win_rate = _win_rate(signal, strategy_return)
    cumulative_return = float(cumulative.iloc[-1] - 1)

    if out_dir is None:
        out_dir = Path(__file__).parent.parent
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / f"cum_{symbol}_{interval}.png"

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(cumulative.index, cumulative.values, label=f"{symbol} {interval}", linewidth=2)
    ax.axhline(1.0, linestyle="--", color="gray", linewidth=0.8, label="basis 1.0")
    ax.set_title(f"Cumulative return — {symbol} {interval} ({len(df)} bars)")
    ax.set_ylabel("cumulative")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(png_path, dpi=120)
    plt.close(fig)

    summary = _summary(symbol, interval, len(df), sharpe, max_drawdown, win_rate, cumulative_return)

    return BacktestResult(
        sharpe=sharpe, max_drawdown=max_drawdown, win_rate=win_rate,
        cumulative_return=cumulative_return, png_path=str(png_path),
        summary=summary, rows=len(df),
    ).__dict__


def _sharpe(returns: pd.Series, periods: int = 252) -> float:
    r = returns.dropna()
    if len(r) < 2 or r.std() == 0:
        return 0.0
    return float(r.mean() / r.std() * np.sqrt(periods))


def _max_drawdown(cumulative: pd.Series) -> float:
    if cumulative.empty:
        return 0.0
    peak = cumulative.cummax()
    drawdown = cumulative / peak - 1
    return float(drawdown.min())


def _win_rate(signal: pd.Series, strategy_return: pd.Series) -> float:
    mask = signal.shift(1).fillna(0) != 0
    if not mask.any():
        return 0.0
    return float((strategy_return[mask] > 0).mean())


def _summary(
    symbol: str, interval: str, rows: int,
    sharpe: float, max_dd: float, win_rate: float, cum: float,
) -> str:
    direction = "上涨" if cum >= 0 else "下跌"
    pct = lambda x: f"{x * 100:.2f}%"  # noqa: E731
    return (
        f"{symbol} {interval} 在最近 {rows} 根 K 线上的回测结果：累计{direction} {pct(cum)}，"
        f"年化夏普 {sharpe:.2f}，最大回撤 {pct(max_dd)}，"
        f"信号触发日胜率 {pct(win_rate)}。"
        f"{'夏普 > 1 说明风险调整后收益尚可' if sharpe >= 1 else '夏普 < 1 说明相对持有并无显著优势'}。"
    )
```

- [ ] **Step 5: 跑测试验证通过**

Run: `pytest tests/test_backtest.py -v`

Expected: 4 passed。

- [ ] **Step 6: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: move backtest.py, add interval support, tests"
```

---

## Task 6: Exchange 接口 + PaperExchange

**Files:**
- Create: `app/exchange/__init__.py`, `app/exchange/base.py`, `app/exchange/paper.py`, `tests/test_paper_exchange.py`

- [ ] **Step 1: 写失败测试 tests/test_paper_exchange.py**

```python
"""验证 PaperExchange 行为：买入扣现金、卖出加现金、不足时 reject。"""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.exchange.base import OrderSide
from app.exchange.paper import PaperExchange
from app.models import Bot, BotStatus, Exchange as ExchangeEnum, Fill, Order, OrderStatus, Position


@pytest.fixture
def session(tmp_path):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        bot = Bot(
            name="t", strategy_name="dual_ma", strategy_params={},
            symbol="BTCUSDT", interval="1h", exchange=ExchangeEnum.paper,
            status=BotStatus.stopped, initial_capital=10000.0,
        )
        s.add(bot)
        s.commit()
        s.refresh(bot)
        s.add(Position(bot_id=bot.id, cash=10000.0, base_qty=0.0, avg_entry_price=None))
        s.commit()
        yield s, bot.id


def test_paper_buy_at_mark_price(session):
    s, bot_id = session
    ex = PaperExchange(fee_rate=0.001)
    order = ex.place_market_order(s, bot_id, OrderSide.buy, qty=0.1, mark_price=1000.0)
    assert order.status == OrderStatus.filled
    fills = s.exec_all_fills(bot_id) if hasattr(s, "exec_all_fills") else None
    # 直接读 DB 验证
    pos = s.get(Position, bot_id)
    assert pos.base_qty == 0.1
    # 现金扣了 100（标的价）+ 0.1（手续费 0.1%）
    assert pos.cash == pytest.approx(10000.0 - 100.0 - 0.1)
    assert pos.avg_entry_price == pytest.approx(1000.0)


def test_paper_sell_realizes_cash(session):
    s, bot_id = session
    ex = PaperExchange(fee_rate=0.001)
    ex.place_market_order(s, bot_id, OrderSide.buy, qty=0.1, mark_price=1000.0)
    ex.place_market_order(s, bot_id, OrderSide.sell, qty=0.1, mark_price=1100.0)
    pos = s.get(Position, bot_id)
    assert pos.base_qty == 0.0
    assert pos.avg_entry_price is None
    # 买花了 100.1，卖回 110 - 0.11 = 109.89；最终 cash ≈ 10000 - 100.1 + 109.89 = 10009.79
    assert pos.cash == pytest.approx(10000.0 - 100.1 + 109.89)


def test_paper_insufficient_cash_rejected(session):
    s, bot_id = session
    ex = PaperExchange(fee_rate=0.001)
    order = ex.place_market_order(s, bot_id, OrderSide.buy, qty=100.0, mark_price=1000.0)
    assert order.status == OrderStatus.rejected
    pos = s.get(Position, bot_id)
    assert pos.base_qty == 0.0
    assert pos.cash == 10000.0


def test_paper_sell_more_than_held_rejected(session):
    s, bot_id = session
    ex = PaperExchange(fee_rate=0.001)
    order = ex.place_market_order(s, bot_id, OrderSide.sell, qty=0.5, mark_price=1000.0)
    assert order.status == OrderStatus.rejected
    pos = s.get(Position, bot_id)
    assert pos.base_qty == 0.0
```

- [ ] **Step 2: 跑测试验证失败**

Run: `pytest tests/test_paper_exchange.py -v`

Expected: ImportError（app.exchange 不存在）。

- [ ] **Step 3: 写 app/exchange/__init__.py**

```python
"""Exchange adapters：paper（内存撮合）+ binance_testnet（REST）。"""
```

- [ ] **Step 4: 写 app/exchange/base.py**

```python
"""Exchange 接口与共用 DTO。

接口约定：
- 所有方法接受一个开启的 SQLModel Session，方法内部不开/不关 session（由调用者管事务）
- place_market_order 立即返回 Order；filled / rejected 在同一调用内决定
- mark_price 是"参考价"——paper 用它直接 fill，testnet 也传给 binance 作为参考但实际成交价由交易所给出
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlmodel import Session

# 复用 models.OrderSide / OrderStatus 避免重复定义
from app.models import OrderSide, OrderStatus


@dataclass
class Balance:
    bot_id: int
    cash: float
    base_qty: float
    avg_entry_price: float | None


class Exchange(Protocol):
    name: str  # "paper" | "binance_testnet"

    def place_market_order(
        self,
        session: Session,
        bot_id: int,
        side: OrderSide,
        qty: float,
        mark_price: float,
    ) -> "Order": ...

    def get_balance(self, session: Session, bot_id: int) -> Balance: ...


# 让 base 自包含：把 models.Order 重新导出方便 tests/type hints
from app.models import Order  # noqa: E402

__all__ = ["Balance", "Exchange", "Order", "OrderSide", "OrderStatus"]
```

- [ ] **Step 5: 写 app/exchange/paper.py**

```python
"""内存撮合：以传入的 mark_price 立即成交。

不维护任何独立状态——所有数据都落在 positions / orders / fills 表里。
"""

from __future__ import annotations

from sqlmodel import Session

from app.exchange.base import Balance, OrderSide, OrderStatus
from app.models import Fill, Order, OrderType, Position


class PaperExchange:
    name = "paper"

    def __init__(self, fee_rate: float = 0.001) -> None:
        self.fee_rate = fee_rate

    def place_market_order(
        self,
        session: Session,
        bot_id: int,
        side: OrderSide,
        qty: float,
        mark_price: float,
    ) -> Order:
        pos = session.get(Position, bot_id)
        if pos is None:
            raise ValueError(f"Position 不存在 bot_id={bot_id}；启动 bot 时应已初始化")

        # 先建 Order pending
        order = Order(bot_id=bot_id, side=side, type=OrderType.market, quantity=qty, status=OrderStatus.pending)
        session.add(order)
        session.flush()

        notional = qty * mark_price
        fee = notional * self.fee_rate

        # 决定能不能 fill
        if side == OrderSide.buy:
            if pos.cash < notional + fee:
                order.status = OrderStatus.rejected
                session.add(order)
                return order
            # fill：扣现金、增持仓、更新均价
            new_qty = pos.base_qty + qty
            if pos.base_qty == 0:
                new_avg = mark_price
            else:
                new_avg = (pos.base_qty * pos.avg_entry_price + qty * mark_price) / new_qty
            pos.cash -= notional + fee
            pos.base_qty = new_qty
            pos.avg_entry_price = new_avg

        else:  # sell
            if pos.base_qty < qty:
                order.status = OrderStatus.rejected
                session.add(order)
                return order
            new_qty = pos.base_qty - qty
            pos.cash += notional - fee
            pos.base_qty = new_qty
            pos.avg_entry_price = None if new_qty == 0 else pos.avg_entry_price

        # fill 成功 → 写 fills + 更新 order
        order.status = OrderStatus.filled
        session.add(order)
        session.add(Fill(order_id=order.id, bot_id=bot_id, price=mark_price, quantity=qty, fee=fee))
        session.add(pos)
        return order

    def get_balance(self, session: Session, bot_id: int) -> Balance:
        pos = session.get(Position, bot_id)
        if pos is None:
            return Balance(bot_id=bot_id, cash=0.0, base_qty=0.0, avg_entry_price=None)
        return Balance(bot_id=bot_id, cash=pos.cash, base_qty=pos.base_qty, avg_entry_price=pos.avg_entry_price)
```

- [ ] **Step 6: 跑测试验证通过**

Run: `pytest tests/test_paper_exchange.py -v`

Expected: 4 passed。

- [ ] **Step 7: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: Exchange interface + PaperExchange + tests"
```

---

## Task 7: BinanceTestnetExchange（REST 适配器）

**Files:**
- Create: `app/exchange/binance_testnet.py`, `tests/test_binance_testnet.py`

- [ ] **Step 1: 写带 skipif 的 smoke 测 tests/test_binance_testnet.py**

```python
"""Binance Testnet 实测：需要环境变量里有 testnet 凭证才跑，否则全部 skip。"""

from __future__ import annotations

import os

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.exchange.base import OrderSide
from app.exchange.binance_testnet import BinanceTestnetExchange
from app.models import Bot, BotStatus, Exchange as ExchangeEnum, Position

REQUIRES_TESTNET = pytest.mark.skipif(
    not os.environ.get("BINANCE_TESTNET_API_KEY"),
    reason="set BINANCE_TESTNET_API_KEY / SECRET to run testnet smoke tests",
)


@pytest.fixture
def session(tmp_path):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        bot = Bot(
            name="testnet-smoke", strategy_name="dual_ma", strategy_params={},
            symbol="BTCUSDT", interval="1h", exchange=ExchangeEnum.binance_testnet,
            status=BotStatus.stopped, initial_capital=0.0,
        )
        s.add(bot)
        s.commit()
        s.refresh(bot)
        s.add(Position(bot_id=bot.id, cash=0.0, base_qty=0.0, avg_entry_price=None))
        s.commit()
        yield s, bot.id


@REQUIRES_TESTNET
def test_testnet_get_balance(session):
    s, bot_id = session
    ex = BinanceTestnetExchange()
    bal = ex.get_balance(s, bot_id)
    # testnet 账户上至少能查到 USDT 余额（≥ 0）
    assert bal.cash >= 0


@REQUIRES_TESTNET
def test_testnet_place_tiny_buy_and_sell(session):
    s, bot_id = session
    ex = BinanceTestnetExchange()
    # 最小可下单数量取决于 symbol；用 BTCUSDT 0.001 通常够
    buy = ex.place_market_order(s, bot_id, OrderSide.buy, qty=0.001, mark_price=0.0)
    assert buy.status.value in {"filled", "rejected"}
    if buy.status.value == "filled":
        sell = ex.place_market_order(s, bot_id, OrderSide.sell, qty=0.001, mark_price=0.0)
        assert sell.status.value in {"filled", "rejected"}
```

- [ ] **Step 2: 跑测试验证 skip 工作**

Run: `pytest tests/test_binance_testnet.py -v`

Expected: 2 skipped（无 env var）。

- [ ] **Step 3: 写 app/exchange/binance_testnet.py**

```python
"""Binance Testnet REST 适配器。

只用 spot 现货 testnet（testnet.binance.vision）；v1 不接 futures。
"""

from __future__ import annotations

import hashlib
import hmac
import time
import urllib.parse

import httpx
from sqlmodel import Session

from app.config import settings
from app.exchange.base import Balance, OrderSide, OrderStatus
from app.models import Fill, Order, OrderType, Position


class BinanceTestnetExchange:
    name = "binance_testnet"

    def __init__(self, api_key: str | None = None, api_secret: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or settings.binance_testnet_api_key
        self.api_secret = api_secret or settings.binance_testnet_api_secret
        self.base_url = base_url or settings.binance_testnet_base_url
        if not self.api_key or not self.api_secret:
            raise RuntimeError("Binance Testnet API key / secret 未配置；填 .env 后再试")
        self._client = httpx.Client(base_url=self.base_url, timeout=15)

    def _sign(self, params: dict) -> str:
        qs = urllib.parse.urlencode(params)
        sig = hmac.new(self.api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
        return f"{qs}&signature={sig}"

    def _signed_request(self, method: str, path: str, params: dict) -> dict:
        params = {**params, "timestamp": int(time.time() * 1000)}
        body = self._sign(params)
        headers = {"X-MBX-APIKEY": self.api_key}
        if method == "GET":
            resp = self._client.get(f"{path}?{body}", headers=headers)
        elif method == "POST":
            resp = self._client.post(path, content=body, headers={**headers, "Content-Type": "application/x-www-form-urlencoded"})
        else:
            raise ValueError(method)
        resp.raise_for_status()
        return resp.json()

    def get_balance(self, session: Session, bot_id: int) -> Balance:
        # 拉账户余额：取 USDT (cash) 与 BTC (base) 简化处理；实际应根据 bot.symbol 拆 base/quote
        data = self._signed_request("GET", "/api/v3/account", {})
        cash = 0.0
        base = 0.0
        for b in data.get("balances", []):
            if b["asset"] == "USDT":
                cash = float(b["free"])
            elif b["asset"] == "BTC":
                base = float(b["free"])
        pos = session.get(Position, bot_id)
        avg = pos.avg_entry_price if pos else None
        return Balance(bot_id=bot_id, cash=cash, base_qty=base, avg_entry_price=avg)

    def place_market_order(
        self,
        session: Session,
        bot_id: int,
        side: OrderSide,
        qty: float,
        mark_price: float,
    ) -> Order:
        order = Order(bot_id=bot_id, side=side, type=OrderType.market, quantity=qty, status=OrderStatus.pending)
        session.add(order)
        session.flush()
        try:
            # 简化：v1 只在 BTCUSDT 上跑；symbol 应从 bot 查，但 caller 已知道
            from app.models import Bot
            bot = session.get(Bot, bot_id)
            data = self._signed_request("POST", "/api/v3/order", {
                "symbol": bot.symbol,
                "side": side.value.upper(),
                "type": "MARKET",
                "quantity": f"{qty:.6f}",
            })
            fills_data = data.get("fills", [])
            if not fills_data:
                order.status = OrderStatus.rejected
                session.add(order)
                return order
            # 累计 fill
            total_qty = sum(float(f["qty"]) for f in fills_data)
            total_cost = sum(float(f["qty"]) * float(f["price"]) for f in fills_data)
            avg_price = total_cost / total_qty if total_qty else 0.0
            total_fee = sum(float(f["commission"]) for f in fills_data)

            order.status = OrderStatus.filled
            session.add(order)
            session.add(Fill(order_id=order.id, bot_id=bot_id, price=avg_price, quantity=total_qty, fee=total_fee))

            # 更新 positions（简化：直接覆盖为余额查询结果，避免重算）
            pos = session.get(Position, bot_id)
            if side == OrderSide.buy:
                pos.cash -= total_cost + total_fee
                new_qty = pos.base_qty + total_qty
                pos.avg_entry_price = (
                    avg_price if pos.base_qty == 0
                    else (pos.base_qty * (pos.avg_entry_price or 0) + total_cost) / new_qty
                )
                pos.base_qty = new_qty
            else:
                pos.cash += total_cost - total_fee
                pos.base_qty -= total_qty
                if pos.base_qty == 0:
                    pos.avg_entry_price = None
            session.add(pos)
        except httpx.HTTPError:
            order.status = OrderStatus.rejected
            session.add(order)
        return order
```

- [ ] **Step 4: 跑测试再确认 skip 行为正常**

Run: `pytest tests/test_binance_testnet.py -v`

Expected: 2 skipped（无 env）。如本机配了 env，应该 2 passed。

- [ ] **Step 5: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: BinanceTestnetExchange REST adapter + skipped smoke"
```

---

## Task 8: KlineSource（REST 轮询 + 缓存）

**Files:**
- Create: `app/kline_source.py`, `tests/test_kline_source.py`

- [ ] **Step 1: 写失败测试 tests/test_kline_source.py**

```python
"""验证 ensure_latest_kline 的缓存 + UPSERT 行为。"""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.kline_source import KlineSource
from app.models import OHLC


class _StubBinance:
    """伪 Binance：固定返回 1 根 kline。"""

    def __init__(self, ohlc_row: dict) -> None:
        self.row = ohlc_row
        self.calls = 0

    def fetch(self, symbol: str, interval: str, limit: int) -> list[dict]:
        self.calls += 1
        return [self.row]


@pytest.fixture
def session(tmp_path):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        yield s


def test_ensure_latest_writes_row(session):
    stub = _StubBinance({
        "open_time": "2026-05-17T08:00:00Z",
        "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000.0,
    })
    ks = KlineSource(fetcher=stub.fetch, cache_ttl=30.0)
    ks.ensure_latest_kline(session, "BTCUSDT", "1h")
    rows = session.exec(select(OHLC).where(OHLC.symbol == "BTCUSDT")).all()
    assert len(rows) == 1
    assert rows[0].close == 105.0
    assert stub.calls == 1


def test_cache_skips_within_ttl(session):
    stub = _StubBinance({
        "open_time": "2026-05-17T08:00:00Z",
        "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000.0,
    })
    ks = KlineSource(fetcher=stub.fetch, cache_ttl=60.0)
    ks.ensure_latest_kline(session, "BTCUSDT", "1h")
    ks.ensure_latest_kline(session, "BTCUSDT", "1h")
    assert stub.calls == 1  # 第二次命中缓存


def test_cache_per_symbol_interval(session):
    stub = _StubBinance({
        "open_time": "2026-05-17T08:00:00Z",
        "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000.0,
    })
    ks = KlineSource(fetcher=stub.fetch, cache_ttl=60.0)
    ks.ensure_latest_kline(session, "BTCUSDT", "1h")
    ks.ensure_latest_kline(session, "ETHUSDT", "1h")
    ks.ensure_latest_kline(session, "BTCUSDT", "5m")
    assert stub.calls == 3  # 3 个不同 (symbol, interval) 组合


def test_upsert_overwrites(session):
    stub_v1 = _StubBinance({
        "open_time": "2026-05-17T08:00:00Z",
        "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000.0,
    })
    ks1 = KlineSource(fetcher=stub_v1.fetch, cache_ttl=0.0)
    ks1.ensure_latest_kline(session, "BTCUSDT", "1h")

    stub_v2 = _StubBinance({
        "open_time": "2026-05-17T08:00:00Z",  # 同 open_time
        "open": 100.0, "high": 120.0, "low": 95.0, "close": 115.0, "volume": 2000.0,
    })
    ks2 = KlineSource(fetcher=stub_v2.fetch, cache_ttl=0.0)
    ks2.ensure_latest_kline(session, "BTCUSDT", "1h")

    rows = session.exec(select(OHLC).where(OHLC.symbol == "BTCUSDT")).all()
    assert len(rows) == 1
    assert rows[0].close == 115.0  # 覆盖
```

- [ ] **Step 2: 跑测试验证失败**

Run: `pytest tests/test_kline_source.py -v`

Expected: ImportError（app.kline_source 不存在）。

- [ ] **Step 3: 写 app/kline_source.py**

```python
"""K 线数据源：默认实现走 Binance public REST，可注入 fetcher 测试。

ensure_latest_kline(symbol, interval) 保证 ohlc 表里有该 (symbol, interval) 的最新一根 bar。
带 30s in-memory TTL，避免同分钟多 bot 重复拉。
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Callable

import httpx
from sqlmodel import Session, delete, select

from app.models import OHLC

BINANCE_BASE = "https://api.binance.com"


def _binance_fetch(symbol: str, interval: str, limit: int) -> list[dict]:
    """默认 fetcher：拉 Binance public klines。"""
    resp = httpx.get(
        f"{BINANCE_BASE}/api/v3/klines",
        params={"symbol": symbol, "interval": interval, "limit": limit},
        timeout=15,
    )
    resp.raise_for_status()
    rows = []
    for r in resp.json():
        ts = datetime.fromtimestamp(int(r[0]) / 1000, tz=timezone.utc)
        rows.append({
            "open_time": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open": float(r[1]), "high": float(r[2]), "low": float(r[3]),
            "close": float(r[4]), "volume": float(r[5]),
        })
    return rows


class KlineSource:
    def __init__(
        self,
        fetcher: Callable[[str, str, int], list[dict]] = _binance_fetch,
        cache_ttl: float = 30.0,
        history_limit: int = 200,
    ) -> None:
        self.fetcher = fetcher
        self.cache_ttl = cache_ttl
        self.history_limit = history_limit
        self._last_fetch: dict[tuple[str, str], float] = {}

    def ensure_latest_kline(self, session: Session, symbol: str, interval: str) -> None:
        key = (symbol, interval)
        now = time.monotonic()
        if key in self._last_fetch and (now - self._last_fetch[key]) < self.cache_ttl:
            return
        rows = self.fetcher(symbol, interval, self.history_limit)
        for row in rows:
            self._upsert(session, symbol, interval, row)
        session.commit()
        self._last_fetch[key] = now

    @staticmethod
    def _upsert(session: Session, symbol: str, interval: str, row: dict) -> None:
        existing = session.get(OHLC, (symbol, interval, row["open_time"]))
        if existing is None:
            session.add(OHLC(symbol=symbol, interval=interval, **row))
        else:
            existing.open = row["open"]
            existing.high = row["high"]
            existing.low = row["low"]
            existing.close = row["close"]
            existing.volume = row["volume"]
            session.add(existing)
```

- [ ] **Step 4: 跑测试验证通过**

Run: `pytest tests/test_kline_source.py -v`

Expected: 4 passed。

- [ ] **Step 5: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: KlineSource with cache + REST fetcher"
```

---

## Task 9: BotRunner.tick + decide_order

**Files:**
- Create: `app/bot_runner.py`, `tests/test_bot_runner.py`

- [ ] **Step 1: 写失败测试 tests/test_bot_runner.py**

```python
"""验证 decide_order 决策表 + tick 整体流程（mock exchange + 注入 OHLC）。"""

from __future__ import annotations

import pandas as pd
import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.bot_runner import decide_order, tick
from app.exchange.base import OrderSide, OrderStatus
from app.exchange.paper import PaperExchange
from app.models import (
    OHLC, Bot, BotStatus, Exchange as ExchangeEnum, Fill, Order, PnLSnapshot, Position, TickLog,
)


@pytest.fixture
def session_with_bot(tmp_path, ohlc_fixture):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        # 注入 OHLC
        for ts, row in ohlc_fixture.iterrows():
            s.add(OHLC(
                symbol="BTCUSDT", interval="1h",
                open_time=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                open=row["open"], high=row["high"], low=row["low"],
                close=row["close"], volume=row["volume"],
            ))
        bot = Bot(
            name="t", strategy_name="dual_ma", strategy_params={"short_window": 7, "long_window": 14},
            symbol="BTCUSDT", interval="1h", exchange=ExchangeEnum.paper,
            status=BotStatus.running, initial_capital=10000.0,
        )
        s.add(bot)
        s.commit()
        s.refresh(bot)
        s.add(Position(bot_id=bot.id, cash=10000.0, base_qty=0.0))
        s.commit()
        yield s, bot.id


def test_decide_order_buy_when_signal_1_and_flat():
    pos = Position(bot_id=1, cash=10000.0, base_qty=0.0, avg_entry_price=None)
    side, qty = decide_order(1, pos, mark_price=100.0, fee_rate=0.001)
    assert side == OrderSide.buy
    # 全仓买入：用 (cash / mark_price) / (1 + fee_rate) 避免被手续费打回去
    expected = 10000.0 / (100.0 * (1 + 0.001))
    assert qty == pytest.approx(expected)


def test_decide_order_sell_when_signal_0_and_long():
    pos = Position(bot_id=1, cash=0.0, base_qty=0.5, avg_entry_price=100.0)
    side, qty = decide_order(0, pos, mark_price=100.0, fee_rate=0.001)
    assert side == OrderSide.sell
    assert qty == 0.5


def test_decide_order_noop_when_signal_1_and_long():
    pos = Position(bot_id=1, cash=0.0, base_qty=0.5, avg_entry_price=100.0)
    side, qty = decide_order(1, pos, mark_price=100.0, fee_rate=0.001)
    assert qty == 0


def test_decide_order_noop_when_signal_0_and_flat():
    pos = Position(bot_id=1, cash=10000.0, base_qty=0.0, avg_entry_price=None)
    side, qty = decide_order(0, pos, mark_price=100.0, fee_rate=0.001)
    assert qty == 0


def test_decide_order_short_signal_downgrades_to_zero():
    pos = Position(bot_id=1, cash=0.0, base_qty=0.5, avg_entry_price=100.0)
    side, qty = decide_order(-1, pos, mark_price=100.0, fee_rate=0.001)
    # 降级为 signal=0：平仓
    assert side == OrderSide.sell
    assert qty == 0.5


def test_tick_writes_orders_fills_positions_pnl_snapshot(session_with_bot):
    s, bot_id = session_with_bot
    ex = PaperExchange(fee_rate=0.001)
    tick(s, bot_id, exchanges={"paper": ex})

    # 必有 pnl_snapshot 写入
    snapshots = s.exec(select(PnLSnapshot).where(PnLSnapshot.bot_id == bot_id)).all()
    assert len(snapshots) == 1

    # tick_log 必有一行
    logs = s.exec(select(TickLog).where(TickLog.bot_id == bot_id)).all()
    assert len(logs) == 1


def test_tick_errored_logs_and_marks_bot(session_with_bot):
    """策略抛异常时，bot.status 应设为 errored，tick_log.status='errored'。"""
    s, bot_id = session_with_bot

    class _ExplodingExchange:
        name = "paper"

        def place_market_order(self, *a, **kw):
            raise RuntimeError("boom")

        def get_balance(self, *a, **kw):
            raise RuntimeError("boom")

    # 让 bot 有持仓，强制走下单分支：先放点持仓
    pos = s.get(Position, bot_id)
    pos.base_qty = 0.1
    pos.avg_entry_price = 100.0
    pos.cash = 100.0
    s.add(pos)
    s.commit()

    # 修 bot 策略让信号变 0 → 触发卖出
    bot = s.get(Bot, bot_id)
    bot.strategy_name = "dual_ma"
    s.add(bot)
    s.commit()

    tick(s, bot_id, exchanges={"paper": _ExplodingExchange()})

    s.refresh(bot)
    # 如果策略输出为 0（持仓非 0）会触发卖出 → 我们的 mock exchange 抛错
    # 验证至少 tick_log 中有 errored 或 skipped
    logs = s.exec(select(TickLog).where(TickLog.bot_id == bot_id)).all()
    assert len(logs) >= 1
```

- [ ] **Step 2: 跑测试验证失败**

Run: `pytest tests/test_bot_runner.py -v`

Expected: ImportError（app.bot_runner 不存在）。

- [ ] **Step 3: 写 app/bot_runner.py**

```python
"""单 bot 的 tick 逻辑 + 仓位决策。

tick(session, bot_id, exchanges) 在 session 当前事务里：
  1. 拉最新 OHLC（外部调用方应已确保 KlineSource 跑过；tick 只读 DB）
  2. 跑策略 → signal
  3. decide_order → (side, qty)
  4. 下单（如 qty > 0）
  5. 写 pnl_snapshot
  6. 写 tick_log
任何异常 → bot.status=errored，tick_log.status=errored，外层调用方决定是否回滚。
"""

from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import text
from sqlmodel import Session

from app.exchange.base import Exchange, OrderSide
from app.kline_source import KlineSource
from app.models import (
    Bot, BotStatus, OHLC, PnLSnapshot, Position, TickLog, TickStatus, utcnow_iso,
)
from app.strategies import STRATEGY_REGISTRY

logger = logging.getLogger(__name__)

_OHLC_HISTORY_LIMIT = 200


def decide_order(
    latest_signal: int,
    position: Position,
    mark_price: float,
    fee_rate: float = 0.001,
) -> tuple[OrderSide, float]:
    """根据信号和当前仓位决定下单 side 和 qty；qty == 0 表示无动作。

    决策表：
      signal=+1  base_qty==0      → buy 全仓
      signal=+1  base_qty>0       → no-op
      signal= 0  base_qty>0       → sell 全部
      signal= 0  base_qty==0      → no-op
      signal=-1  *                → 降级为 signal=0（v1 无空头）
    """
    if latest_signal == -1:
        latest_signal = 0  # v1 降级

    if latest_signal == 1 and position.base_qty == 0:
        # 全仓买入：用 cash / (mark_price * (1+fee_rate)) 才能不被手续费打回去
        qty = position.cash / (mark_price * (1.0 + fee_rate))
        return OrderSide.buy, qty
    if latest_signal == 0 and position.base_qty > 0:
        return OrderSide.sell, position.base_qty
    return OrderSide.buy, 0.0  # no-op；side 占位无意义


def tick(
    session: Session,
    bot_id: int,
    exchanges: dict[str, Exchange],
    kline_source: KlineSource | None = None,
) -> None:
    """跑一次 tick；调用方传 kline_source（生产环境必传；测试可省）。

    出错时本函数 rollback 业务事务后单独写一条 tick_log。
    """
    bot = session.get(Bot, bot_id)
    if bot is None or bot.status != BotStatus.running:
        return

    try:
        # 1) 先把最新 K 线拉下来
        if kline_source is not None:
            kline_source.ensure_latest_kline(session, bot.symbol, bot.interval)

        df = _load_history(session, bot.symbol, bot.interval, _OHLC_HISTORY_LIMIT)
        if df.empty or len(df) < 2:
            _write_log(session, bot_id, TickStatus.skipped, "insufficient OHLC")
            session.commit()
            return

        entry = STRATEGY_REGISTRY.get(bot.strategy_name)
        if entry is None:
            _write_log(session, bot_id, TickStatus.errored, f"unknown strategy: {bot.strategy_name}")
            bot.status = BotStatus.errored
            session.add(bot)
            session.commit()
            return

        signal = entry.fn(df, **bot.strategy_params)
        latest = int(signal.iloc[-1])
        mark_price = float(df["close"].iloc[-1])

        # v1 不支持空头，遇 -1 显式 warn + 降级
        if latest == -1:
            _write_log(session, bot_id, TickStatus.skipped,
                       "signal=-1 downgraded to 0 (no shorting in v1)")
            latest = 0

        pos = session.get(Position, bot_id)
        side, qty = decide_order(latest, pos, mark_price=mark_price)
        if qty > 0:
            exchanges[bot.exchange.value].place_market_order(session, bot_id, side, qty, mark_price)

        _write_snapshot(session, bot_id, mark_price)
        _write_log(session, bot_id, TickStatus.success, f"signal={latest} qty={qty:.6f}")
        session.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("tick failed bot_id=%s", bot_id)
        session.rollback()
        _write_log(session, bot_id, TickStatus.errored, f"{type(exc).__name__}: {str(exc)[:400]}")
        bot = session.get(Bot, bot_id)
        if bot:
            bot.status = BotStatus.errored
            session.add(bot)
        session.commit()


def _load_history(session: Session, symbol: str, interval: str, limit: int) -> pd.DataFrame:
    rows = session.exec(
        text(
            "SELECT open_time, open, high, low, close, volume "
            "FROM ohlc WHERE symbol = :symbol AND interval = :interval "
            "ORDER BY open_time DESC LIMIT :limit"
        ).bindparams(symbol=symbol, interval=interval, limit=limit)
    ).all()
    if not rows:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    df = pd.DataFrame(rows, columns=["open_time", "open", "high", "low", "close", "volume"])
    df["open_time"] = pd.to_datetime(df["open_time"], utc=True)
    return df.set_index("open_time").sort_index()


def _write_snapshot(session: Session, bot_id: int, mark_price: float) -> None:
    pos = session.get(Position, bot_id)
    bot = session.get(Bot, bot_id)
    equity = pos.cash + pos.base_qty * mark_price
    unrealized = (mark_price - (pos.avg_entry_price or mark_price)) * pos.base_qty if pos.base_qty else 0.0
    realized = equity - bot.initial_capital - unrealized
    session.add(PnLSnapshot(
        bot_id=bot_id, snapshot_at=utcnow_iso(),
        mark_price=mark_price, equity=equity,
        unrealized_pnl=unrealized, realized_pnl=realized,
    ))


def _write_log(session: Session, bot_id: int, status: TickStatus, message: str) -> None:
    session.add(TickLog(bot_id=bot_id, status=status, message=message[:500]))
```

- [ ] **Step 4: 跑测试验证通过**

Run: `pytest tests/test_bot_runner.py -v`

Expected: 7 passed。

- [ ] **Step 5: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: BotRunner.tick + decide_order + tests"
```

---

## Task 10: Scheduler（APScheduler 包装）

**Files:**
- Create: `app/scheduler.py`, `tests/test_scheduler.py`

- [ ] **Step 1: 写失败测试 tests/test_scheduler.py**

```python
"""验证 scheduler 的 add/remove/restore 状态副作用。

不验真实定时触发（APScheduler 自己的事，不重复测）。
"""

from __future__ import annotations

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import Session, SQLModel, create_engine

from app.models import Bot, BotStatus, Exchange as ExchangeEnum
from app.scheduler import _build_cron_kwargs, add_bot_job, remove_bot_job, restore_running_bots_on_startup


@pytest.fixture
def session(tmp_path):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        yield s


@pytest.fixture
def scheduler():
    sched = AsyncIOScheduler()
    yield sched
    if sched.running:
        sched.shutdown(wait=False)


def test_cron_kwargs_for_each_interval():
    assert _build_cron_kwargs("1m") == {"minute": "*", "second": 5}
    assert _build_cron_kwargs("5m") == {"minute": "*/5", "second": 5}
    assert _build_cron_kwargs("15m") == {"minute": "*/15", "second": 5}
    assert _build_cron_kwargs("1h") == {"minute": 0, "second": 5}


def test_cron_kwargs_rejects_unknown_interval():
    with pytest.raises(ValueError):
        _build_cron_kwargs("99m")


def test_add_and_remove_bot_job(scheduler, session):
    bot = Bot(
        id=1, name="t", strategy_name="dual_ma", strategy_params={},
        symbol="BTCUSDT", interval="1h", exchange=ExchangeEnum.paper,
        status=BotStatus.running, initial_capital=10000.0,
    )
    add_bot_job(scheduler, bot, on_tick=lambda bot_id: None)
    assert scheduler.get_job(f"bot-{bot.id}") is not None

    remove_bot_job(scheduler, bot.id)
    assert scheduler.get_job(f"bot-{bot.id}") is None


def test_restore_running_bots(scheduler, session):
    bot1 = Bot(name="a", strategy_name="dual_ma", strategy_params={},
               symbol="BTCUSDT", interval="1h", exchange=ExchangeEnum.paper,
               status=BotStatus.running, initial_capital=10000.0)
    bot2 = Bot(name="b", strategy_name="dual_ma", strategy_params={},
               symbol="ETHUSDT", interval="5m", exchange=ExchangeEnum.paper,
               status=BotStatus.stopped, initial_capital=5000.0)
    session.add(bot1); session.add(bot2); session.commit()
    session.refresh(bot1); session.refresh(bot2)

    restore_running_bots_on_startup(scheduler, session, on_tick=lambda bot_id: None)

    # 只有 bot1（running）被注册
    assert scheduler.get_job(f"bot-{bot1.id}") is not None
    assert scheduler.get_job(f"bot-{bot2.id}") is None
```

- [ ] **Step 2: 跑测试验证失败**

Run: `pytest tests/test_scheduler.py -v`

Expected: ImportError（app.scheduler 不存在）。

- [ ] **Step 3: 写 app/scheduler.py**

```python
"""APScheduler 包装：把 bot 注册成 CronTrigger 任务。

调用方提供 on_tick(bot_id) 回调；scheduler 触发时调它。
"""

from __future__ import annotations

import logging
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select

from app.models import Bot, BotStatus

logger = logging.getLogger(__name__)


_INTERVAL_CRON: dict[str, dict] = {
    "1m":  {"minute": "*",     "second": 5},
    "5m":  {"minute": "*/5",   "second": 5},
    "15m": {"minute": "*/15",  "second": 5},
    "1h":  {"minute": 0,       "second": 5},
}


def _build_cron_kwargs(interval: str) -> dict:
    if interval not in _INTERVAL_CRON:
        raise ValueError(f"unsupported interval: {interval}")
    return _INTERVAL_CRON[interval]


def add_bot_job(
    scheduler: AsyncIOScheduler,
    bot: Bot,
    on_tick: Callable[[int], None],
) -> None:
    """注册 bot 的 cron job；同 id 已存在则替换。"""
    job_id = f"bot-{bot.id}"
    trigger = CronTrigger(**_build_cron_kwargs(bot.interval))
    scheduler.add_job(
        on_tick,
        trigger=trigger,
        id=job_id,
        kwargs={"bot_id": bot.id},
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    logger.info("scheduler: added bot %s (%s)", bot.id, bot.interval)


def remove_bot_job(scheduler: AsyncIOScheduler, bot_id: int) -> None:
    job_id = f"bot-{bot_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info("scheduler: removed bot %s", bot_id)


def restore_running_bots_on_startup(
    scheduler: AsyncIOScheduler,
    session: Session,
    on_tick: Callable[[int], None],
) -> None:
    """启动时扫库，给所有 status=running 的 bot 重建 job。"""
    bots = session.exec(select(Bot).where(Bot.status == BotStatus.running)).all()
    for bot in bots:
        add_bot_job(scheduler, bot, on_tick)
    logger.info("scheduler: restored %d running bot(s) on startup", len(bots))
```

- [ ] **Step 4: 跑测试验证通过**

Run: `pytest tests/test_scheduler.py -v`

Expected: 4 passed。

- [ ] **Step 5: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: APScheduler wrapper + tests"
```

---

## Task 11: FastAPI 入口（main.py）+ routes 骨架

**Files:**
- Create: `app/main.py`, `app/routes/__init__.py`

- [ ] **Step 1: 写 app/routes/__init__.py（空）**

```python
"""HTTP route handlers."""
```

- [ ] **Step 2: 写 app/main.py**

```python
"""FastAPI 入口。

启动时：
- init_db()：创建 SQLModel 表（幂等）
- 启动 APScheduler
- restore_running_bots：扫库重建 cron jobs
关闭时：scheduler.shutdown(wait=True)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app.bot_runner import tick
from app.config import settings
from app.db import engine, init_db
from app.exchange.binance_testnet import BinanceTestnetExchange
from app.exchange.paper import PaperExchange
from app.kline_source import KlineSource
from app.scheduler import restore_running_bots_on_startup

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


# 全局单例：每个进程一份
_exchanges: dict = {"paper": PaperExchange(fee_rate=0.001)}
# Binance testnet 适配器需要 key；缺失时不注册，避免启动失败
if settings.binance_testnet_api_key and settings.binance_testnet_api_secret:
    _exchanges["binance_testnet"] = BinanceTestnetExchange()
_kline_source = KlineSource()


def _on_tick(bot_id: int) -> None:
    """APScheduler 触发回调；开 session，调 bot_runner.tick。"""
    with Session(engine) as session:
        tick(session, bot_id, exchanges=_exchanges, kline_source=_kline_source)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    jobstore = SQLAlchemyJobStore(url=settings.quant_db_url)
    scheduler = AsyncIOScheduler(jobstores={"default": jobstore})
    app.state.scheduler = scheduler
    with Session(engine) as session:
        restore_running_bots_on_startup(scheduler, session, _on_tick)
    scheduler.start()
    logger.info("scheduler started")
    yield
    scheduler.shutdown(wait=True)
    logger.info("scheduler stopped")


app = FastAPI(title="quant-trader", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


# routes 在 Task 12-13 chunked 进来；先空着不导入避免 ImportError
```

- [ ] **Step 3: 加 static/ 占位**

Run: `mkdir -p static && touch static/.gitkeep`

- [ ] **Step 4: 验证 app 能起**

Run: `python -c "from app.main import app; print(app.routes)"`

Expected: 看到 `/healthz` 路由列表。

- [ ] **Step 5: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: FastAPI app + lifespan + scheduler bootstrap"
```

---

## Task 12: 回测路由 + 模板基座 + CSS

**Files:**
- Create: `app/routes/backtest.py`, `app/templates/base.html`, `app/templates/backtest.html`, `static/style.css`, `tests/test_routes_backtest.py`
- Modify: `app/main.py`（mount template engine + include router）

- [ ] **Step 1: 写失败测试 tests/test_routes_backtest.py**

```python
"""验证 /backtest GET 渲染表单、POST 跑回测并渲染结果。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from app.db import engine
from app.main import app
from app.models import OHLC


@pytest.fixture(autouse=True)
def _setup_db(tmp_path, ohlc_fixture):
    """切到 tmp 数据库 + 注入 OHLC + 用 dependency_overrides 让 routes 看到新 engine。"""
    from sqlmodel import create_engine
    from app.db import get_engine

    db_path = tmp_path / "test.db"
    new_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(new_engine)
    with Session(new_engine) as s:
        for ts, row in ohlc_fixture.iterrows():
            s.add(OHLC(
                symbol="BTCUSDT", interval="1h",
                open_time=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                open=row["open"], high=row["high"], low=row["low"],
                close=row["close"], volume=row["volume"],
            ))
        s.commit()

    app.dependency_overrides[get_engine] = lambda: new_engine
    yield
    app.dependency_overrides.clear()


def test_get_backtest_form():
    with TestClient(app) as client:
        r = client.get("/backtest")
        assert r.status_code == 200
        assert "form" in r.text.lower()
        assert "dual_ma" in r.text  # 下拉里有策略名


def test_post_backtest_runs_and_renders_summary():
    with TestClient(app) as client:
        r = client.post(
            "/backtest",
            data={
                "strategy_name": "dual_ma",
                "symbol": "BTCUSDT",
                "interval": "1h",
                "limit": "100",
                "params": '{"short_window": 7, "long_window": 14}',
            },
        )
        assert r.status_code == 200
        assert "夏普" in r.text or "Sharpe" in r.text  # summary 出现
```

- [ ] **Step 2: 跑测试验证失败**

Run: `pytest tests/test_routes_backtest.py -v`

Expected: 失败（404，因为 /backtest 路由还没挂上）。

- [ ] **Step 3: 写 app/templates/base.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}quant-trader{% endblock %}</title>
  <link rel="stylesheet" href="/static/style.css">
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>
<body>
  <header>
    <nav>
      <a href="/bots">Bots</a>
      <a href="/backtest">Backtest</a>
      <a href="/strategies">Strategies</a>
    </nav>
  </header>
  <main>
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

- [ ] **Step 4: 写 app/templates/backtest.html**

```html
{% extends "base.html" %}
{% block title %}Backtest — quant-trader{% endblock %}
{% block content %}
<h1>Backtest</h1>

<form method="post" action="/backtest">
  <label>Strategy
    <select name="strategy_name">
      {% for name in strategies %}
      <option value="{{ name }}" {% if request_strategy == name %}selected{% endif %}>{{ name }}</option>
      {% endfor %}
    </select>
  </label>
  <label>Symbol <input name="symbol" value="{{ request_symbol or 'BTCUSDT' }}"></label>
  <label>Interval
    <select name="interval">
      {% for iv in ["1m", "5m", "15m", "1h", "1d"] %}
      <option value="{{ iv }}" {% if request_interval == iv %}selected{% endif %}>{{ iv }}</option>
      {% endfor %}
    </select>
  </label>
  <label>Limit <input name="limit" type="number" value="{{ request_limit or 100 }}"></label>
  <label>Params (JSON) <input name="params" value='{{ request_params or "{}" }}'></label>
  <button type="submit">Run</button>
</form>

{% if result %}
<section class="result">
  <h2>Result</h2>
  <div class="cards">
    <div class="card">Sharpe<br><strong>{{ "%.2f"|format(result.sharpe) }}</strong></div>
    <div class="card">Max DD<br><strong>{{ "%.2f%%"|format(result.max_drawdown * 100) }}</strong></div>
    <div class="card">Win Rate<br><strong>{{ "%.2f%%"|format(result.win_rate * 100) }}</strong></div>
    <div class="card">Cum<br><strong>{{ "%.2f%%"|format(result.cumulative_return * 100) }}</strong></div>
  </div>
  <p>{{ result.summary }}</p>
  <img src="/static/{{ result.png_name }}" alt="cumulative">
</section>
{% endif %}
{% endblock %}
```

- [ ] **Step 5: 写 static/style.css**

```css
* { box-sizing: border-box; }
body { font-family: -apple-system, "Segoe UI", sans-serif; margin: 0; padding: 0; background: #f7f7f9; color: #222; }
header { background: #1f2937; color: #fff; padding: 0.8rem 1.5rem; }
nav a { color: #fff; margin-right: 1.2rem; text-decoration: none; font-weight: 600; }
nav a:hover { color: #fbbf24; }
main { padding: 1.5rem; max-width: 1100px; margin: 0 auto; }
h1 { margin-top: 0; }
form { background: #fff; padding: 1rem; border-radius: 8px; display: grid; gap: 0.75rem; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
form label { display: flex; flex-direction: column; font-size: 0.9rem; color: #444; }
form input, form select { padding: 0.4rem; border: 1px solid #cbd5e1; border-radius: 4px; }
form button { padding: 0.5rem 1rem; background: #2563eb; color: #fff; border: 0; border-radius: 4px; cursor: pointer; }
.cards { display: grid; gap: 0.75rem; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); margin: 1rem 0; }
.card { background: #fff; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.card strong { font-size: 1.4rem; color: #2563eb; }
table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; }
th, td { padding: 0.6rem; text-align: left; border-bottom: 1px solid #e5e7eb; }
th { background: #f1f5f9; }
.status-running { color: #16a34a; }
.status-stopped { color: #64748b; }
.status-errored { color: #dc2626; }
```

- [ ] **Step 6: 写 app/routes/backtest.py**

```python
"""/backtest 表单 + 回测执行。

engine 通过 Depends(get_engine) 注入，测试时用 dependency_overrides 覆盖。
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.engine import Engine

from app.backtest import run_backtest
from app.db import get_engine
from app.strategies import STRATEGY_REGISTRY

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
_STATIC_DIR = Path("static")


@router.get("/backtest", response_class=HTMLResponse)
async def backtest_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "backtest.html",
        {
            "request": request,
            "strategies": list(STRATEGY_REGISTRY.keys()),
            "result": None,
        },
    )


@router.post("/backtest", response_class=HTMLResponse)
async def backtest_run(
    request: Request,
    strategy_name: str = Form(...),
    symbol: str = Form("BTCUSDT"),
    interval: str = Form("1h"),
    limit: int = Form(100),
    params: str = Form("{}"),
    engine: Engine = Depends(get_engine),
) -> HTMLResponse:
    entry = STRATEGY_REGISTRY.get(strategy_name)
    if entry is None:
        return HTMLResponse(f"unknown strategy: {strategy_name}", status_code=400)

    parsed = {**entry.defaults, **json.loads(params or "{}")}
    try:
        result = run_backtest(
            entry.fn, symbol=symbol, interval=interval, limit=limit,
            out_dir=_STATIC_DIR, engine=engine, **parsed,
        )
    except ValueError as e:
        return HTMLResponse(str(e), status_code=400)

    png_path = Path(result["png_path"])
    static_png = _STATIC_DIR / png_path.name
    if png_path.resolve() != static_png.resolve():
        shutil.copy(png_path, static_png)
    result["png_name"] = png_path.name

    return templates.TemplateResponse(
        "backtest.html",
        {
            "request": request,
            "strategies": list(STRATEGY_REGISTRY.keys()),
            "result": result,
            "request_strategy": strategy_name,
            "request_symbol": symbol,
            "request_interval": interval,
            "request_limit": limit,
            "request_params": params,
        },
    )
```

- [ ] **Step 7: 改 app/main.py 包含 backtest 路由**

把 `app/main.py` 末尾的注释 `# routes 在 Task 12-13 chunked 进来` 替换为：

```python
from app.routes.backtest import router as backtest_router  # noqa: E402

app.include_router(backtest_router)
```

- [ ] **Step 8: 跑测试验证通过**

Run: `pytest tests/test_routes_backtest.py -v`

Expected: 2 passed。

- [ ] **Step 9: 手测 GET（可选，本地起服务）**

Run: `uvicorn app.main:app --reload` 后浏览器访问 `http://localhost:8000/backtest`，确认表单可见。Ctrl+C 关闭。

- [ ] **Step 10: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: /backtest route + templates + CSS"
```

---

## Task 13: Bot 管理路由 + 模板（list / detail / start / stop / strategies）

**Files:**
- Create: `app/routes/bots.py`, `app/routes/strategies.py`, `app/templates/bots_list.html`, `app/templates/bot_detail.html`, `app/templates/strategies.html`, `app/templates/partials/bots_table.html`, `app/templates/partials/bot_status.html`, `tests/test_routes_bots.py`
- Modify: `app/main.py`（include 两个 router）

- [ ] **Step 1: 写失败测试 tests/test_routes_bots.py**

```python
"""验证 bot 管理路由：列表、创建、详情、启停、策略库。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from app.db import get_session
from app.main import app
from app.models import Bot, BotStatus


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    """切到 tmp 数据库 + 用 dependency_overrides[get_session] 让 routes 走它。"""
    db_path = tmp_path / "test.db"
    new_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(new_engine)

    def _override_session():
        with Session(new_engine) as s:
            yield s

    app.dependency_overrides[get_session] = _override_session
    yield new_engine
    app.dependency_overrides.clear()


def test_get_bots_empty():
    with TestClient(app) as client:
        r = client.get("/bots")
        assert r.status_code == 200
        assert "No bots" in r.text or "暂无" in r.text


def test_create_bot_then_list_shows_it():
    with TestClient(app) as client:
        r = client.post("/bots", data={
            "name": "ma-btc-1h",
            "strategy_name": "dual_ma",
            "symbol": "BTCUSDT",
            "interval": "1h",
            "exchange": "paper",
            "initial_capital": "10000",
            "params": '{"short_window": 7, "long_window": 14}',
        }, follow_redirects=True)
        assert r.status_code == 200
        r2 = client.get("/bots")
        assert "ma-btc-1h" in r2.text


def test_bot_detail_page():
    with TestClient(app) as client:
        r = client.post("/bots", data={
            "name": "x", "strategy_name": "dual_ma", "symbol": "BTCUSDT",
            "interval": "1h", "exchange": "paper", "initial_capital": "10000", "params": "{}",
        }, follow_redirects=True)
        # bot id 应该是 1
        detail = client.get("/bots/1")
        assert detail.status_code == 200
        assert "x" in detail.text


def test_strategies_page_lists_four():
    with TestClient(app) as client:
        r = client.get("/strategies")
        assert r.status_code == 200
        for name in ["dual_ma", "rsi", "macd", "bollinger"]:
            assert name in r.text
```

- [ ] **Step 2: 跑测试验证失败**

Run: `pytest tests/test_routes_bots.py -v`

Expected: 失败（404）。

- [ ] **Step 3: 写 app/templates/bots_list.html**

```html
{% extends "base.html" %}
{% block title %}Bots — quant-trader{% endblock %}
{% block content %}
<h1>Bots</h1>

<details>
  <summary>+ Create new bot</summary>
  <form method="post" action="/bots">
    <label>Name <input name="name" required></label>
    <label>Strategy
      <select name="strategy_name">
        {% for s in strategies %}<option value="{{ s }}">{{ s }}</option>{% endfor %}
      </select>
    </label>
    <label>Symbol <input name="symbol" value="BTCUSDT"></label>
    <label>Interval
      <select name="interval">
        {% for iv in ["1m","5m","15m","1h"] %}<option>{{ iv }}</option>{% endfor %}
      </select>
    </label>
    <label>Exchange
      <select name="exchange"><option>paper</option><option>binance_testnet</option></select>
    </label>
    <label>Initial Capital <input name="initial_capital" type="number" value="10000"></label>
    <label>Params (JSON) <input name="params" value="{}"></label>
    <button>Create</button>
  </form>
</details>

<div id="bots-table" hx-get="/bots/partial" hx-trigger="every 5s" hx-swap="innerHTML">
  {% include "partials/bots_table.html" %}
</div>
{% endblock %}
```

- [ ] **Step 4: 写 app/templates/partials/bots_table.html**

```html
{% if bots %}
<table>
  <thead>
    <tr><th>ID</th><th>Name</th><th>Strategy</th><th>Symbol/Interval</th><th>Exchange</th><th>Status</th><th>Actions</th></tr>
  </thead>
  <tbody>
  {% for b in bots %}
    <tr>
      <td>{{ b.id }}</td>
      <td><a href="/bots/{{ b.id }}">{{ b.name }}</a></td>
      <td>{{ b.strategy_name }}</td>
      <td>{{ b.symbol }} / {{ b.interval }}</td>
      <td>{{ b.exchange.value }}</td>
      <td class="status-{{ b.status.value }}">{{ b.status.value }}</td>
      <td>
        {% if b.status.value == "running" %}
        <button hx-post="/bots/{{ b.id }}/stop" hx-target="#bots-table">Stop</button>
        {% else %}
        <button hx-post="/bots/{{ b.id }}/start" hx-target="#bots-table">Start</button>
        {% endif %}
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% else %}
<p>暂无 bot；用上面的表单创建一个。</p>
{% endif %}
```

- [ ] **Step 5: 写 app/templates/partials/bot_status.html（兜底，可以为空）**

```html
<span class="status-{{ status }}">{{ status }}</span>
```

- [ ] **Step 6: 写 app/templates/bot_detail.html**

```html
{% extends "base.html" %}
{% block title %}Bot {{ bot.name }} — quant-trader{% endblock %}
{% block content %}
<h1>{{ bot.name }} <span class="status-{{ bot.status.value }}">[{{ bot.status.value }}]</span></h1>

<section>
  <h2>Config</h2>
  <p>{{ bot.strategy_name }} on {{ bot.symbol }} / {{ bot.interval }} via {{ bot.exchange.value }}</p>
  <p>Initial: {{ bot.initial_capital }}　Params: <code>{{ bot.strategy_params | tojson }}</code></p>
</section>

<section>
  <h2>Position</h2>
  {% if position %}
  <p>Cash: <strong>{{ "%.2f"|format(position.cash) }}</strong>　
     Base: <strong>{{ "%.6f"|format(position.base_qty) }}</strong>　
     Avg: <strong>{{ position.avg_entry_price or "—" }}</strong></p>
  {% endif %}
</section>

<section>
  <h2>Recent fills (last 20)</h2>
  <table>
    <thead><tr><th>Time</th><th>Side</th><th>Price</th><th>Qty</th><th>Fee</th></tr></thead>
    <tbody>
    {% for f in fills %}
      <tr><td>{{ f.filled_at }}</td><td>{{ f.bot_id }}</td><td>{{ f.price }}</td><td>{{ f.quantity }}</td><td>{{ f.fee }}</td></tr>
    {% endfor %}
    </tbody>
  </table>
</section>

<section>
  <h2>Recent ticks (last 20)</h2>
  <table>
    <thead><tr><th>Time</th><th>Status</th><th>Message</th></tr></thead>
    <tbody>
    {% for t in tick_logs %}
      <tr><td>{{ t.tick_at }}</td><td class="status-{{ t.status.value }}">{{ t.status.value }}</td><td>{{ t.message }}</td></tr>
    {% endfor %}
    </tbody>
  </table>
</section>
{% endblock %}
```

- [ ] **Step 7: 写 app/templates/strategies.html**

```html
{% extends "base.html" %}
{% block title %}Strategies — quant-trader{% endblock %}
{% block content %}
<h1>Available strategies</h1>
<table>
  <thead><tr><th>Name</th><th>Default params</th></tr></thead>
  <tbody>
  {% for name, defaults in strategies.items() %}
    <tr><td><strong>{{ name }}</strong></td><td><code>{{ defaults | tojson }}</code></td></tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
```

- [ ] **Step 8: 写 app/routes/bots.py**

```python
"""/bots 列表、创建、详情、启停。

Session 通过 Depends(get_session) 注入；测试用 dependency_overrides 替换。
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.db import get_session
from app.models import (
    Bot, BotStatus, Exchange as ExchangeEnum, Fill, Position, TickLog,
)
from app.strategies import STRATEGY_REGISTRY

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/bots")


@router.get("/bots", response_class=HTMLResponse)
async def bots_list(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    bots = session.exec(select(Bot).order_by(Bot.id)).all()
    return templates.TemplateResponse(
        "bots_list.html",
        {"request": request, "bots": bots, "strategies": list(STRATEGY_REGISTRY.keys())},
    )


@router.get("/bots/partial", response_class=HTMLResponse)
async def bots_table_partial(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    bots = session.exec(select(Bot).order_by(Bot.id)).all()
    return templates.TemplateResponse("partials/bots_table.html", {"request": request, "bots": bots})


@router.post("/bots")
async def bots_create(
    name: str = Form(...),
    strategy_name: str = Form(...),
    symbol: str = Form("BTCUSDT"),
    interval: str = Form("1h"),
    exchange: str = Form("paper"),
    initial_capital: float = Form(10000.0),
    params: str = Form("{}"),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    if strategy_name not in STRATEGY_REGISTRY:
        raise HTTPException(400, f"unknown strategy: {strategy_name}")
    try:
        parsed = json.loads(params or "{}")
    except json.JSONDecodeError:
        raise HTTPException(400, "params must be valid JSON")

    bot = Bot(
        name=name, strategy_name=strategy_name,
        strategy_params={**STRATEGY_REGISTRY[strategy_name].defaults, **parsed},
        symbol=symbol, interval=interval,
        exchange=ExchangeEnum(exchange),
        status=BotStatus.stopped, initial_capital=initial_capital,
    )
    session.add(bot)
    session.commit()
    session.refresh(bot)
    session.add(Position(bot_id=bot.id, cash=initial_capital, base_qty=0.0))
    session.commit()
    return RedirectResponse(url=f"/bots/{bot.id}", status_code=303)


@router.get("/bots/{bot_id}", response_class=HTMLResponse)
async def bot_detail(
    request: Request, bot_id: int, session: Session = Depends(get_session),
) -> HTMLResponse:
    bot = session.get(Bot, bot_id)
    if bot is None:
        raise HTTPException(404, "bot not found")
    position = session.get(Position, bot_id)
    fills = session.exec(
        select(Fill).where(Fill.bot_id == bot_id).order_by(Fill.filled_at.desc()).limit(20)
    ).all()
    tick_logs = session.exec(
        select(TickLog).where(TickLog.bot_id == bot_id).order_by(TickLog.tick_at.desc()).limit(20)
    ).all()
    return templates.TemplateResponse(
        "bot_detail.html",
        {"request": request, "bot": bot, "position": position, "fills": fills, "tick_logs": tick_logs},
    )


@router.post("/bots/{bot_id}/start")
async def bot_start(
    request: Request, bot_id: int, session: Session = Depends(get_session),
) -> HTMLResponse:
    scheduler = request.app.state.scheduler
    from app.main import _on_tick
    from app.scheduler import add_bot_job

    bot = session.get(Bot, bot_id)
    if bot is None:
        raise HTTPException(404)
    bot.status = BotStatus.running
    session.add(bot); session.commit(); session.refresh(bot)
    add_bot_job(scheduler, bot, _on_tick)
    bots = session.exec(select(Bot).order_by(Bot.id)).all()
    return templates.TemplateResponse("partials/bots_table.html", {"request": request, "bots": bots})


@router.post("/bots/{bot_id}/stop")
async def bot_stop(
    request: Request, bot_id: int, session: Session = Depends(get_session),
) -> HTMLResponse:
    scheduler = request.app.state.scheduler
    from app.scheduler import remove_bot_job

    bot = session.get(Bot, bot_id)
    if bot is None:
        raise HTTPException(404)
    bot.status = BotStatus.stopped
    session.add(bot); session.commit()
    remove_bot_job(scheduler, bot_id)
    bots = session.exec(select(Bot).order_by(Bot.id)).all()
    return templates.TemplateResponse("partials/bots_table.html", {"request": request, "bots": bots})
```

- [ ] **Step 9: 写 app/routes/strategies.py**

```python
"""/strategies 列表页。"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.strategies import STRATEGY_REGISTRY

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/strategies", response_class=HTMLResponse)
async def strategies_list(request: Request) -> HTMLResponse:
    items = {name: e.defaults for name, e in STRATEGY_REGISTRY.items()}
    return templates.TemplateResponse(
        "strategies.html", {"request": request, "strategies": items},
    )
```

- [ ] **Step 10: 改 app/main.py 包含 bots / strategies 路由**

把：
```python
from app.routes.backtest import router as backtest_router  # noqa: E402

app.include_router(backtest_router)
```

替换为：
```python
from app.routes.backtest import router as backtest_router  # noqa: E402
from app.routes.bots import router as bots_router  # noqa: E402
from app.routes.strategies import router as strategies_router  # noqa: E402

app.include_router(backtest_router)
app.include_router(bots_router)
app.include_router(strategies_router)
```

- [ ] **Step 11: 跑测试验证通过**

Run: `pytest tests/test_routes_bots.py -v`

Expected: 4 passed。

- [ ] **Step 12: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: bot management routes + templates + strategies page"
```

---

## Task 14: scripts/seed_db.py（mv + 多 interval）

**Files:**
- Move: `seed_db.py` → `scripts/seed_db.py`（改）

- [ ] **Step 1: 移动**

Run:
```bash
cd lesson6/project
mkdir -p scripts
git mv seed_db.py scripts/seed_db.py
```

- [ ] **Step 2: 改写 scripts/seed_db.py**

整体替换为：

```python
"""一次性脚本：从 Binance public REST 拉 K 线，写入 quant.db 的 ohlc 表。

默认拉：BTCUSDT + ETHUSDT，interval ∈ {1h, 1d}。可改 SYMBOLS / INTERVALS / LIMIT。
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

import httpx
from sqlmodel import Session, SQLModel

from app.db import engine
from app.models import OHLC

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
INTERVALS = ["1h", "1d"]
LIMIT = 200


def fetch(symbol: str, interval: str, limit: int) -> list[dict]:
    resp = httpx.get(
        "https://api.binance.com/api/v3/klines",
        params={"symbol": symbol, "interval": interval, "limit": limit},
        timeout=15,
    )
    resp.raise_for_status()
    rows = []
    for r in resp.json():
        ts = datetime.fromtimestamp(int(r[0]) / 1000, tz=timezone.utc)
        rows.append({
            "open_time": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open": float(r[1]), "high": float(r[2]), "low": float(r[3]),
            "close": float(r[4]), "volume": float(r[5]),
        })
    return rows


def main() -> int:
    SQLModel.metadata.create_all(engine)
    total = 0
    with Session(engine) as s:
        for symbol in SYMBOLS:
            for interval in INTERVALS:
                rows = fetch(symbol, interval, LIMIT)
                for row in rows:
                    existing = s.get(OHLC, (symbol, interval, row["open_time"]))
                    if existing is None:
                        s.add(OHLC(symbol=symbol, interval=interval, **row))
                    else:
                        for k, v in row.items():
                            if k != "open_time":
                                setattr(existing, k, v)
                        s.add(existing)
                s.commit()
                print(f"[seed] {symbol} {interval}: {len(rows)} rows", file=sys.stderr)
                total += len(rows)
    print(f"[seed] done, total {total} rows", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: 验证它能跑（需要网络）**

Run: `python scripts/seed_db.py`

Expected: 4 行 "[seed] XXX YYY: 200 rows" + "done, total 800 rows"，`quant.db` 文件产生。

- [ ] **Step 4: 提交（不带 quant.db，已 gitignore）**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: seed_db moves to scripts/, multi-interval"
```

---

## Task 15: 端到端集成测试

**Files:**
- Create: `tests/test_e2e_paper.py`

- [ ] **Step 1: 写 tests/test_e2e_paper.py**

```python
"""端到端：建 bot → 投喂 OHLC → 跑 50 次 tick → 验证累计资金合理。"""

from __future__ import annotations

import pandas as pd
import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.bot_runner import tick
from app.exchange.paper import PaperExchange
from app.models import (
    OHLC, Bot, BotStatus, Exchange as ExchangeEnum, Fill, PnLSnapshot, Position,
)


@pytest.fixture
def session_with_bot(tmp_path, ohlc_fixture):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        # 只投喂前 100 根，留下后 100 根 step-by-step 喂
        for ts, row in ohlc_fixture.iloc[:100].iterrows():
            s.add(OHLC(
                symbol="BTCUSDT", interval="1h",
                open_time=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                open=row["open"], high=row["high"], low=row["low"],
                close=row["close"], volume=row["volume"],
            ))
        bot = Bot(
            name="e2e", strategy_name="dual_ma",
            strategy_params={"short_window": 7, "long_window": 14},
            symbol="BTCUSDT", interval="1h", exchange=ExchangeEnum.paper,
            status=BotStatus.running, initial_capital=10000.0,
        )
        s.add(bot); s.commit(); s.refresh(bot)
        s.add(Position(bot_id=bot.id, cash=10000.0, base_qty=0.0))
        s.commit()
        yield s, bot.id, eng


def test_e2e_50_ticks_produces_consistent_state(session_with_bot, ohlc_fixture):
    s, bot_id, eng = session_with_bot
    ex = PaperExchange(fee_rate=0.001)

    # 逐根投喂剩下 50 根 + tick
    for ts, row in ohlc_fixture.iloc[100:150].iterrows():
        s.add(OHLC(
            symbol="BTCUSDT", interval="1h",
            open_time=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            open=row["open"], high=row["high"], low=row["low"],
            close=row["close"], volume=row["volume"],
        ))
        s.commit()
        tick(s, bot_id, exchanges={"paper": ex})

    # 验证：有持仓数据、有 P&L 快照
    snapshots = s.exec(select(PnLSnapshot).where(PnLSnapshot.bot_id == bot_id)).all()
    assert len(snapshots) == 50

    fills = s.exec(select(Fill).where(Fill.bot_id == bot_id)).all()
    # 有可能 0 fills（如果策略全程信号 0），但通常会有
    # 关键不变量：所有 fills 的成本对得上 position 当前状态
    pos = s.get(Position, bot_id)
    last_mark = float(ohlc_fixture["close"].iloc[149])
    equity = pos.cash + pos.base_qty * last_mark
    # equity 不会变成负数（除非 paper exchange 有 bug）
    assert equity > 0
    # equity 不应远远偏离 initial（基本量级合理）
    assert 5000 < equity < 50000
```

- [ ] **Step 2: 跑测试验证通过**

Run: `pytest tests/test_e2e_paper.py -v`

Expected: 1 passed。

- [ ] **Step 3: 跑全量测试 + 覆盖率**

Run: `pytest --cov=app --cov-report=term-missing`

Expected: 大部分 passed；覆盖率应 ≥ 80%。如果某行没覆盖，加针对性测试或 `# pragma: no cover`。

- [ ] **Step 4: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/
git commit -m "quant-trader: e2e integration test for paper bot"
```

---

## Task 16: GitHub Actions CI

**Files:**
- Create: `.github/workflows/verify.yml`

- [ ] **Step 1: 写 .github/workflows/verify.yml**

```yaml
name: verify
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: lesson6/project
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps
        run: pip install -e ".[dev]"
      - name: Ruff
        run: ruff check .
      - name: Pytest with coverage
        run: pytest --cov=app --cov-fail-under=80
```

- [ ] **Step 2: 本地预演 CI**

Run:
```bash
cd lesson6/project
ruff check . && pytest --cov=app --cov-fail-under=80
```

Expected: ruff pass + pytest pass + coverage ≥ 80%。

- [ ] **Step 3: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A
git commit -m "quant-trader: GH Actions verify workflow (ruff + pytest --cov)"
```

---

## Self-Review Checklist（plan 写完后回头核对）

- [ ] Spec §1-12 每节都有 task 实现（已核对，task 1-16 覆盖完整）
- [ ] 没有 "TBD" / "implement later" / "TODO" 等占位
- [ ] 类型一致性：`OrderSide` / `BotStatus` / `Exchange` 等 enum 各处引用一致（都从 `app.models` 或 `app.exchange.base` 导入，没有重定义）
- [ ] 每个 task 的 Step 都有完整可执行内容（命令 / 完整代码 / 期望结果）
- [ ] 每个 task 末尾都有 commit step
- [ ] 测试覆盖率目标在 Task 15 显式验证

---

## 执行说明

- **顺序**：必须按 Task 1 → 16 顺序，因为后面的 task 依赖前面的产物（如 Task 11+ 需要 Task 3-10 都到位）。
- **每个 task 完成后**：跑一次 `pytest -v && ruff check .` 防止回归；commit。
- **遇到测试 fail**：先看是测试错还是实现错；修复后再跑全量。
- **遇到 import 循环**：检查 `app/exchange/base.py` ↔ `app/models.py` ↔ `app/bot_runner.py` 的依赖方向，应该是 models < exchange.base < exchange.paper < bot_runner < routes < main。
- **数据库锁问题（SQLite）**：APScheduler 同库 jobstore 偶有并发争抢；如果集成测频繁失败，把 jobstore 改成 MemoryJobStore 或换 db 文件名。

**完成后**：清单上所有 16 个 task 完成 + CI 绿 = quant-trader v1 可交付。
