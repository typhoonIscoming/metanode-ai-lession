# Backtest Custom Time Range Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/backtest` 表单加自定义起止时间字段；缺数据时自动从 Binance public REST 拉补（最多 200000 根 K 线）；保持向后兼容（不填时间段 → 沿用 limit）。

**Architecture:** 新模块 `app/kline_fetcher.py` 提供 `fetch_range` + `ensure_range_in_db` 可注入 fetcher 的底层。`app/backtest.py:load_ohlc` 增 keyword-only 的 `start_time` / `end_time`，与现有 `limit` 互斥。`app/routes/backtest.py:backtest_run` 先 parse 表单 → 算 bar 数 → 护栏 → ensure_range_in_db → run_backtest。

**Tech Stack:** httpx + SQLModel（不变）；HTML5 `<input type="datetime-local">`（前端无 JS）。

---

## File Structure

| 文件 | 改动 | 责任 |
|---|---|---|
| `app/kline_fetcher.py` | **新建** | INTERVAL_SECONDS / fetch_range（分页 REST）/ ensure_range_in_db（diff + UPSERT）/ _iso_to_ts_ms |
| `app/backtest.py` | 修改 `load_ohlc` 和 `run_backtest` 签名 | 加 start_time/end_time 参数 + range 模式 SQL + range 模式 PNG 文件名 |
| `app/routes/backtest.py` | 修改 `backtest_run` | 接 2 个新 Form 字段 → 估算护栏 → 调 ensure_range_in_db → 调 run_backtest |
| `app/templates/backtest.html` | 修改表单 | 加 2 个 `<input type="datetime-local">` + 中文 hint |
| `tests/test_backtest.py` | 加 1 测 | load_ohlc 范围模式 |
| `tests/test_kline_fetcher.py` | **新建** | 3 测：empty DB / partial fill / fully present |
| `tests/test_routes_backtest.py` | 加 1 测 | POST /backtest with start/end + monkeypatch 避网络 |

---

## Task 1: 新建 `app/kline_fetcher.py` + 3 个单测

**Files:**
- Create: `lesson6/project/app/kline_fetcher.py`
- Create: `lesson6/project/tests/test_kline_fetcher.py`

- [ ] **Step 1: 写失败测试 `tests/test_kline_fetcher.py`**

