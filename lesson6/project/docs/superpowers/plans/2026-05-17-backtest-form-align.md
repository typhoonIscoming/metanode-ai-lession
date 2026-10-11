# Backtest Form Alignment Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 `/backtest` 表单输入框基线错位 + 优化按钮放置；零功能改动。

**Architecture:** 2 个文件改动，1 个 task。CSS 加 `align-items: end` 让 grid cell 底边对齐 + input 加 `min-height: 36px` 稳基线；模板把 hint 从标题里的 `<span>` 改成 input 下方的 `<small class="hint">`，按钮拆出 grid 单独放 `<div class="form-footer">` 右对齐。

**Tech Stack:** 纯 HTML/CSS。无 JS。无新依赖。

---

## File Structure

| 文件 | 改动 |
|---|---|
| `static/style.css` | 修改 form.stack + form input；新增 `.hint` 和 `.form-footer` |
| `app/templates/backtest.html` | 重写表单内 7 个 label + 移按钮到 form-footer |

---

## Task 1: 修对齐 + 重排按钮（1 个 commit）

**Files:**
- Modify: `lesson6/project/static/style.css`
- Modify: `lesson6/project/app/templates/backtest.html`

- [ ] **Step 1: 改 `static/style.css` — form.stack + input + 2 个新 utility**

定位文件第 4 段「Form」中的 `form.stack` 和 `form input, form select, form textarea`，整体替换为：

```css
form.stack { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
             align-items: end; }
form label { display: flex; flex-direction: column; font-size: 13px; color: #475569; gap: 4px; }
form input, form select, form textarea {
    padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px;
    font-size: 14px; background: #fff; font-family: inherit;
    min-height: 36px;
}
```

在第 4 段「Form」末尾追加：

```css
.hint { display: block; font-size: 11px; color: #94a3b8; margin-top: 4px; }
.form-footer { display: flex; justify-content: flex-end; margin-top: 16px; padding-top: 16px;
               border-top: 1px solid #f1f5f9; }
```

- [ ] **Step 2: 整体重写 `app/templates/backtest.html`**

替换为：

