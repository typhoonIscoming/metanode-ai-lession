# UI Polish (中文化 + 现代卡片风) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 quant-trader v1 的 5 个 Web 页面升级成全中文、现代卡片风（白底 / 蓝主色 / 红涨绿跌），Bot 详情页加入 equity 曲线 PNG。

**Architecture:** 纯前端 + 1 个路由扩展。`static/style.css` 重写为分段 utility CSS（~150 行）；5 个模板按设计稿改写；`app/routes/bots.py:bot_detail` 多查 `pnl_snapshots` 并通过新私有 helper `_render_equity_png` 写 PNG 到 `static/`；`app/strategies/registry.py` 增 `STRATEGY_DESCRIPTIONS` 字典。零业务/schema 改动。

**Tech Stack:** Jinja2 + HTMX 1.9.10（不变）；matplotlib Agg（复用现有 backtest 模式）；FastAPI TestClient（测试）。

---

## File Structure

| 文件 | 改动类型 | 责任 |
|---|---|---|
| `static/style.css` | **重写**（20→~150 行） | 全部样式 utility classes |
| `app/templates/base.html` | 重写 | 顶栏 + 品牌 + 中文 nav |
| `app/templates/bots_list.html` | 重写 | 机器人卡片网格 + 中文新建表单 |
| `app/templates/partials/bots_table.html` | 重写 | 机器人卡片 partial（HTMX 5s 刷新目标）|
| `app/templates/partials/bot_status.html` | 重写 | 状态徽章组件 |
| `app/templates/bot_detail.html` | 重写 | 顶部 + 资金概要卡片 + equity 曲线 + 两栏成交/tick |
| `app/templates/backtest.html` | 重写 | 中文表单 + 4 张大数字卡 + 曲线 |
| `app/templates/strategies.html` | 重写 | 策略卡片网格 |
| `app/strategies/registry.py` | 修改（+1 dict） | 加 `STRATEGY_DESCRIPTIONS` |
| `app/routes/bots.py` | 修改（bot_detail + new helper） | 拉 pnl_snapshots、画 equity PNG |
| `app/routes/strategies.py` | 修改（pass descriptions） | 传 `STRATEGY_DESCRIPTIONS` 给模板 |
| `tests/test_routes_bots.py` | 修改（中文断言）+ 新增 equity 测试 | 适配新 UI 字符串 + 验 equity section |

---

## Task 1: 重写 `static/style.css` + 改 `base.html` 顶栏

**Files:**
- Modify: `lesson6/project/static/style.css`（整体重写）
- Modify: `lesson6/project/app/templates/base.html`（整体重写）

- [ ] **Step 1: 重写 `static/style.css`**

整体替换为：

