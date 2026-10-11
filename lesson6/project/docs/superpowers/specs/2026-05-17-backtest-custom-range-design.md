# Backtest Custom Time Range — Design

**Date:** 2026-05-17
**Status:** Approved for implementation planning
**Scope:** quant-trader v1.2（v1.1 UI polish 之后的增量）
**Authors:** locey + Claude (via superpowers:brainstorming)

---

## 1. Purpose

`/backtest` 当前只能用「最近 N 根 K 线」选范围；用户希望能填**任意起止时间**。同时若所选范围超出 DB 现有数据，**自动从 Binance public REST 拉补**，让用户无感。

## 2. Scope

### In scope
- 表单加 `start_time` + `end_time` 两个 `datetime-local` 字段；两个都填 → 走时间段模式；否则保留现有「行数 N」模式（向后兼容）
- `app/backtest.py:load_ohlc` 加 `start_time` / `end_time` 关键字参数
- 新模块 `app/kline_fetcher.py`：抽出 Binance kline 拉取 + UPSERT 的可复用底层；`KlineSource` 不变（沿用旧路径）
- 新 helper `ensure_range_in_db(session, symbol, interval, start, end)`：计算 missing chunks → 分页拉 → UPSERT
- `routes/backtest.py:backtest_run` 调用顺序变为：parse 范围 → 算 bar 数估算 → 护栏（≤ 200000）→ ensure_range_in_db → run_backtest
- 护栏：单次估算 bar 数超过 **200000** → 返回 400 + 中文友好提示「时间范围过大（约 X 根 K 线），最多支持 200000 根，请收窄」
- 测试：单测 `load_ohlc` 范围模式、`ensure_range_in_db` 分页/UPSERT 行为；集成测覆盖 POST /backtest with start/end（mock fetcher 避网络）

### Out of scope（v2 / 后续）
- 后台异步拉取 + 进度条（v1.2 同步拉，最长 ~40s 用户等）
- 拉补失败的部分重试 / 断点续传
- 多用户并发请求同一范围的去重（v1 单用户）
- WebSocket 流式更新结果
- `bot_runner` / `kline_source` 也用新 `ensure_range_in_db`（v1.2 只服务 backtest）

## 3. UI 改动

`app/templates/backtest.html` 表单加两个字段（位置：现有「行数」之后，「参数 JSON」之前）：

```
起始时间   [_____ datetime-local input _____]
结束时间   [_____ datetime-local input _____]
                                 ↑ 两个都填则走范围模式；否则用上面的「行数」
```

加一行小字 hint：`(留空则按「行数」回放最近 N 根)`

## 4. 路由 / 数据流

`routes/backtest.py:backtest_run` 新签名：

```python
async def backtest_run(
    ...
    limit: int = Form(100),
    params: str = Form("{}"),
    start_time: str = Form(""),
    end_time: str = Form(""),
    engine: Engine = Depends(get_engine),
) -> HTMLResponse:
    ...
    use_range = bool(start_time and end_time)
    if use_range:
        start_iso, end_iso = _parse_datetime_local(start_time, end_time)  # 转 UTC ISO
        bars_estimate = _estimate_bars(interval, start_iso, end_iso)
        if bars_estimate > 200_000:
            return HTMLResponse(f"时间范围过大（约 {bars_estimate} 根 K 线），最多支持 200000 根，请收窄", 400)
        with Session(engine) as s:
            ensure_range_in_db(s, symbol, interval, start_iso, end_iso)
        result = run_backtest(
            entry.fn, symbol=symbol, interval=interval,
            start_time=start_iso, end_time=end_iso,
            out_dir=_STATIC_DIR, engine=engine, **parsed,
        )
    else:
        result = run_backtest(entry.fn, symbol=symbol, interval=interval, limit=limit, ...)
```