```python
"""验证 ensure_range_in_db 的 diff + 分块 + UPSERT 行为。

fetch_range 单测略——它是薄包装的 HTTP 调用，不在 v1.2 覆盖范围。
"""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.kline_fetcher import _iso_to_ts_ms, ensure_range_in_db
from app.models import OHLC


@pytest.fixture
def session(tmp_path):
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        yield s


def _stub_factory(rows_per_call):
    """构造一个 stub fetcher，按调用顺序返回预设的 rows 列表。"""
    calls = []

    def stub(symbol, interval, start_ts_ms, end_ts_ms):
        calls.append((symbol, interval, start_ts_ms, end_ts_ms))
        return rows_per_call.pop(0) if rows_per_call else []

    stub.calls = calls
    return stub


def _row(open_time_iso: str, close: float = 100.0) -> dict:
    return {
        "open_time": open_time_iso,
        "open": close, "high": close + 1, "low": close - 1,
        "close": close, "volume": 1000.0,
    }


def test_ensure_range_with_empty_db_inserts_all(session):
    rows = [_row("2025-01-01T00:00:00Z", 100),
            _row("2025-01-01T01:00:00Z", 101),
            _row("2025-01-01T02:00:00Z", 102)]
    stub = _stub_factory([rows])

    n = ensure_range_in_db(
        session, "BTCUSDT", "1h",
        "2025-01-01T00:00:00Z", "2025-01-01T02:00:00Z",
        fetcher=stub,
    )
    assert n == 3
    assert len(stub.calls) == 1
    db_rows = session.exec(select(OHLC).where(OHLC.symbol == "BTCUSDT")).all()
    assert len(db_rows) == 3


def test_ensure_range_skips_existing(session):
    # DB 预置 2025-01-01T01:00:00Z 一条；范围要 00/01/02 三条
    session.add(OHLC(symbol="BTCUSDT", interval="1h",
                     open_time="2025-01-01T01:00:00Z",
                     open=200, high=201, low=199, close=200, volume=500))
    session.commit()

    # stub fetcher 应该被调 2 次（00:00 一段，02:00 一段，因为 01:00 已存在打断了连续区段）
    stub = _stub_factory([
        [_row("2025-01-01T00:00:00Z", 100)],
        [_row("2025-01-01T02:00:00Z", 102)],
    ])
    n = ensure_range_in_db(
        session, "BTCUSDT", "1h",
        "2025-01-01T00:00:00Z", "2025-01-01T02:00:00Z",
        fetcher=stub,
    )
    assert n == 2
    assert len(stub.calls) == 2
    rows = session.exec(select(OHLC).where(OHLC.symbol == "BTCUSDT").order_by(OHLC.open_time)).all()
    assert len(rows) == 3
    # 已有那条 close=200 没被改
    middle = next(r for r in rows if r.open_time == "2025-01-01T01:00:00Z")
    assert middle.close == 200


def test_ensure_range_all_present_does_not_call_fetcher(session):
    for hour in range(3):
        session.add(OHLC(symbol="BTCUSDT", interval="1h",
                         open_time=f"2025-01-01T0{hour}:00:00Z",
                         open=100, high=101, low=99, close=100, volume=500))
    session.commit()

    stub = _stub_factory([])
    n = ensure_range_in_db(
        session, "BTCUSDT", "1h",
        "2025-01-01T00:00:00Z", "2025-01-01T02:00:00Z",
        fetcher=stub,
    )
    assert n == 0
    assert stub.calls == []


def test_iso_to_ts_ms_round_trip():
    ts = _iso_to_ts_ms("2025-01-01T00:00:00Z")
    assert ts == 1735689600000  # 2025-01-01 00:00 UTC in ms
```

- [ ] **Step 2: 跑测试验证它失败**

Run: `cd /mnt/d/培训/ai_lesson/lesson6/project && pytest tests/test_kline_fetcher.py -v`
Expected: ImportError（app.kline_fetcher 不存在）。

- [ ] **Step 3: 写 `app/kline_fetcher.py`**

