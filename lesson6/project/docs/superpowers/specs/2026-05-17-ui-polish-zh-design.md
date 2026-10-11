# UI Polish (中文化 + 现代卡片风) — Design

**Date:** 2026-05-17
**Status:** Approved for implementation planning
**Scope:** quant-trader v1 已上线后的 UI 迭代（v1.1）
**Authors:** locey + Claude (via superpowers:brainstorming)

---

## 1. Purpose

把 quant-trader v1 的 5 个 Web 页面从「能用但丑」升级到「简单清晰易懂、看起来像个正经产品」。全部中文化，统一现代卡片视觉，Bot 详情页加入小型资金曲线。后端业务/路由零改动；仅模板、CSS、`bot_detail` 路由读多一张表。

## 2. Scope

### In scope
- 5 个页面模板 + 2 个 partials 全部中文化、卡片化
- `static/style.css` 从 20 行扩到 ~150 行，引入 utility classes
- `app/routes/bots.py:bot_detail` 多查 `pnl_snapshots` 并生成 `static/equity_<bot_id>.png`
- `STRATEGY_REGISTRY` 旁挂一个 `STRATEGY_DESCRIPTIONS: dict[str, str]`，给每个策略一行中文人话描述（不改 dataclass）
- 更新 `tests/test_routes_bots.py` 里"暂无 bot"等中文化字符串断言

### Out of scope（v2 再说）
- 新建 `/dashboard` 总览页
- WebSocket 实时推送（仍用 HTMX 5s 轮询）
- 主题切换（深色模式）
- Equity curve 用 JS 图表库渲染（v1.1 仍用后端生成 PNG）
- `Bot.strategy_params` 编辑 UI（现在只能在创建时填）

## 3. 视觉系统

### 颜色
| 用途 | 颜色 | 备注 |
|---|---|---|
| 页面背景 | `#f5f6fa` | |
| 卡片背景 | `#ffffff` | |
| 主色（链接/按钮/强调） | `#2563eb` | 蓝 |
| 中性文字 | `#1f2937`（主）/ `#64748b`（次） | |
| 分隔线 | `#e5e7eb` | |
| **PnL 涨/盈利** | `#dc2626` | 红，**中国惯例** |
| **PnL 跌/亏损** | `#16a34a` | 绿 |
| 状态 - 运行中 | `#2563eb` | 蓝（避免和 PnL 红冲突）|
| 状态 - 已停止 | `#64748b` | 灰 |
| 状态 - 异常 | `#ea580c` | 橙（避免和 PnL 红冲突）|
| 状态 - 已删除 | `#94a3b8` | 浅灰 |

### 几何
- 圆角：卡片 `12px`、按钮 `8px`、徽章 `999px`
- 卡片阴影：`0 1px 3px rgba(15,23,42,.04), 0 1px 2px rgba(15,23,42,.06)`
- 间距：`gap-sm=8px / gap-md=16px / gap-lg=24px`
- 内容最大宽：1200px

### 字体
- 默认：`-apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif`
- 数字（价格 / 数量 / 时间）：`ui-monospace, "SF Mono", Consolas, monospace`

## 4. 页面改造

### 4.1 `base.html`
- 顶栏品牌名 `QuantTrader` + 副标 `量化交易实验台`
- 导航中文：`机器人 / 回测 / 策略库`
- HTMX 1.9.10 CDN 不变

### 4.2 `/bots` 机器人列表
- 顶部 H1 `机器人`
- 「+ 新建机器人」按钮 → 折叠 `<details>` 内的表单（中文 labels：名称 / 策略 / 交易对 / 周期 / 撮合 / 初始资金 / 参数）
- 列表用**卡片网格**（每个 bot 一张卡），每卡含：
  - 名称 + 状态徽章（彩色 chip）
  - 一行小字：`策略 / 交易对 / 周期`
  - 三个数字：现金 / 持仓数量 / 当前权益（从 position 计算）
  - 底部按钮组：详情 / 启动|停止 / 删除（删除带 confirm）
- 空状态：居中插画位 + 一行字「还没有机器人，点上面"新建机器人"开始」
- `hx-trigger="every 5s"` 自动刷新保留

### 4.3 `/bots/{id}` 机器人详情
版面三部分：
1. **顶部**：H1 名称 + 状态徽章 + 配置 caption（`{strategy} · {symbol} · {interval} · {exchange}`） + 启停删按钮组
2. **资金概要卡片组**（4 个并列）：
   - 现金 / 持仓数量 / 持仓均价 / 当前权益（最后一项配 vs initial 的 +/-% 涨幅徽章，红涨绿跌）