辅助：
- `_parse_datetime_local(s) -> str`：HTML5 `datetime-local` 是无时区的 `YYYY-MM-DDTHH:MM` 字符串；我们当作 UTC 解释，转成 `YYYY-MM-DDTHH:MM:00Z`
- `_estimate_bars(interval, start_iso, end_iso) -> int`：按 `INTERVAL_SECONDS[interval]`（来自 `app/kline_fetcher.py`）做整除估算

## 5. `app/backtest.py` 改动

`load_ohlc` 增加 keyword-only 参数：

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
    - 提供 start_time + end_time → WHERE open_time BETWEEN ... AND ...（按时间升序）
    - 否则 → ORDER BY open_time DESC LIMIT limit
    两组参数互斥；同时提供时优先 range，limit 忽略
    """
```

`run_backtest` 透传：增 `start_time` / `end_time` 参数，转发给 `load_ohlc`。`limit` 仍兼容。

PNG 文件名：range 模式下用 `cum_{symbol}_{interval}_{start_date}_{end_date}.png`，避免覆盖 limit 模式产物。

`TRADING_PERIODS` 计算 Sharpe 年化不受影响（按 interval 决定）。

## 6. `app/kline_fetcher.py`（新模块）

抽出 Binance kline 拉取的可复用底层。**复用** `kline_source.py:_binance_fetch` 现有的 URL + 错误处理风格。

```python
"""Binance kline 分页拉取 + UPSERT 进 ohlc 表的可复用底层。"""

from __future__ import annotations

from datetime import datetime, timezone

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
    """Binance public klines 按 1000-bar 分页，覆盖 [start, end] 区间。
    返回 list of {open_time, open, high, low, close, volume}。
    """
    rows: list[dict] = []
    cursor = start_ts_ms
    interval_ms = INTERVAL_SECONDS[interval] * 1000
    while cursor <= end_ts_ms:
        resp = httpx.get(
            f"{BINANCE_BASE}/api/v3/klines",
            params={"symbol": symbol, "interval": interval,
                    "startTime": cursor, "endTime": end_ts_ms, "limit": 1000},
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        for r in batch:
            ts = datetime.fromtimestamp(int(r[0]) / 1000, tz=timezone.utc)
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
    session: Session, symbol: str, interval: str,
    start_iso: str, end_iso: str,
    fetcher=fetch_range,
) -> int:
    """确保 ohlc 表里覆盖 [start, end]。返回新增/更新的 bar 数。

    实现：先把 [start, end] 内已有 open_time 集合查出来；按 interval 步长枚举期望的
    open_time 集合；diff 出 missing；分块（连续的 missing）调 fetcher 拉补；UPSERT。
    fetcher 参数留出来便于测试注入 stub。
    """
    interval_sec = INTERVAL_SECONDS[interval]
    start_ts = _iso_to_ts_ms(start_iso)
    end_ts = _iso_to_ts_ms(end_iso)

    # 已有的 open_time（ms）
    existing_iso = set(session.exec(
        select(OHLC.open_time)
        .where(OHLC.symbol == symbol, OHLC.interval == interval,
               OHLC.open_time >= start_iso, OHLC.open_time <= end_iso)
    ).all())
    existing_ts = {_iso_to_ts_ms(t) for t in existing_iso}

    # 期望的 open_time（Binance 的 open_time 都对齐到 interval 边界）
    aligned_start = (start_ts // (interval_sec * 1000)) * (interval_sec * 1000)
    expected = set(range(aligned_start, end_ts + 1, interval_sec * 1000))
    missing = sorted(expected - existing_ts)
    if not missing:
        return 0

    # 把 missing 按连续区段分组
    chunks: list[tuple[int, int]] = []
    chunk_start = missing[0]
    prev = missing[0]
    step_ms = interval_sec * 1000
    for ts in missing[1:]:
        if ts - prev > step_ms:
            chunks.append((chunk_start, prev))
            chunk_start = ts
        prev = ts
    chunks.append((chunk_start, prev))

    upserted = 0
    for chunk_start_ms, chunk_end_ms in chunks:
        rows = fetcher(symbol, interval, chunk_start_ms, chunk_end_ms)
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
    # 兼容 "2025-01-01T00:00:00Z" / "2025-01-01T00:00Z" 形式
    s = iso.replace("Z", "+00:00")
    return int(datetime.fromisoformat(s).timestamp() * 1000)
```

## 7. 测试

### `tests/test_backtest.py` 加 1 个测试

```python
def test_load_ohlc_by_range(db_with_ohlc):
    df = load_ohlc("BTCUSDT", "1h", engine=db_with_ohlc,
                   start_time="2025-01-01T00:00:00Z",
                   end_time="2025-01-01T05:00:00Z")
    assert all("2025-01-01T00:00:00Z" <= t.strftime("%Y-%m-%dT%H:%M:%SZ") <= "2025-01-01T05:00:00Z"
               for t in df.index)
```

（注：ohlc_fixture 用 freq="1h" 从 2025-01-01 开始，所以范围测试用这些时间是有数据的。）

### `tests/test_kline_fetcher.py`（新文件）

3 个测试：
1. `test_ensure_range_with_empty_db`：DB 全空时，stub fetcher 返回 5 条 → 5 条都进库
2. `test_ensure_range_skips_existing`：DB 已有部分 bar，再调一次 → 只拉缺的；fetcher 调用次数符合预期
3. `test_ensure_range_all_present`：DB 完整覆盖范围 → fetcher 不被调用，返回 0

### `tests/test_routes_backtest.py` 加 1 个测试

```python
def test_post_backtest_with_range(monkeypatch):
    # mock ensure_range_in_db 避免真的网络调用
    monkeypatch.setattr("app.routes.backtest.ensure_range_in_db", lambda *a, **kw: 0)
    with TestClient(app) as client:
        r = client.post("/backtest", data={
            "strategy_name": "dual_ma", "symbol": "BTCUSDT", "interval": "1h",
            "limit": "100",  # 即使填了 limit，range 模式会覆盖
            "params": "{}",
            "start_time": "2025-01-01T00:00",
            "end_time": "2025-01-01T05:00",
        })
        assert r.status_code in {200, 400}  # 200 即数据齐；400 即数据缺
        # 这个 test 主要验路由不崩；具体行为由 ensure_range_in_db 测试覆盖
```

## 8. 异常 / 边界

- 用户填 `start > end` → 400 + "起始时间不能晚于结束时间"
- 估算 bar 超过 200000 → 400 + 友好提示（见 §4）
- Binance 网络失败 → 现有 `httpx.HTTPError` 冒泡到 `routes/backtest.py` 已有的 try/except → 返回 400 + 错误文本
- 用户填了 start 但没填 end（或反之）→ 视为「未启用范围模式」，按 limit 走（向后兼容）
- 用户填的范围远早于 Binance 该 symbol 的上线时间 → Binance 返回空数组 → `ensure_range_in_db` 拉不到东西 → load_ohlc 取到 0 行 → `run_backtest` 抛已有的 `ValueError("ohlc 表里没有...")` → 400

## 9. 验收

- `pytest -v && ruff check .` 51 + 4 = 55 + 2 skipped pass
- coverage 不低于 80%
- 浏览器测：填一个跨年的 1h 范围（如 2025-01-01 到 2025-02-01），首次约 1-3 秒拉数据，看到结果；再跑同一范围秒返
- 估算超 200000 时返回友好中文提示，不是 500

## 10. 已知 v2 backlog

- 同步拉取最长 ~40s 可能让用户以为页面卡死 → v2 加 progress UI（HTMX SSE / 后台 task + 轮询）
- `bot_runner` 触发 tick 时也应该用 `ensure_range_in_db`（v1.2 还是用 KlineSource 老接口；OK 因为 bot 只关心最新一根）
- 拉补失败（局部超时 / 个别 chunk 报错）的部分重试 → v2 加重试 + 标记 failed chunks
- 同一范围并发请求去重（v1 单用户无并发问题）

---

**Approved by**: locey, 2026-05-17
**Next step**: superpowers:writing-plans → 产出 3 个 task 的 plan