```python
"""Binance kline 分页拉取 + UPSERT 进 ohlc 表的可复用底层。

供 /backtest 自定义时间段使用；KlineSource（live tick 路径）不变。
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import httpx
from sqlmodel import Session, select

from app.models import OHLC

BINANCE_BASE = "https://api.binance.com"

INTERVAL_SECONDS: dict[str, int] = {
    "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "2h": 7200, "4h": 14400, "6h": 21600, "8h": 28800, "12h": 43200,
    "1d": 86400, "3d": 259200, "1w": 604800,
}


def fetch_range(symbol: str, interval: str, start_ts_ms: int, end_ts_ms: int) -> list[dict]:
    """Binance public klines 按 1000-bar 分页拉 [start, end] 区间。"""
    rows: list[dict] = []
    cursor = start_ts_ms
    interval_ms = INTERVAL_SECONDS[interval] * 1000
    while cursor <= end_ts_ms:
        resp = httpx.get(
            f"{BINANCE_BASE}/api/v3/klines",
            params={
                "symbol": symbol, "interval": interval,
                "startTime": cursor, "endTime": end_ts_ms, "limit": 1000,
            },
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        for r in batch:
            ts = datetime.fromtimestamp(int(r[0]) / 1000, tz=UTC)
            rows.append({
                "open_time": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": float(r[1]), "high": float(r[2]), "low": float(r[3]),
                "close": float(r[4]), "volume": float(r[5]),
            })
        last_open_ms = int(batch[-1][0])
        cursor = last_open_ms + interval_ms
        if len(batch) < 1000:
            break
    return rows


def ensure_range_in_db(
    session: Session,
    symbol: str,
    interval: str,
    start_iso: str,
    end_iso: str,
    fetcher: Callable[[str, str, int, int], list[dict]] = fetch_range,
) -> int:
    """确保 [start_iso, end_iso] 内 ohlc 表全覆盖；返回新增/更新的 bar 数。

    算法：
      1. 查 DB 中该范围已有 open_time 集合
      2. 按 interval 步长枚举期望的 open_time 集合
      3. diff 出 missing；按连续段分块
      4. 每块调 fetcher 拉补；UPSERT 进 ohlc
    """
    interval_sec = INTERVAL_SECONDS[interval]
    step_ms = interval_sec * 1000
    start_ts = _iso_to_ts_ms(start_iso)
    end_ts = _iso_to_ts_ms(end_iso)

    existing_iso_rows = session.exec(
        select(OHLC.open_time).where(
            OHLC.symbol == symbol,
            OHLC.interval == interval,
            OHLC.open_time >= start_iso,
            OHLC.open_time <= end_iso,
        )
    ).all()
    existing_ts = {_iso_to_ts_ms(t) for t in existing_iso_rows}

    aligned_start = (start_ts // step_ms) * step_ms
    expected = set(range(aligned_start, end_ts + 1, step_ms))
    missing = sorted(expected - existing_ts)
    if not missing:
        return 0

    # 按连续区段分块（连续 = 相邻差恰为一个 step）
    chunks: list[tuple[int, int]] = []
    chunk_start = missing[0]
    prev = missing[0]
    for ts in missing[1:]:
        if ts - prev > step_ms:
            chunks.append((chunk_start, prev))
            chunk_start = ts
        prev = ts
    chunks.append((chunk_start, prev))

    upserted = 0
    for c_start, c_end in chunks:
        rows = fetcher(symbol, interval, c_start, c_end)
        for row in rows:
            existing = session.get(OHLC, (symbol, interval, row["open_time"]))
            if existing is None:
                session.add(OHLC(symbol=symbol, interval=interval, **row))
            else:
                for k, v in row.items():
                    if k != "open_time":
                        setattr(existing, k, v)
                session.add(existing)
            upserted += 1
        session.commit()
    return upserted


def _iso_to_ts_ms(iso: str) -> int:
    """'2025-01-01T00:00:00Z' or '2025-01-01T00:00:00+00:00' → ms since epoch."""
    s = iso.replace("Z", "+00:00")
    return int(datetime.fromisoformat(s).timestamp() * 1000)
```

- [ ] **Step 4: 跑测试验证通过**

Run: `cd /mnt/d/培训/ai_lesson/lesson6/project && pytest tests/test_kline_fetcher.py -v && ruff check .`
Expected: 4 passed（empty / skips / all present / iso roundtrip），ruff 0。

- [ ] **Step 5: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/app/kline_fetcher.py lesson6/project/tests/test_kline_fetcher.py
git commit -m "quant-trader: v1.2 — kline_fetcher with paged fetch + ensure_range_in_db"
```

---

## Task 2: 扩 `app/backtest.py:load_ohlc` 支持 start/end + 加单测

**Files:**
- Modify: `lesson6/project/app/backtest.py:load_ohlc` 和 `run_backtest`（增 keyword-only 参数）
- Modify: `lesson6/project/tests/test_backtest.py`（加 1 测）

- [ ] **Step 1: 加失败测试到 `tests/test_backtest.py` 末尾**

```python
def test_load_ohlc_by_range(db_with_ohlc):
    from app.backtest import load_ohlc
    # ohlc_fixture 第 0 根是 2025-01-01T00:00:00Z，hourly 200 根
    df = load_ohlc(
        "BTCUSDT", "1h", engine=db_with_ohlc,
        start_time="2025-01-01T01:00:00Z",
        end_time="2025-01-01T03:00:00Z",
    )
    # 范围内 3 根：01/02/03
    assert len(df) == 3
    times = [t.strftime("%Y-%m-%dT%H:%M:%SZ") for t in df.index]
    assert times == ["2025-01-01T01:00:00Z", "2025-01-01T02:00:00Z", "2025-01-01T03:00:00Z"]