```css
/* 1. Reset + 全局排版 */
*, *::before, *::after { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                 "Microsoft YaHei", Roboto, sans-serif;
    background: #f5f6fa;
    color: #1f2937;
    line-height: 1.5;
    font-size: 14px;
}
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }
h1 { font-size: 24px; font-weight: 600; margin: 0 0 16px; }
h2 { font-size: 18px; font-weight: 600; margin: 0 0 12px; color: #1f2937; }
p { margin: 0 0 12px; }

/* 2. Layout */
header.topbar {
    background: #fff;
    border-bottom: 1px solid #e5e7eb;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    gap: 24px;
}
header.topbar .brand { font-weight: 700; font-size: 16px; color: #1f2937; }
header.topbar .brand small { font-weight: 400; color: #64748b; margin-left: 8px; }
header.topbar nav { display: flex; gap: 20px; }
header.topbar nav a {
    color: #475569; font-weight: 500;
    padding: 4px 0; border-bottom: 2px solid transparent;
}
header.topbar nav a:hover { color: #2563eb; text-decoration: none; border-bottom-color: #2563eb; }
main { max-width: 1200px; margin: 0 auto; padding: 24px; }

/* 3. Card + section */
.card {
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(15,23,42,.04), 0 1px 2px rgba(15,23,42,.06);
    padding: 20px;
    margin-bottom: 16px;
}
.section { margin-bottom: 24px; }
.section-title { font-size: 13px; font-weight: 600; color: #64748b;
                 text-transform: uppercase; letter-spacing: .04em; margin-bottom: 8px; }

/* 4. Form */
form.stack { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
form label { display: flex; flex-direction: column; font-size: 13px; color: #475569; gap: 4px; }
form input, form select, form textarea {
    padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px;
    font-size: 14px; background: #fff; font-family: inherit;
}
form input:focus, form select:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,.15); }
button, .btn {
    padding: 8px 16px; border-radius: 8px; border: 0; cursor: pointer;
    font-size: 14px; font-weight: 500; background: #2563eb; color: #fff;
}
button:hover, .btn:hover { background: #1d4ed8; }
button.secondary { background: #fff; color: #475569; border: 1px solid #cbd5e1; }
button.secondary:hover { background: #f1f5f9; border-color: #94a3b8; }
button.danger { background: #fff; color: #dc2626; border: 1px solid #fecaca; }
button.danger:hover { background: #fef2f2; }
details > summary {
    cursor: pointer; padding: 12px 16px; background: #fff; border-radius: 12px;
    box-shadow: 0 1px 3px rgba(15,23,42,.04);
    list-style: none; font-weight: 500;
}
details > summary::before { content: "+ "; color: #2563eb; font-weight: 700; }
details[open] > summary::before { content: "- "; }
details[open] > .card { margin-top: 8px; }

/* 5. Table */
table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #f1f5f9; font-size: 13px; }
th { background: #f8fafc; color: #64748b; font-weight: 500; font-size: 12px;
     text-transform: uppercase; letter-spacing: .03em; }
tr:last-child td { border-bottom: 0; }
tr:hover { background: #fafbfc; }

/* 6. Badge + status */
.badge {
    display: inline-block; padding: 2px 10px; border-radius: 999px;
    font-size: 12px; font-weight: 500; line-height: 1.6;
    background: #f1f5f9; color: #475569;
}
.badge.status-running { background: #dbeafe; color: #1d4ed8; }
.badge.status-stopped { background: #f1f5f9; color: #64748b; }
.badge.status-errored { background: #ffedd5; color: #c2410c; }
.badge.status-deleted { background: #e2e8f0; color: #94a3b8; }
.badge.status-success { background: #dbeafe; color: #1d4ed8; }
.badge.status-skipped { background: #f1f5f9; color: #64748b; }

/* 7. Metric cards */
.metrics { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); margin-bottom: 16px; }
.metric {
    background: #fff; padding: 16px 20px; border-radius: 12px;
    box-shadow: 0 1px 3px rgba(15,23,42,.04);
}
.metric .label { font-size: 12px; color: #64748b; margin-bottom: 8px;
                 text-transform: uppercase; letter-spacing: .03em; }
.metric .value { font-size: 24px; font-weight: 600; color: #1f2937;
                 font-family: ui-monospace, "SF Mono", Consolas, monospace; }
.metric .sub { font-size: 12px; margin-top: 4px; }

/* 8. Empty state */
.empty {
    text-align: center; padding: 48px 24px; color: #94a3b8;
    background: #fff; border-radius: 12px; border: 1px dashed #e2e8f0;
}
.empty .emoji { font-size: 32px; margin-bottom: 12px; }
.empty .hint { font-size: 13px; }

/* 9. Helpers */
.muted { color: #94a3b8; }
.numeric { font-family: ui-monospace, "SF Mono", Consolas, monospace; }
.pnl-up { color: #dc2626; }     /* 中国惯例：红涨 */
.pnl-down { color: #16a34a; }   /* 中国惯例：绿跌 */
.row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.row.justify-between { justify-content: space-between; }
.grid-2 { display: grid; gap: 16px; grid-template-columns: 1fr 1fr; }
@media (max-width: 700px) { .grid-2 { grid-template-columns: 1fr; } }
.actions { display: flex; gap: 8px; }
img.chart { width: 100%; height: auto; border-radius: 8px; }
```

- [ ] **Step 2: 重写 `app/templates/base.html`**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}QuantTrader{% endblock %}</title>
  <link rel="stylesheet" href="/static/style.css">
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>
<body>
  <header class="topbar">
    <div class="brand">QuantTrader<small>量化交易实验台</small></div>
    <nav>
      <a href="/bots">机器人</a>
      <a href="/backtest">回测</a>
      <a href="/strategies">策略库</a>
    </nav>
  </header>
  <main>
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

- [ ] **Step 3: 验证页面不崩 + 跑测试**

Run:
```bash
cd /mnt/d/培训/ai_lesson/lesson6/project
pytest -v && ruff check .
```
Expected: 既有测试可能 fail（因为页面上 "No bots" / "form" 这种英文断言可能仍中标，但新中文 nav 不影响）。如果只是少量 fail，记下来留给后续 task 修；如果一片 fail，停下来报告。

- [ ] **Step 4: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/static/style.css lesson6/project/app/templates/base.html
git commit -m "quant-trader: ui v1.1 — rewrite style.css and base.html (中文 nav + brand)"
```

---

## Task 2: `STRATEGY_DESCRIPTIONS` + `/strategies` 页面

**Files:**
- Modify: `lesson6/project/app/strategies/registry.py`（加字典）
- Modify: `lesson6/project/app/routes/strategies.py`（传新数据）
- Modify: `lesson6/project/app/templates/strategies.html`（卡片网格）

- [ ] **Step 1: 在 `app/strategies/registry.py` 末尾追加**

定位文件末尾，追加：

```python


