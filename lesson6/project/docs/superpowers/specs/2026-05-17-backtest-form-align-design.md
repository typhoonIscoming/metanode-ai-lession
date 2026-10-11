# Backtest Form Alignment Fix — Design

**Date:** 2026-05-17
**Status:** Approved
**Scope:** v1.2.1（v1.2 之后的 UI 修复，无功能变化）

---

## 1. Problem

`/backtest` 表单的「起始时间」「结束时间」输入框跟其它字段不在同一基线上。

**根因**：`form.stack` 是 grid（`auto-fit minmax(180px, 1fr)`），每个 `<label>` 是一个 cell，cell 内 `flex-direction: column`（标题在上、input 在下）。「起始时间 (UTC，可空)」「结束时间 (UTC，可空)」「行数（最近 N 根 K 线）」「参数 JSON（留空用默认值）」这些标题在窄列里**换行成 2 行**，而「策略 / 交易对 / 周期」是 1 行 → 同行 cell 高度不一致 → input 基线错位。

附带毛病：表单 7 cell 用 auto-fit 排成 6 列时，第 7 个「开始回测」按钮会被丢到下一行只占 1 列，孤立又突兀。

## 2. Solution

5 个改动，零功能变化：

1. **`form.stack { align-items: end }`** — 强制每个 cell 底边对齐；input 自然在同一基线
2. **`form label > input/select { min-height: 36px }`** — 输入控件统一高度，进一步稳基线
3. **把按钮从 grid 里拿出来**，单独放在表单底部右侧（去掉 `<label>&nbsp;` 这个 hack）
4. **gap 从 12px 加到 16px**，喘息感更好
5. **`(UTC，可空)` 这种 hint 改用 `<small class="hint">`** 放在 input 下面，不再挤压标题行；同时去掉模板里的 inline `style=...`

## 3. Files

| 文件 | 改动 |
|---|---|
| `app/templates/backtest.html` | 标题里的 `<span>` 拆成 input 下方的 `<small>`；移除「开始回测」label 包装，单独放表单底部 `<div class="form-footer">` 右对齐 |
| `static/style.css` | `form.stack` 加 `align-items: end` + `gap: 16px`；input/select 加 `min-height: 36px`；新增 `.hint` 和 `.form-footer` 两个 utility class |

## 4. CSS 增量

`static/style.css` 第 4 段「Form」末尾追加 / 局部改：

```css
form.stack { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
             align-items: end; }
form input, form select, form textarea {
    padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px;
    font-size: 14px; background: #fff; font-family: inherit;
    min-height: 36px;
}
.hint { display: block; font-size: 11px; color: #94a3b8; margin-top: 4px; }
.form-footer { display: flex; justify-content: flex-end; margin-top: 16px; }
```

## 5. 模板增量

`backtest.html` 关键改动：

- 起始时间 / 结束时间 label 改为：
  ```html
  <label>起始时间
    <input name="start_time" type="datetime-local" value="{{ request_start_time or '' }}">
    <small class="hint">UTC，留空走「行数」模式</small>
  </label>
  ```
- 「行数」「参数 JSON」label 内的括号备注同样下沉到 `<small class="hint">`，保持标题简短
- 移除 `<label>&nbsp;<button>开始回测</button></label>`，改用：
  ```html
  </form>  <!-- form 结束在 params label 之后 -->
  ...
  <div class="form-footer">
    <button type="submit" form="backtest-form">开始回测</button>
  </div>
  ```
  注意：button 用 `form="backtest-form"` 属性绑定回外层 form；同时给 `<form>` 加 `id="backtest-form"`

（**或更简洁**：把 footer div 放进 form 内，按钮直接是 form 子元素，不用 form 属性绑定。两种都行，后者更简单。spec 选**后者**。）

## 6. 测试

不动测试。`test_get_backtest_form` 断言 `"form" in r.text.lower()` 和 `"dual_ma" in r.text`，都满足；`test_post_backtest_*` 测试断言的是结果文本不依赖结构。

跑全套确保零回归：`pytest -v && ruff check .` → 60 + 2 skipped。

## 7. 验收

- 浏览器开 `/backtest`：所有输入框底边在同一直线上，无论标题是 1 行还是 2 行
- 按钮显示在表单底部右下角，不再孤立挤在网格里
- 所有 hint 文字（UTC、参数说明等）显示在 input 下方，不影响标题行高
- 测试 60 + 2 skipped 全绿