def test_load_ohlc_range_overrides_limit(db_with_ohlc):
    from app.backtest import load_ohlc
    # 同时给 limit 和 range：以 range 为准
    df = load_ohlc(
        "BTCUSDT", "1h", limit=999, engine=db_with_ohlc,
        start_time="2025-01-01T00:00:00Z",
        end_time="2025-01-01T01:00:00Z",
    )
    assert len(df) == 2  # 00 和 01 两根，不是 999
```

- [ ] **Step 2: 跑测试验证它失败**

Run: `cd /mnt/d/培训/ai_lesson/lesson6/project && pytest tests/test_backtest.py::test_load_ohlc_by_range tests/test_backtest.py::test_load_ohlc_range_overrides_limit -v`
Expected: TypeError（load_ohlc 不接受 start_time）。

- [ ] **Step 3: 改 `app/backtest.py:load_ohlc`**

定位现有的 `load_ohlc` 函数，整体替换为：

```python
def load_ohlc(
    symbol: str,
    interval: str,
    limit: int | None = None,
    engine: Engine | None = None,
    *,
    start_time: str | None = None,
    end_time: str | None = None,
) -> pd.DataFrame:
    """读 ohlc。

    两种模式：
    - 范围模式：start_time + end_time 都非空 → WHERE open_time BETWEEN ... AND ...
    - 行数模式：否则用 LIMIT N DESC，limit 必须非空
    优先级：范围模式 > 行数模式（同时提供时 limit 被忽略）
    """
    eng = engine or default_engine
    if start_time and end_time:
        query = text(
            "SELECT open_time, open, high, low, close, volume "
            "FROM ohlc WHERE symbol = :symbol AND interval = :interval "
            "AND open_time >= :start AND open_time <= :end "
            "ORDER BY open_time ASC"
        )
        sql_params = {"symbol": symbol, "interval": interval,
                      "start": start_time, "end": end_time}
    else:
        if limit is None:
            raise ValueError("load_ohlc 需要 limit 或 start_time+end_time")
        query = text(
            "SELECT open_time, open, high, low, close, volume "
            "FROM ohlc WHERE symbol = :symbol AND interval = :interval "
            "ORDER BY open_time DESC LIMIT :limit"
        )
        sql_params = {"symbol": symbol, "interval": interval, "limit": limit}

    with eng.connect() as conn:
        df = pd.read_sql_query(query, conn, params=sql_params)
    if df.empty:
        raise ValueError(
            f"ohlc 表里没有 {symbol} {interval} 在所选范围内的数据；"
            f"先跑 scripts/seed_db.py 或在 backtest 表单填合理的范围"
        )
    df["open_time"] = pd.to_datetime(df["open_time"], utc=True)
    df = df.set_index("open_time").sort_index()
    return df
```

(关键差异：`limit` 改为 `int | None = None`；增 keyword-only `start_time`/`end_time`；分两个 SQL 分支；range 模式直接 ORDER BY ASC 省去后续 sort_index 但保留 sort_index 以保险。)

- [ ] **Step 4: 改 `app/backtest.py:run_backtest` 透传新参数**

定位 `run_backtest` 签名，替换为：

```python
def run_backtest(
    strategy: Callable[..., pd.Series],
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int | None = 30,
    out_dir: Path | None = None,
    engine: Engine | None = None,
    *,
    start_time: str | None = None,
    end_time: str | None = None,
    **strategy_params,
) -> dict:
    """跑一次回测，把累计曲线写到 out_dir/cum_<symbol>_<interval>[_<dates>].png；返回结果 dict。"""
    df = load_ohlc(
        symbol, interval, limit=limit, engine=engine,
        start_time=start_time, end_time=end_time,
    )
    # ... 中间 signal / strategy_return / cumulative / 指标计算保持原样 ...