```html
{% extends "base.html" %}
{% block title %}回测 — QuantTrader{% endblock %}
{% block content %}
<h1>回测</h1>
<p class="muted">基于历史 K 线一次性回放策略，输出夏普 / 最大回撤 / 胜率 / 累计收益 + 累计曲线。
  填了起止时间会走「时间段」模式（缺数据时自动从 Binance 拉补，最多 200000 根）；否则按上面的「行数」回放最近 N 根。</p>

{% if error_msg %}
<div class="card" style="border-left: 4px solid #dc2626; background: #fef2f2; color: #991b1b; padding: 12px 16px; margin-bottom: 16px;">
  <strong>⚠️ 出错了：</strong> {{ error_msg }}
</div>
{% endif %}

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
    <label>行数
      <input name="limit" type="number" value="{{ request_limit or 100 }}">
      <small class="hint">最近 N 根 K 线</small>
    </label>
    <label>起始时间
      <input name="start_time" type="datetime-local" value="{{ request_start_time or '' }}">
      <small class="hint">UTC，留空走「行数」模式</small>
    </label>
    <label>结束时间
      <input name="end_time" type="datetime-local" value="{{ request_end_time or '' }}">
      <small class="hint">UTC，留空走「行数」模式</small>
    </label>
    <label>参数 JSON
      <input name="params" value='{{ request_params or "{}" }}'>
      <small class="hint">留空用策略默认值</small>
    </label>
    <div class="form-footer" style="grid-column: 1 / -1;">
      <button type="submit">开始回测</button>
    </div>
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

关键差异 vs 旧版：
- 7 个 label 的标题文字都变成「**1-3 个汉字**」纯标题（策略 / 交易对 / 周期 / 行数 / 起始时间 / 结束时间 / 参数 JSON）
- 所有「(...)」括号备注下沉为 `<small class="hint">` 在 input 下方
- 移除 `<label>&nbsp;<button>...</button></label>` 这个 hack
- 按钮放在 `<div class="form-footer" style="grid-column: 1 / -1;">` 内 —— `grid-column: 1 / -1` 让 div 在 grid 内横跨整行；`form-footer` class 提供右对齐 + 顶部分隔线

- [ ] **Step 3: 跑测试 + lint，确认零回归**

Run:
```
cd /mnt/d/培训/ai_lesson/lesson6/project
pytest -v && ruff check .
```
Expected: 60 + 2 skipped 全绿。Ruff 0（CSS/HTML 文件不参与 ruff 检查）。

`tests/test_routes_backtest.py` 的 5 个测试都不依赖结构，只看字符串内容：
- `test_get_backtest_form` 找 `"form"` 和 `"dual_ma"` —— 仍在
- `test_post_backtest_runs_and_renders_summary` 找 `"夏普"` 或 `"Sharpe"` —— 仍在（"年化夏普"卡片标签）
- `test_post_backtest_with_range` 找 `"夏普"` 或 `"Sharpe"` —— 仍在
- `test_post_backtest_range_too_large` 找 `"时间范围过大"` —— 仍在（error_msg 渲染）
- `test_post_backtest_start_after_end` 找 `"起始时间不能晚于结束时间"` —— 仍在

- [ ] **Step 4: 浏览器手测对齐**

uvicorn 已在 127.0.0.1:8000 后台跑（pid `bfbcxf3bk`）。FastAPI 默认不 reload 模板？检查方式：直接 curl 看新 HTML：

```bash
curl -s http://127.0.0.1:8000/backtest | grep -E 'class="hint"|form-footer|<small'
```
Expected: 看到 3 个 `<small class="hint">` 和 1 个 `<div class="form-footer"`。

如果没看到（模板缓存），重启 uvicorn：
```bash
pkill -f "uvicorn app.main:app" 2>/dev/null; sleep 1
cd /mnt/d/培训/ai_lesson/lesson6/project
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/uvicorn-v121.log 2>&1 &
sleep 3
curl -sf http://127.0.0.1:8000/healthz && echo OK
```

浏览器 `Ctrl+Shift+R` 强刷 `http://localhost:8000/backtest`，确认：
- 7 个输入框底边对齐成一条直线
- 起止时间下面有灰色「UTC，留空走"行数"模式」小字
- 「开始回测」按钮显示在表单底部右下角，上面有一条浅色分隔线

- [ ] **Step 5: 提交**

```bash
cd /mnt/d/培训/ai_lesson
git add -A lesson6/project/static/style.css lesson6/project/app/templates/backtest.html
git commit -m "quant-trader: v1.2.1 — fix /backtest form alignment + footer button"
```

---

## Self-Review Checklist

- [ ] Spec §2 五个改动：(1) align-items: end → Step 1 ✓ (2) min-height: 36px → Step 1 ✓ (3) 按钮拆出 grid → Step 2 form-footer div ✓ (4) gap 12→16 → Step 1 ✓ (5) hint 改 small → Step 2 ✓
- [ ] Spec §3 两个文件 → Task 1 改两个 ✓
- [ ] Spec §6 不动测试 → Step 3 跑现有测试验证零回归 ✓
- [ ] Spec §7 验收三条 → Step 4 手测覆盖（基线对齐 / hint 显示 / 按钮位置）✓
- [ ] 无 TBD / TODO / placeholder
- [ ] 类型一致：CSS class 名 `.hint` `.form-footer` 在模板和 CSS 两处用法一致；`grid-column: 1 / -1` 在 form-footer div 上需要这样写（用 inline style 避免新增一个 class）
- [ ] 单个 task 单个 commit

---

## 执行说明

- 一个 task 就这一件事，不会跨 task 累积复杂度
- uvicorn 默认不监听模板/CSS 文件变化（除非加 `--reload`），改完要么浏览器强刷（CSS 会缓存）要么重启 uvicorn
- 浏览器对 `/static/style.css` 有缓存，**强刷必须 Ctrl+Shift+R**，否则看不到 CSS 变化
- 完成 = 测试 60+2 skipped 全绿 + 浏览器确认 3 条视觉验收点 → commit