STRATEGY_DESCRIPTIONS: dict[str, str] = {
    "dual_ma":   "双均线交叉：短均线上穿长均线时做多，下穿时清仓。趋势跟随。",
    "rsi":       "RSI 反转：相对强弱指数跌破超卖线做多，涨破超买线清仓。均值回归。",
    "macd":      "MACD 金叉：MACD 线上穿信号线做多，下穿清仓。中期趋势确认。",
    "bollinger": "布林带均值回归：收盘价跌破下轨做多，回到中轨清仓。震荡市策略。",
}
```

- [ ] **Step 2: 改 `app/routes/strategies.py`**

整体替换为：

```python
"""/strategies 列表页。"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.strategies import STRATEGY_REGISTRY
from app.strategies.registry import STRATEGY_DESCRIPTIONS

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/strategies", response_class=HTMLResponse)
async def strategies_list(request: Request) -> HTMLResponse:
    items = [
        {
            "name": name,
            "defaults": entry.defaults,
            "description": STRATEGY_DESCRIPTIONS.get(name, ""),
        }
        for name, entry in STRATEGY_REGISTRY.items()
    ]
    return templates.TemplateResponse(
        request,
        "strategies.html",
        {"strategies": items},
    )
```

- [ ] **Step 3: 整体重写 `app/templates/strategies.html`**

```html
{% extends "base.html" %}
{% block title %}策略库 — QuantTrader{% endblock %}
{% block content %}
<h1>策略库</h1>
<p class="muted">当前内置 {{ strategies|length }} 个策略。所有策略统一签名 <code>strategy(df, **params) -> Series ∈ {-1, 0, +1}</code>。</p>

<div class="metrics">
  {% for s in strategies %}
  <div class="metric">
    <div class="label">{{ s.name }}</div>
    <div class="value" style="font-size: 14px; font-family: inherit; font-weight: 500; color: #1f2937; line-height: 1.5;">
      {{ s.description }}
    </div>
    <div class="sub muted">默认参数：</div>
    <table style="margin-top: 6px;">
      <tbody>
        {% for k, v in s.defaults.items() %}
        <tr><td style="color: #64748b;">{{ k }}</td><td class="numeric">{{ v }}</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endfor %}
</div>
{% endblock %}
```

- [ ] **Step 4: 验证 `/strategies` 仍能渲染所有 4 个策略名**

Run:
```bash
cd /mnt/d/培训/ai_lesson/lesson6/project
pytest tests/test_routes_bots.py::test_strategies_page_lists_four -v
```
Expected: PASS（4 个策略名 dual_ma/rsi/macd/bollinger 仍在响应里）。

- [ ] **Step 5: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/app/strategies/registry.py \
              lesson6/project/app/routes/strategies.py \
              lesson6/project/app/templates/strategies.html
git commit -m "quant-trader: ui v1.1 — /strategies card grid + 中文描述"
```

---

## Task 3: 重写 `/backtest` 页面（中文表单 + 大数字结果卡）

**Files:**
- Modify: `lesson6/project/app/templates/backtest.html`（整体重写）

- [ ] **Step 1: 整体重写 `app/templates/backtest.html`**

```html
{% extends "base.html" %}
{% block title %}回测 — QuantTrader{% endblock %}
{% block content %}
<h1>回测</h1>
<p class="muted">基于历史 K 线一次性回放策略，输出夏普 / 最大回撤 / 胜率 / 累计收益 + 累计曲线。</p>

<div class="card">
  <form class="stack" method="post" action="/backtest">
    <label>策略
      <select name="strategy_name">
        {% for name in strategies %}
        <option value="{{ name }}" {% if request_strategy == name %}selected{% endif %}>{{ name }}</option>
        {% endfor %}
      </select>
    </label>
    <label>交易对
      <input name="symbol" value="{{ request_symbol or 'BTCUSDT' }}">
    </label>
    <label>周期
      <select name="interval">
        {% for iv in ["1m", "5m", "15m", "1h", "1d"] %}
        <option value="{{ iv }}" {% if request_interval == iv %}selected{% endif %}>{{ iv }}</option>
        {% endfor %}
      </select>
    </label>
    <label>行数（最近 N 根 K 线）
      <input name="limit" type="number" value="{{ request_limit or 100 }}">
    </label>
    <label>参数 JSON（留空用默认值）
      <input name="params" value='{{ request_params or "{}" }}'>
    </label>
    <label>&nbsp;
      <button type="submit">开始回测</button>
    </label>
  </form>
</div>

{% if result %}
<h2 style="margin-top: 24px;">回测结果</h2>
<div class="metrics">
  <div class="metric">
    <div class="label">年化夏普</div>
    <div class="value {% if result.sharpe >= 1 %}pnl-up{% elif result.sharpe < 0 %}pnl-down{% endif %}">
      {{ "%.2f"|format(result.sharpe) }}
    </div>
    <div class="sub muted">{% if result.sharpe >= 1 %}风险调整后收益尚可{% else %}相对持有无显著优势{% endif %}</div>
  </div>
  <div class="metric">
    <div class="label">最大回撤</div>
    <div class="value pnl-down">{{ "%.2f%%"|format(result.max_drawdown * 100) }}</div>
  </div>
  <div class="metric">
    <div class="label">信号触发胜率</div>
    <div class="value">{{ "%.2f%%"|format(result.win_rate * 100) }}</div>
  </div>
  <div class="metric">
    <div class="label">累计收益</div>
    <div class="value {% if result.cumulative_return >= 0 %}pnl-up{% else %}pnl-down{% endif %}">
      {% if result.cumulative_return >= 0 %}+{% endif %}{{ "%.2f%%"|format(result.cumulative_return * 100) }}
    </div>
  </div>
</div>

<div class="card">
  <p>{{ result.summary }}</p>
  <img class="chart" src="/static/{{ result.png_name }}" alt="累计收益曲线">
</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 2: 跑回测路由测试验证基本可用**

Run:
```bash
cd /mnt/d/培训/ai_lesson/lesson6/project
pytest tests/test_routes_backtest.py -v
```

注：`test_get_backtest_form` 断言 `"form" in r.text.lower()` — 仍 PASS（HTML 还有 `<form>`）。
注：`test_get_backtest_form` 断言 `"dual_ma" in r.text` — 仍 PASS（下拉里有）。
注：`test_post_backtest_runs_and_renders_summary` 断言 `"夏普" in r.text or "Sharpe" in r.text` — 仍 PASS（模板有 "年化夏普"）。

Expected: 2 passed。

- [ ] **Step 3: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/app/templates/backtest.html
git commit -m "quant-trader: ui v1.1 — /backtest 中文 + 大数字结果卡"
```

---

## Task 4: 重写 `/bots` 列表 + bots_table partial + bot_status partial

**Files:**
- Modify: `lesson6/project/app/templates/bots_list.html`（整体重写）
- Modify: `lesson6/project/app/templates/partials/bots_table.html`（整体重写为卡片网格）
- Modify: `lesson6/project/app/templates/partials/bot_status.html`（升级为统一徽章组件）
- Modify: `lesson6/project/app/routes/bots.py`（bots_list / bots_table_partial 多传 positions dict 供卡片显示资金）
- Modify: `lesson6/project/tests/test_routes_bots.py`（中文化 "暂无" 断言）

- [ ] **Step 1: 修改 `tests/test_routes_bots.py` 改 empty-state 断言**

定位 `test_get_bots_empty`，替换：
```python
def test_get_bots_empty():
    with TestClient(app) as client:
        r = client.get("/bots")
        assert r.status_code == 200
        assert "No bots" in r.text or "暂无" in r.text
```

为：
```python
def test_get_bots_empty():
    with TestClient(app) as client:
        r = client.get("/bots")
        assert r.status_code == 200
        assert "还没有机器人" in r.text
```

`test_create_bot_then_list_shows_it` 仍找 `"ma-btc-1h"` — 不动。
`test_bot_detail_page` 仍找 `"x"` — 不动。
`test_delete_bot_soft_deletes` 仍找 `"to-delete"` not in — 不动。

- [ ] **Step 2: 跑测试验证 empty 断言失败**

Run: `pytest tests/test_routes_bots.py::test_get_bots_empty -v`
Expected: FAIL（旧模板说 "暂无 bot；用上面的表单..."，新断言要 "还没有机器人"）。

- [ ] **Step 3: 重写 `app/templates/partials/bot_status.html`**

```html
<span class="badge status-{{ status }}">{{ {"running":"运行中","stopped":"已停止","errored":"异常","deleted":"已删除"}.get(status, status) }}</span>
```

- [ ] **Step 4: 修改 `app/routes/bots.py` 让 `bots_list` 和 `bots_table_partial` 多传 positions**

定位 `bots_list` 函数，整体替换：

```python
@router.get("/bots", response_class=HTMLResponse)
async def bots_list(
    request: Request,
    session: Session = Depends(get_session),  # noqa: B008
) -> HTMLResponse:
    bots = session.exec(
        select(Bot).where(Bot.status != BotStatus.deleted).order_by(Bot.id)
    ).all()
    positions = {p.bot_id: p for p in session.exec(select(Position)).all()}
    return templates.TemplateResponse(
        request,
        "bots_list.html",
        {
            "bots": bots,
            "positions": positions,
            "strategies": list(STRATEGY_REGISTRY.keys()),
        },
    )
```

定位 `bots_table_partial`，整体替换：

```python
@router.get("/bots/partial", response_class=HTMLResponse)
async def bots_table_partial(
    request: Request,
    session: Session = Depends(get_session),  # noqa: B008
) -> HTMLResponse:
    bots = session.exec(
        select(Bot).where(Bot.status != BotStatus.deleted).order_by(Bot.id)
    ).all()
    positions = {p.bot_id: p for p in session.exec(select(Position)).all()}
    return templates.TemplateResponse(
        request,
        "partials/bots_table.html",
        {"bots": bots, "positions": positions},
    )
```

同样，定位 `bot_start` 和 `bot_stop` 和 `bot_delete` 末尾的 `return templates.TemplateResponse(... "partials/bots_table.html" ...)` 调用，把上下文从 `{"bots": bots}` 改成 `{"bots": bots, "positions": positions}`，并在 select(Bot)... 前面加 `positions = {p.bot_id: p for p in session.exec(select(Position)).all()}`。

例如 `bot_start` 末尾改成：

```python
    add_bot_job(scheduler, bot, _on_tick)
    bots = session.exec(
        select(Bot).where(Bot.status != BotStatus.deleted).order_by(Bot.id)
    ).all()
    positions = {p.bot_id: p for p in session.exec(select(Position)).all()}
    return templates.TemplateResponse(
        request, "partials/bots_table.html", {"bots": bots, "positions": positions}
    )
```

`bot_stop` 和 `bot_delete` 末尾同样改。

- [ ] **Step 5: 重写 `app/templates/partials/bots_table.html` 为卡片网格**

```html
{% if bots %}
<div class="metrics" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
{% for b in bots %}
  {% set p = positions.get(b.id) %}
  {% set equity = (p.cash + p.base_qty * (p.avg_entry_price or 0)) if p else 0 %}
  <div class="card" style="margin-bottom: 0;">
    <div class="row justify-between" style="margin-bottom: 8px;">
      <a href="/bots/{{ b.id }}" style="font-weight: 600; font-size: 16px;">{{ b.name }}</a>
      {% with status=b.status.value %}{% include "partials/bot_status.html" %}{% endwith %}
    </div>
    <div class="muted" style="font-size: 12px; margin-bottom: 12px;">
      {{ b.strategy_name }} · {{ b.symbol }} · {{ b.interval }} · {{ {"paper":"纸交易","binance_testnet":"币安测试网"}.get(b.exchange.value, b.exchange.value) }}
    </div>
    <table style="margin-bottom: 12px;">
      <tbody>
        <tr><td style="color:#64748b;">现金</td><td class="numeric" style="text-align:right;">{{ "%.2f"|format(p.cash if p else 0) }}</td></tr>
        <tr><td style="color:#64748b;">持仓</td><td class="numeric" style="text-align:right;">{{ "%.6f"|format(p.base_qty if p else 0) }}</td></tr>
        <tr><td style="color:#64748b;">入场均价</td><td class="numeric" style="text-align:right;">{{ "%.2f"|format(p.avg_entry_price) if p and p.avg_entry_price else "—" }}</td></tr>
      </tbody>
    </table>
    <div class="actions">
      {% if b.status.value == "running" %}
      <button hx-post="/bots/{{ b.id }}/stop" hx-target="#bots-table" class="secondary">停止</button>
      {% else %}
      <button hx-post="/bots/{{ b.id }}/start" hx-target="#bots-table">启动</button>
      {% endif %}
      <button hx-delete="/bots/{{ b.id }}" hx-target="#bots-table"
              hx-confirm="确认删除机器人「{{ b.name }}」？" class="danger">删除</button>
    </div>
  </div>
{% endfor %}
</div>
{% else %}
<div class="empty">
  <div class="emoji">🤖</div>
  <div>还没有机器人</div>
  <div class="hint">点击上方「新建机器人」开始创建第一个交易实例</div>
</div>
{% endif %}
```

- [ ] **Step 6: 重写 `app/templates/bots_list.html`**

```html
{% extends "base.html" %}
{% block title %}机器人 — QuantTrader{% endblock %}
{% block content %}
<div class="row justify-between" style="margin-bottom: 16px;">
  <h1 style="margin: 0;">机器人</h1>
</div>

<details style="margin-bottom: 16px;">
  <summary>新建机器人</summary>
  <div class="card" style="margin-top: 8px;">
    <form class="stack" method="post" action="/bots">
      <label>名称 <input name="name" required placeholder="例：ma-btc-1h"></label>
      <label>策略
        <select name="strategy_name">
          {% for s in strategies %}<option value="{{ s }}">{{ s }}</option>{% endfor %}
        </select>
      </label>
      <label>交易对 <input name="symbol" value="BTCUSDT"></label>
      <label>周期
        <select name="interval">
          {% for iv in ["1m","5m","15m","1h"] %}<option value="{{ iv }}">{{ iv }}</option>{% endfor %}
        </select>
      </label>
      <label>撮合
        <select name="exchange">
          <option value="paper">纸交易</option>
          <option value="binance_testnet">币安测试网</option>
        </select>
      </label>
      <label>初始资金 <input name="initial_capital" type="number" value="10000" step="any"></label>
      <label>参数 JSON（留空用默认值）<input name="params" value="{}"></label>
      <label>&nbsp;<button type="submit">创建</button></label>
    </form>
  </div>
</details>

<div id="bots-table" hx-get="/bots/partial" hx-trigger="every 5s" hx-swap="innerHTML">
  {% include "partials/bots_table.html" %}
</div>
{% endblock %}
```

- [ ] **Step 7: 验证测试通过**

Run:
```bash
cd /mnt/d/培训/ai_lesson/lesson6/project
pytest tests/test_routes_bots.py -v
```
Expected: 5 passed（test_get_bots_empty 现在断言 `"还没有机器人"`，应满足）。

如果 ruff 有抱怨（比如 routes/bots.py 复杂度上升），fix 或加 noqa 处理；目标 `ruff check .` 0 errors。

- [ ] **Step 8: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/app/templates/ \
              lesson6/project/app/routes/bots.py \
              lesson6/project/tests/test_routes_bots.py
git commit -m "quant-trader: ui v1.1 — /bots 卡片网格 + 资金概要 + 中文 empty state"
```

---

## Task 5: 重写 `/bots/{id}` 详情 + equity 曲线 PNG + 新增测试

**Files:**
- Modify: `lesson6/project/app/routes/bots.py`（bot_detail 拉 pnl_snapshots + 调 _render_equity_png；新私有 helper）
- Modify: `lesson6/project/app/templates/bot_detail.html`（整体重写）
- Modify: `lesson6/project/tests/test_routes_bots.py`（新增 2 个 equity 测试）

- [ ] **Step 1: 先加 2 个失败测试到 `tests/test_routes_bots.py`**

在文件末尾追加：

```python
def test_bot_detail_renders_equity_section_when_snapshots_exist(_setup_db):
    from sqlmodel import Session
    from app.models import PnLSnapshot
    new_engine = _setup_db
    # 创建 bot
    with TestClient(app) as client:
        client.post("/bots", data={
            "name": "with-pnl", "strategy_name": "dual_ma", "symbol": "BTCUSDT",
            "interval": "1h", "exchange": "paper", "initial_capital": "10000", "params": "{}",
        }, follow_redirects=True)
        # 直接 DB 插 3 条 pnl_snapshot
        with Session(new_engine) as s:
            for i, equity in enumerate([10000.0, 10050.0, 10100.0]):
                s.add(PnLSnapshot(
                    bot_id=1, snapshot_at=f"2026-05-17T0{i}:00:00Z",
                    mark_price=100.0, equity=equity,
                    unrealized_pnl=0.0, realized_pnl=equity - 10000.0,
                ))
            s.commit()
        r = client.get("/bots/1")
        assert r.status_code == 200
        assert "资金曲线" in r.text
        assert "equity_1.png" in r.text


def test_bot_detail_no_equity_section_when_empty(_setup_db):
    with TestClient(app) as client:
        client.post("/bots", data={
            "name": "no-pnl", "strategy_name": "dual_ma", "symbol": "BTCUSDT",
            "interval": "1h", "exchange": "paper", "initial_capital": "10000", "params": "{}",
        }, follow_redirects=True)
        r = client.get("/bots/1")
        assert r.status_code == 200
        # 没快照时不渲染 equity 段
        assert "资金曲线" not in r.text
```

注：`_setup_db` fixture 当前 yield `new_engine`（见 Step 4 of Task 12 在 v1 plan）。新测试函数签名直接接 fixture 即可。

- [ ] **Step 2: 跑这 2 个新测试验证失败**

Run: `pytest tests/test_routes_bots.py::test_bot_detail_renders_equity_section_when_snapshots_exist tests/test_routes_bots.py::test_bot_detail_no_equity_section_when_empty -v`
Expected: 失败（路由还没拉 pnl_snapshots，模板里没 "资金曲线" 字串）。

- [ ] **Step 3: 在 `app/routes/bots.py` 末尾加私有 helper `_render_equity_png`**

在文件末尾加：

```python


def _render_equity_png(bot_id: int, snapshots: list) -> str | None:
    """画 equity 曲线写到 static/equity_<bot_id>.png；snapshots 为空返回 None。"""
    if not snapshots:
        return None
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    static_dir = Path("static")
    static_dir.mkdir(parents=True, exist_ok=True)
    png_name = f"equity_{bot_id}.png"
    png_path = static_dir / png_name

    xs = list(range(len(snapshots)))
    ys = [s.equity for s in snapshots]

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(xs, ys, color="#2563eb", linewidth=2)
    ax.axhline(ys[0], linestyle="--", color="#94a3b8", linewidth=0.8, label="起点")
    ax.fill_between(xs, ys, ys[0], where=[y >= ys[0] for y in ys], color="#fee2e2", alpha=0.5)
    ax.fill_between(xs, ys, ys[0], where=[y < ys[0] for y in ys], color="#dcfce7", alpha=0.5)
    ax.set_title(f"Equity curve — bot {bot_id}")
    ax.set_xlabel("snapshot #")
    ax.set_ylabel("equity")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(png_path, dpi=120)
    plt.close(fig)
    return png_name
```

- [ ] **Step 4: 改 `bot_detail` 路由拉 pnl_snapshots + 调 helper**

定位 `bot_detail`，整体替换为：

```python
@router.get("/bots/{bot_id}", response_class=HTMLResponse)
async def bot_detail(
    request: Request,
    bot_id: int,
    session: Session = Depends(get_session),  # noqa: B008
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
    snapshots = session.exec(
        select(PnLSnapshot)
        .where(PnLSnapshot.bot_id == bot_id)
        .order_by(PnLSnapshot.snapshot_at)
        .limit(200)
    ).all()
    equity_png_name = _render_equity_png(bot_id, snapshots)
    latest_equity = snapshots[-1].equity if snapshots else None
    pct_change = (
        (latest_equity - bot.initial_capital) / bot.initial_capital * 100
        if latest_equity is not None and bot.initial_capital
        else None
    )
    return templates.TemplateResponse(
        request,
        "bot_detail.html",
        {
            "bot": bot,
            "position": position,
            "fills": fills,
            "tick_logs": tick_logs,
            "equity_png_name": equity_png_name,
            "latest_equity": latest_equity,
            "pct_change": pct_change,
        },
    )
```

同时在文件顶部 `from app.models import (...)` 那一行加上 `PnLSnapshot`：

```python
from app.models import (
    Bot, BotStatus, Exchange as ExchangeEnum, Fill, PnLSnapshot, Position, TickLog,
)
```

- [ ] **Step 5: 整体重写 `app/templates/bot_detail.html`**

```html
{% extends "base.html" %}
{% block title %}{{ bot.name }} — QuantTrader{% endblock %}
{% block content %}
<div class="row justify-between" style="margin-bottom: 8px;">
  <h1 style="margin: 0;">{{ bot.name }}
    {% with status=bot.status.value %}{% include "partials/bot_status.html" %}{% endwith %}
  </h1>
  <div class="actions">
    {% if bot.status.value == "running" %}
    <form method="post" action="/bots/{{ bot.id }}/stop" style="display: inline;">
      <button class="secondary">停止</button>
    </form>
    {% elif bot.status.value != "deleted" %}
    <form method="post" action="/bots/{{ bot.id }}/start" style="display: inline;">
      <button>启动</button>
    </form>
    {% endif %}
    <a href="/bots" class="btn secondary" style="text-decoration: none;">返回列表</a>
  </div>
</div>
<div class="muted" style="margin-bottom: 20px;">
  {{ bot.strategy_name }} · {{ bot.symbol }} · {{ bot.interval }} ·
  {{ {"paper":"纸交易","binance_testnet":"币安测试网"}.get(bot.exchange.value, bot.exchange.value) }} ·
  初始资金 <span class="numeric">{{ "%.2f"|format(bot.initial_capital) }}</span>
</div>

<div class="section">
  <div class="section-title">资金概要</div>
  <div class="metrics">
    <div class="metric">
      <div class="label">现金</div>
      <div class="value">{{ "%.2f"|format(position.cash if position else 0) }}</div>
    </div>
    <div class="metric">
      <div class="label">持仓数量</div>
      <div class="value">{{ "%.6f"|format(position.base_qty if position else 0) }}</div>
    </div>
    <div class="metric">
      <div class="label">入场均价</div>
      <div class="value">{{ "%.2f"|format(position.avg_entry_price) if position and position.avg_entry_price else "—" }}</div>
    </div>
    <div class="metric">
      <div class="label">当前权益</div>
      <div class="value">{{ "%.2f"|format(latest_equity) if latest_equity is not none else "—" }}</div>
      {% if pct_change is not none %}
      <div class="sub {% if pct_change >= 0 %}pnl-up{% else %}pnl-down{% endif %}">
        {% if pct_change >= 0 %}+{% endif %}{{ "%.2f%%"|format(pct_change) }}
      </div>
      {% endif %}
    </div>
  </div>
</div>

{% if equity_png_name %}
<div class="section">
  <div class="section-title">资金曲线</div>
  <div class="card">
    <img class="chart" src="/static/{{ equity_png_name }}" alt="资金曲线">
  </div>
</div>
{% endif %}

<div class="grid-2">
  <div class="section">
    <div class="section-title">最近成交（最近 20 条）</div>
    {% if fills %}
    <table>
      <thead><tr><th>时间</th><th>订单</th><th>价格</th><th>数量</th><th>手续费</th></tr></thead>
      <tbody>
      {% for f in fills %}
        <tr>
          <td class="numeric" style="font-size: 12px;">{{ f.filled_at }}</td>
          <td class="numeric">{{ f.order_id }}</td>
          <td class="numeric">{{ "%.2f"|format(f.price) }}</td>
          <td class="numeric">{{ "%.6f"|format(f.quantity) }}</td>
          <td class="numeric">{{ "%.4f"|format(f.fee) }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    {% else %}
    <div class="empty"><div class="emoji">📭</div><div>暂无成交</div></div>
    {% endif %}
  </div>

  <div class="section">
    <div class="section-title">最近 tick（最近 20 条）</div>
    {% if tick_logs %}
    <table>
      <thead><tr><th>时间</th><th>状态</th><th>消息</th></tr></thead>
      <tbody>
      {% for t in tick_logs %}
        <tr>
          <td class="numeric" style="font-size: 12px;">{{ t.tick_at }}</td>
          <td>{% with status=t.status.value %}<span class="badge status-{{ status }}">{{ {"success":"成功","skipped":"跳过","errored":"异常"}.get(status, status) }}</span>{% endwith %}</td>
          <td style="font-size: 12px;">{{ t.message }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    {% else %}
    <div class="empty"><div class="emoji">⏱</div><div>暂无 tick 记录</div></div>
    {% endif %}
  </div>
</div>
{% endblock %}
```

- [ ] **Step 6: 跑测试**

Run:
```bash
cd /mnt/d/培训/ai_lesson/lesson6/project
pytest tests/test_routes_bots.py -v
```
Expected: 7 passed（原 5 + 新 2）。

跑全量：
```bash
pytest --cov=app --cov-fail-under=80 && ruff check .
```
Expected: 全绿，coverage 不掉。

- [ ] **Step 7: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/app/routes/bots.py \
              lesson6/project/app/templates/bot_detail.html \
              lesson6/project/tests/test_routes_bots.py
git commit -m "quant-trader: ui v1.1 — bot_detail 资金概要 + equity 曲线 PNG"
```

---

## Self-Review Checklist（plan 写完后回头核对）

- [ ] Spec §3 视觉系统 → Task 1 CSS 全覆盖（颜色、几何、字体）
- [ ] Spec §4 5 个页面 → Task 1 (base) / Task 2 (strategies) / Task 3 (backtest) / Task 4 (bots) / Task 5 (bot_detail) 各对应一个 task
- [ ] Spec §5.1 bot_detail 路由扩展 + helper → Task 5
- [ ] Spec §5.2 STRATEGY_DESCRIPTIONS → Task 2
- [ ] Spec §6 CSS 9 段结构 → Task 1
- [ ] Spec §7 测试更新 + 新增 → Task 4 (中文断言) + Task 5 (equity 测试)
- [ ] 无 TBD / TODO / "implement later"
- [ ] 类型一致性：路由签名、模板变量名、PnLSnapshot/Position 字段名各处一致
- [ ] 每个 task 末尾都有 commit
- [ ] 测试覆盖率不下降（task 5 加新 helper 但有 2 个新测试覆盖）

---

## 执行说明

- **顺序**：Task 1（CSS 基座）必须先做；其他 task 互相不强依赖，但按 1→5 顺序最少返工。
- **每个 task 完成后**：浏览器手动开 `http://localhost:8000` 看一眼对应页面，跟 v1 截图对比。
- **uvicorn 已在后台跑**（pid `bflsoww07`）；改完模板/路由后浏览器刷新就生效（FastAPI 默认无 reload，需要 `uvicorn --reload` 或手动重启 uvicorn）。
- **静态资源缓存**：浏览器可能缓存 style.css；改完 CSS 后强制刷新（Ctrl+Shift+R）。

**完成后**：5 个页面浏览器对比明显升级 + 测试全绿 = v1.1 可交付。