```

在 PNG 文件名构造的那一行（搜 `f"cum_{symbol}_{interval}.png"`）改为：

```python
    if start_time and end_time:
        # 用 YYYYMMDD-YYYYMMDD 形式避免文件名特殊字符
        s_short = start_time[:10].replace("-", "")
        e_short = end_time[:10].replace("-", "")
        png_path = out_dir / f"cum_{symbol}_{interval}_{s_short}_{e_short}.png"
    else:
        png_path = out_dir / f"cum_{symbol}_{interval}.png"
```

`run_backtest` 其余部分（图表绘制、指标计算、summary 生成）不动。

- [ ] **Step 5: 跑测试验证通过 + 整体不回归**

Run:
```bash
cd /mnt/d/培训/ai_lesson/lesson6/project
pytest -v && ruff check .
```
Expected: 51（之前）+ 2 新 = 53 passed + 2 skipped。Ruff 0。

- [ ] **Step 6: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/app/backtest.py lesson6/project/tests/test_backtest.py
git commit -m "quant-trader: v1.2 — load_ohlc + run_backtest 支持 start_time/end_time"
```

---

## Task 3: 路由 + 模板加 datetime-local 字段 + 1 集成测

**Files:**
- Modify: `lesson6/project/app/routes/backtest.py:backtest_run`
- Modify: `lesson6/project/app/templates/backtest.html`
- Modify: `lesson6/project/tests/test_routes_backtest.py`

- [ ] **Step 1: 加失败测试到 `tests/test_routes_backtest.py` 末尾**

```python
def test_post_backtest_with_range(monkeypatch, ohlc_fixture):
    """填了 start/end 走 range 模式；mock ensure_range_in_db 避免真网络。"""
    monkeypatch.setattr(
        "app.routes.backtest.ensure_range_in_db",
        lambda *a, **kw: 0,  # 假装数据已就绪
    )
    with TestClient(app) as client:
        r = client.post("/backtest", data={
            "strategy_name": "dual_ma",
            "symbol": "BTCUSDT",
            "interval": "1h",
            "limit": "100",  # 被 range 覆盖
            "params": "{}",
            "start_time": "2025-01-01T01:00",
            "end_time": "2025-01-01T03:00",
        })
        assert r.status_code == 200
        assert "夏普" in r.text or "Sharpe" in r.text


def test_post_backtest_range_too_large(monkeypatch):
    """估算 bar 数超过 200000 → 400 + 中文提示。"""
    with TestClient(app) as client:
        # 1m × 200 天 = 288000 bars，超过 200000
        r = client.post("/backtest", data={
            "strategy_name": "dual_ma",
            "symbol": "BTCUSDT",
            "interval": "1m",
            "limit": "100",
            "params": "{}",
            "start_time": "2024-01-01T00:00",
            "end_time": "2024-07-20T00:00",
        })
        assert r.status_code == 400
        assert "时间范围过大" in r.text


def test_post_backtest_start_after_end():
    with TestClient(app) as client:
        r = client.post("/backtest", data={
            "strategy_name": "dual_ma",
            "symbol": "BTCUSDT", "interval": "1h", "limit": "100", "params": "{}",
            "start_time": "2025-02-01T00:00",
            "end_time": "2025-01-01T00:00",
        })
        assert r.status_code == 400
        assert "起始时间不能晚于结束时间" in r.text
```

- [ ] **Step 2: 跑测试验证它失败**

Run: `cd /mnt/d/培训/ai_lesson/lesson6/project && pytest tests/test_routes_backtest.py -v`
Expected: 失败（路由还没接 start_time/end_time 字段）。

- [ ] **Step 3: 改 `app/routes/backtest.py`**

整体替换文件内容（在现有基础上加 import、加 helpers、扩 backtest_run）：

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
from sqlmodel import Session