3. **资金曲线**（如果有 `pnl_snapshots`）：标题 `资金曲线` + 一张 `static/equity_<bot_id>.png`（matplotlib Agg 后端生成，equity 折线 + 起点基线）
4. **两栏**：
   - 左：最近成交（时间 / 订单号 / 价格 / 数量 / 手续费），空时显 "暂无成交"
   - 右：最近 tick 日志（时间 / 状态徽章 / 消息），空时显 "暂无 tick 记录"

### 4.4 `/backtest` 回测
- 表单卡片化，labels 中文（策略 / 交易对 / 周期 / 行数 / 参数 JSON）
- 结果区 4 张大数字卡片：`年化夏普` / `最大回撤` / `胜率` / `累计收益`
- 中文 summary 段落 + 累计曲线 PNG
- 错误（缺数据 / 未知策略）显友好提示卡

### 4.5 `/strategies` 策略库
- 卡片网格，每个策略一张：
  - 大字策略名（英文 code）
  - 一行中文人话描述（从 `STRATEGY_DESCRIPTIONS`）
  - 默认参数表（key/value 两列）

## 5. 后端微改

### 5.1 `bot_detail` 路由扩展
- 多查 `pnl_snapshots`（取最近 N=200 条按 `snapshot_at` 升序）
- 在 `app/routes/bots.py` 同模块内加私有 helper `_render_equity_png(bot_id, snapshots) -> str | None`：用 matplotlib Agg 后端画 equity 折线（reuse `app/backtest.py` 的画图风格），写到 `lesson6/project/static/equity_<bot_id>.png`，返回文件名；snapshots 为空时返回 `None` 不画
- 因为 `/bots/{id}` 不是 HTMX 轮询页（用户手动访问），每次重新生成 PNG 即可，不缓存
- 传给模板：`equity_png_name` (None 或 str)、`equity_summary` 包含 `latest_equity` + `pct_change_vs_initial`

### 5.2 `STRATEGY_DESCRIPTIONS`
在 `app/strategies/registry.py` 增：
```python
STRATEGY_DESCRIPTIONS: dict[str, str] = {
    "dual_ma":   "双均线交叉：短均线上穿长均线时做多，下穿时清仓。趋势跟随。",
    "rsi":       "RSI 反转：相对强弱指数跌破超卖线做多，涨破超买线清仓。均值回归。",
    "macd":      "MACD 金叉：MACD 线上穿信号线做多，下穿清仓。中期趋势确认。",
    "bollinger": "布林带均值回归：收盘价跌破下轨做多，回到中轨清仓。震荡市策略。",
}
```
不改 `StrategyEntry` dataclass（避免动 Task 4 的接口）；`/strategies` 路由读 `STRATEGY_DESCRIPTIONS.get(name, "")`。

## 6. CSS 文件结构

`static/style.css` 重写为分段：
```
/* 1. Reset + 全局排版 */
/* 2. Layout（header / main / container）*/
/* 3. Card + section utility */
/* 4. Form（label / input / button / select）*/
/* 5. Table */
/* 6. Badge + status */
/* 7. Metric cards（资金概要 / 回测结果）*/
/* 8. Empty state */
/* 9. Helpers（numeric / pnl-up / pnl-down / muted）*/
```
约 150 行，无外部依赖。

## 7. 测试更新

`tests/test_routes_bots.py`：
- `test_get_bots_empty` 现在断言 `"No bots" in r.text or "暂无" in r.text` — 改成只断言 `"还没有机器人" in r.text` 或保留宽松
- `test_strategies_page_lists_four` 仍断言 4 个策略名 → 不变（英文 code 仍渲染）
- `test_create_bot_then_list_shows_it` 仍找 `"ma-btc-1h"` → 不变
- `test_bot_detail_page` 仍找 `"x"` → 不变

新增：
- `test_bot_detail_renders_equity_section_when_snapshots_exist`：插 3 条 PnLSnapshot，断言响应里有 `"资金曲线"` 字串
- `test_bot_detail_no_equity_section_when_empty`：无 snapshot 时不渲染 equity 区

## 8. 验收

- `pytest -v && ruff check .` 全绿
- 覆盖率不低于 80%（不变 / 微涨）
- 浏览器实际打开 5 个页面，跟 v1 截图对比：感观差距明显
- 没有任何业务逻辑或 schema 改动（grep 验证 routes 的 select/insert 逻辑未变）

## 9. 已知不修

- bot 详情页"删除"按钮在第 (4.3) 节没单独列出，沿用 partials/bots_table 已有的 hx-delete 模式即可
- equity_<bot_id>.png 多个 bot 并存时会有多张图占 static/；gitignore 已排除 `*.png`
- 策略中文描述硬编码在 registry.py，将来要 i18n 时迁移到独立 dict 或 yml

---

**Approved by**: locey, 2026-05-17
**Next step**: superpowers:writing-plans → 产出 UI 改造 plan（预计 5-7 个 task）