from app.backtest import run_backtest
from app.db import get_engine
from app.kline_fetcher import INTERVAL_SECONDS, ensure_range_in_db
from app.strategies import STRATEGY_REGISTRY

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
_STATIC_DIR = Path("static")
_MAX_BARS = 200_000


def _normalize_datetime_local(s: str) -> str:
    """HTML5 datetime-local 是 'YYYY-MM-DDTHH:MM'（无 tz）。当 UTC 解释，补秒和 Z。"""
    if not s:
        return ""
    # 已经有秒就不再加
    if len(s) == 16:  # YYYY-MM-DDTHH:MM
        s = s + ":00"
    if not s.endswith("Z") and "+" not in s:
        s = s + "Z"
    return s


def _estimate_bars(interval: str, start_iso: str, end_iso: str) -> int:
    from app.kline_fetcher import _iso_to_ts_ms
    start_ms = _iso_to_ts_ms(start_iso)
    end_ms = _iso_to_ts_ms(end_iso)
    step_ms = INTERVAL_SECONDS[interval] * 1000
    return max(0, (end_ms - start_ms) // step_ms + 1)


@router.get("/backtest", response_class=HTMLResponse)
async def backtest_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "backtest.html",
        {"strategies": list(STRATEGY_REGISTRY.keys()), "result": None},
    )


@router.post("/backtest", response_class=HTMLResponse)
async def backtest_run(
    request: Request,
    strategy_name: str = Form(...),
    symbol: str = Form("BTCUSDT"),
    interval: str = Form("1h"),
    limit: int = Form(100),
    params: str = Form("{}"),
    start_time: str = Form(""),
    end_time: str = Form(""),
    engine: Engine = Depends(get_engine),  # noqa: B008
) -> HTMLResponse:
    entry = STRATEGY_REGISTRY.get(strategy_name)
    if entry is None:
        return HTMLResponse(f"unknown strategy: {strategy_name}", status_code=400)

    try:
        parsed = {**entry.defaults, **json.loads(params or "{}")}
    except json.JSONDecodeError:
        return HTMLResponse("参数 JSON 解析失败", status_code=400)

    use_range = bool(start_time and end_time)
    start_iso = end_iso = None
    if use_range:
        start_iso = _normalize_datetime_local(start_time)
        end_iso = _normalize_datetime_local(end_time)
        if start_iso >= end_iso:
            return HTMLResponse("起始时间不能晚于结束时间", status_code=400)
        bars = _estimate_bars(interval, start_iso, end_iso)
        if bars > _MAX_BARS:
            return HTMLResponse(
                f"时间范围过大（约 {bars} 根 K 线），最多支持 {_MAX_BARS} 根，请收窄",
                status_code=400,
            )
        with Session(engine) as s:
            ensure_range_in_db(s, symbol, interval, start_iso, end_iso)

    try:
        result = run_backtest(
            entry.fn, symbol=symbol, interval=interval,
            limit=None if use_range else limit,
            out_dir=_STATIC_DIR, engine=engine,
            start_time=start_iso, end_time=end_iso,
            **parsed,
        )
    except ValueError as e:
        return HTMLResponse(str(e), status_code=400)

    png_path = Path(result["png_path"])
    static_png = _STATIC_DIR / png_path.name
    if png_path.resolve() != static_png.resolve():
        shutil.copy(png_path, static_png)
    result["png_name"] = png_path.name

    return templates.TemplateResponse(
        request,
        "backtest.html",
        {
            "strategies": list(STRATEGY_REGISTRY.keys()),
            "result": result,
            "request_strategy": strategy_name,
            "request_symbol": symbol,
            "request_interval": interval,
            "request_limit": limit,
            "request_params": params,
            "request_start_time": start_time,
            "request_end_time": end_time,
        },
    )
```

- [ ] **Step 4: 改 `app/templates/backtest.html` 表单加 2 个 datetime-local 字段**

定位 form 内的 `<label>行数...</label>` 后面，**在「参数 JSON」label 之前**插入 2 个新 label：

```html
    <label>起始时间 <span class="muted" style="font-weight:400;font-size:11px;">(UTC，可空)</span>
      <input name="start_time" type="datetime-local" value="{{ request_start_time or '' }}">
    </label>
    <label>结束时间 <span class="muted" style="font-weight:400;font-size:11px;">(UTC，可空)</span>
      <input name="end_time" type="datetime-local" value="{{ request_end_time or '' }}">
    </label>
```

并把表单顶部 `<p class="muted">` 那一段稍作补充（增一行 hint），整体替换为：

```html
<h1>回测</h1>
<p class="muted">基于历史 K 线一次性回放策略，输出夏普 / 最大回撤 / 胜率 / 累计收益 + 累计曲线。
  填了起止时间会走「时间段」模式（缺数据时自动从 Binance 拉补，最多 200000 根）；否则按上面的「行数」回放最近 N 根。</p>
```

- [ ] **Step 5: 跑测试 + 全套测试**

Run:
```bash
cd /mnt/d/培训/ai_lesson/lesson6/project
pytest -v && ruff check .
```
Expected: 53 + 3 = 56 + 2 skipped。Ruff 0。

注：`test_post_backtest_with_range` 走 range 模式 + monkeypatch 后调 `run_backtest(start_time=..., end_time=...)`，需要 ohlc_fixture 通过 `test_routes_backtest.py` 自身的 `_setup_db` autouse fixture 注入 OHLC（已有，不需改）。范围 `2025-01-01T01:00..03:00` 在 fixture 200 hourly bars 内，能查到数据。

- [ ] **Step 6: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/app/routes/backtest.py \
              lesson6/project/app/templates/backtest.html \
              lesson6/project/tests/test_routes_backtest.py
git commit -m "quant-trader: v1.2 — /backtest UI + route 支持自定义时间段（自动补数据）"
```

---

## Self-Review Checklist

- [ ] Spec §3 UI 加 datetime-local + hint → Task 3 Step 4
- [ ] Spec §4 路由 estimate + 护栏 + ensure_range_in_db 调用 → Task 3 Step 3
- [ ] Spec §5 load_ohlc/run_backtest 新签名 + range PNG 文件名 → Task 2 Steps 3-4
- [ ] Spec §6 kline_fetcher 模块（INTERVAL_SECONDS + fetch_range + ensure_range_in_db + _iso_to_ts_ms） → Task 1 Step 3
- [ ] Spec §7 测试：load_ohlc 范围 / ensure_range_in_db 3 case / route range POST → Tasks 1+2+3
- [ ] Spec §8 边界：start>end / 超护栏 / Binance 失败（透 ValueError）→ Task 3 路由分支 + 测试
- [ ] 无 TBD / TODO
- [ ] 类型一致性：`ensure_range_in_db` 签名（session, symbol, interval, start_iso, end_iso, fetcher）各处一致；`load_ohlc` 新签名在 backtest.py 内的 run_backtest 调用处也用关键字传 start_time/end_time
- [ ] 每个 task 末尾都有 commit
- [ ] 测试覆盖率不下降（新代码都有对应测试）

---

## 执行说明

- **顺序**：Task 1 → 2 → 3 必须按序（2 依赖 1 不写；3 依赖 1 和 2 都写完）。
- **每个 task 完成后**：跑一次 `pytest -v && ruff check .` 保险。
- **uvicorn 后台仍在跑**（pid `bn2lfm9em` from v1.1 收尾）；改完 routes/template 后浏览器 Ctrl+Shift+R 强刷或 `pkill -f "uvicorn app.main:app" && nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/uvicorn.log 2>&1 &` 重启。
- **手测**：Task 3 完成后打开 `/backtest`，填一段 1d 的范围（如 2024-01-01 ~ 2025-01-01），首次 1-3 秒拉数据，看曲线；同范围再点一次秒返。
