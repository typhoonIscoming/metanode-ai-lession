# Polymarket BTC 套利信号工具 · Frontend PRD

> 文档版本：v1.0.1
> 编写日期：2026-05-17
> 最近修订：2026-05-18
> 依赖文档：`PRD.md`、`backend-PRD.md`
>
> 修订记录：
> - v1.0.1 (2026-05-18)：前端框架版本由 Next.js 15 升级到 Next.js 16，原因：实施时 `create-next-app@latest` 默认值为 16，与本项目所用 App Router / TypeScript / Tailwind 4 / shadcn/ui 等功能完全兼容

---

## 0. 文档读法

本文档面向前端开发与设计，按「技术栈 → 路由 → 各页详述（数据契约 + wireframe + 交互） → 组件 → 状态管理 → 表单 → 设计规范 → UX 细节 → 测试」九节描述。每个页面必描述「URL/数据来源/Loading & 错误态/交互细节/验收标准」。

---

## 1. 技术栈

| 维度 | 选型 |
|------|------|
| 框架 | Next.js 16 (App Router) |
| 语言 | TypeScript (strict) |
| 样式 | Tailwind CSS 4 |
| 组件库 | shadcn/ui (Radix 内核) |
| 图表 | Recharts |
| 数据请求 | TanStack Query (v5) |
| 表单 | React Hook Form + Zod |
| 时间处理 | date-fns (浏览器侧 UTC → 本地化) |
| 图标 | lucide-react |
| HTTP 客户端 | fetch + 轻封装 (`lib/api.ts`) |
| 测试 | Vitest + React Testing Library（关键组件） |
| Lint | ESLint + Prettier（默认配置） |

**架构约束**：
- 仅 Client Components（`"use client"`，简化 v1，不引入 RSC fetch / streaming）
- 全部 API 调用走 `lib/api.ts` 统一封装，不在组件直 fetch
- 路由独立分页，无嵌套布局（除全站顶栏外）
- 不引入 Redux/Zustand 等全局状态（TanStack Query 管服务态足够）

---

## 2. 目录结构

```
frontend/
├── package.json
├── next.config.js
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── .env.local                       # NEXT_PUBLIC_API_BASE
├── app/
│   ├── layout.tsx                   # 全站布局（顶部导航 + Toast）
│   ├── page.tsx                     # → redirect /dashboard
│   ├── globals.css
│   ├── dashboard/
│   │   └── page.tsx
│   ├── markets/
│   │   └── [id]/
│   │       └── page.tsx
│   ├── predict/
│   │   └── page.tsx
│   ├── history/
│   │   └── page.tsx
│   └── settings/
│       └── page.tsx
├── components/
│   ├── ui/                          # shadcn/ui 生成
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── input.tsx
│   │   ├── form.tsx
│   │   ├── select.tsx
│   │   ├── switch.tsx
│   │   ├── dialog.tsx
│   │   ├── toast.tsx
│   │   └── table.tsx
│   ├── navbar.tsx
│   ├── market-card.tsx
│   ├── state-badge.tsx
│   ├── signal-kind-badge.tsx
│   ├── price-chart.tsx              # p_ai vs p_mkt 双线
│   ├── prediction-card.tsx
│   ├── prediction-timeline.tsx
│   ├── signal-timeline.tsx
│   ├── kpi-tile.tsx
│   ├── time-ago.tsx
│   ├── countdown.tsx
│   ├── threshold-form.tsx
│   ├── discovery-form.tsx
│   ├── ai-model-form.tsx
│   ├── feishu-form.tsx
│   ├── scheduler-status-table.tsx
│   ├── data-maintenance-panel.tsx
│   └── empty-state.tsx
├── lib/
│   ├── api.ts                       # fetch 封装 + 错误转 toast
│   ├── format.ts                    # 数字/百分比/时间格式化
│   ├── time.ts                      # UTC ↔ 本地化
│   └── schemas.ts                   # Zod schema（与后端 Pydantic 对齐）
├── hooks/
│   ├── use-markets.ts               # TanStack Query hooks
│   ├── use-market.ts
│   ├── use-predictions.ts
│   ├── use-signals.ts
│   ├── use-settings.ts
│   └── use-scheduler.ts
└── tests/
    └── components/
```

---

## 3. 全站布局

### 3.1 顶部导航 (`components/navbar.tsx`)

```
┌───────────────────────────────────────────────────────────────┐
│  ₿ BTC 套利信号  │ 仪表盘 · 手动预测 · 推送历史 · 设置  │ ⚙ │
└───────────────────────────────────────────────────────────────┘
```

- 左侧 logo + 项目名（点击回 /dashboard）
- 中间 4 个一级导航（高亮当前路由）
- 右侧调度状态指示灯（绿/黄/红，悬停显示「最近一次 daily_discovery: 2h ago」）
- 高度固定 56px，sticky top，浅灰边框底部 1px

### 3.2 全局错误 Toast

- 任何 API 4xx/5xx 经 `lib/api.ts` 统一拦截 → 弹 Toast（右下角）
- Toast 内容：`code` + `message`（中文）
- 5 秒后自动消失，可手动关闭

### 3.3 风险声明

- footer 一行小字：「本工具仅作个人研究信号提醒，不构成投资建议」

---

## 4. 页面详述

### 4.1 `/dashboard` — 仪表盘

**目标**：一屏看完当前所有监控市场状态 + 关键 KPI。

**数据源**：
- `GET /api/v1/markets?state=WATCHING,ENTERED_LONG,ENTERED_SHORT` (排除 EXPIRED)
- `GET /api/v1/signals?from=今天 00:00 UTC` (今日推送数)
- `GET /api/v1/scheduler/jobs` (下次 daily_discovery 时间)

**Wireframe**：

```
┌──────────────────────────────────────────────────────────────────────────┐
│  KPI Row (4 tiles)                                                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ 监控中    │ │ 今日发现  │ │ 今日推送  │ │ 未推送(红)│                    │
│  │  23      │ │   5      │ │   3      │ │    0      │                    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                    │
│                                                                          │
│  筛选 [全部 ▼] [全部状态 ▼]    [+ 手动添加 → /predict]    [刷新 ↻]      │
│                                                                          │
│  Market Cards Grid (3 列响应式)                                          │
│  ┌────────────────────────────┐  ┌────────────────────────────┐         │
│  │ [ENTERED_LONG 橙] [手动]    │  │ [WATCHING 灰] [自动发现]    │         │
│  │ Bitcoin above $108K May17  │  │ Bitcoin above $110K May20  │         │
│  │                             │  │                             │         │
│  │  AI 0.72   →  Market 0.55   │  │  AI 0.45   →  Market 0.48   │         │
│  │           gap +0.17         │  │           gap -0.03         │         │
│  │                             │  │                             │         │
│  │  ⏱ 剩 8h 23m                │  │  ⏱ 剩 3d 5h                 │         │
│  │  Updated 2m ago             │  │  Updated 4m ago             │         │
│  │                             │  │                             │         │
│  │  [详情] [Polymarket ↗]      │  │  [详情] [Polymarket ↗]      │         │
│  └────────────────────────────┘  └────────────────────────────┘         │
│  ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

**交互**：
- 每 30 秒 TanStack Query 自动 refetch（`refetchInterval: 30_000`）
- 卡片整体可点 → 跳 `/markets/[id]`
- 「Polymarket ↗」新开标签到 `https://polymarket.com/event/{slug}`
- 「刷新」按钮手动触发 refetch + 旋转图标 1s
- 筛选下拉变化时改 query → 自动重新拉
- 距结算 < 1h 的卡片右上角加「临近结算」徽章（蓝紫色）
- `metadata.stale=true` 的卡片整张灰显 + 悬停 tooltip「价格数据异常」

**Loading & 错误态**：
- 首次加载：6 张骨架卡片
- 拉取失败：顶部 banner「无法连接后端，请检查服务运行状态」+ 重试按钮
- 数据为 0：EmptyState 组件「还没有在监控的市场。手动添加 →」按钮跳 `/predict`

**验收标准**：
- 拉取 100 个市场时首屏 < 1s（本地）
- 每 30 秒自动刷新无视觉抖动（用 TanStack Query placeholderData 平滑过渡）
- 状态徽章颜色与卡片左边框颜色一致（见 §6 色板）

---

### 4.2 `/markets/[id]` — 市场详情

**目标**：单市场全貌：价格走势、预测演化、推送事件、原始数据。

**数据源**：
- `GET /api/v1/markets/{id}` (含 latest_prediction + latest_price)
- `GET /api/v1/markets/{id}/price_ticks?from=14天前&granularity=hourly`
- `GET /api/v1/markets/{id}/predictions`
- `GET /api/v1/signals?market_id={id}`

**Wireframe**：

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ← 返回仪表盘                                                            │
│                                                                          │
│  Bitcoin above $108,000 on May 17?              [ENTERED_LONG]  [手动添加]│
│  ⏱ 结算 2026-05-17 12:00 UTC (剩 8h 23m)                                  │
│  ⚙ Polymarket ↗   condition_id: 0x...                                    │
│                                                                          │
│  ╔════════════════════════════════════════════════════════════════════╗  │
│  ║  价格走势（双线 14 天）                                              ║  │
│  ║                                                                    ║  │
│  ║    1.0 │                                                           ║  │
│  ║        │              ╭─────●  AI 0.72                              ║  │
│  ║    0.5 │     ____●────╯                                            ║  │
│  ║        │   ─●─                  Market 0.55                       ║  │
│  ║    0.0 │_______________________________________________________     ║  │
│  ║         5/3   5/5   5/7   5/9   5/11  5/13  5/15  now              ║  │
│  ║                                                                    ║  │
│  ║  ● AI 预测  ● Market YES 价格        [立即重跑预测]                  ║  │
│  ╚════════════════════════════════════════════════════════════════════╝  │
│                                                                          │
│  ┌─────────────────────────┐  ┌────────────────────────────────────┐   │
│  │ 当前预测 (Prediction)    │  │ 信号事件时间线 (倒序)               │   │
│  │                         │  │                                     │   │
│  │ AI 概率   0.72          │  │ ━━ 2026-05-15 08:35  ENTRY_LONG ✅ │   │
│  │ 量化基础   0.68          │  │    WATCHING → ENTERED_LONG          │   │
│  │ LLM 调整  +0.04          │  │    gap +0.17                        │   │
│  │ 置信度    medium         │  │    飞书已推                          │   │
│  │ 模型      quant-v1+gpt-5│  │                                     │   │
│  │                         │  │ ━━ 2026-05-12 15:20  EXIT_SHORT ✅ │   │
│  │ LLM 理由 (点击展开 ▼)   │  │    ENTERED_SHORT → WATCHING         │   │
│  │ 近期 BTC 价格突破历史... │  │    ...                              │   │
│  │                         │  │                                     │   │
│  │ 参考新闻 (3 条 ▼)       │  │                                     │   │
│  └─────────────────────────┘  └────────────────────────────────────┘   │
│                                                                          │
│  ╔════════════════════════════════════════════════════════════════════╗  │
│  ║  预测历史 (按时间倒序，每条可展开看完整 LLM 理由与新闻源)            ║  │
│  ╚════════════════════════════════════════════════════════════════════╝  │
└──────────────────────────────────────────────────────────────────────────┘
```

**关键组件**：
- `<PriceChart predictions={...} ticks={...} />` Recharts LineChart，两条 line（AI 阶梯线，Market 平滑线）；x 轴时间，y 轴 0–1；hover 显示十字线 + tooltip
- `<PredictionCard prediction={latest} />`
- `<SignalTimeline signals={signals} />`
- `<PredictionTimeline predictions={predictions} />` 折叠列表，每条卡片含 LLM 理由 + 新闻列表（点击新闻跳出去）

**交互**：
- 「立即重跑预测」按钮 → `POST /api/v1/markets/{id}/repredict` → 成功后 refetch 当前页 + Toast「预测已更新」
- 「Polymarket ↗」新开 polymarket.com 对应 event
- 每 30 秒 refetch（与仪表盘节奏一致）
- 删除市场按钮（右上角小垃圾桶）→ 弹确认 → `DELETE /api/v1/markets/{id}` → 跳回 /dashboard

**Loading & 错误态**：
- 首次加载：每个 section 骨架
- market 不存在：404 页

**验收标准**：
- 14 天 hourly 数据点（≤ 336 条）+ 多条 prediction 渲染 < 1s
- 双线图悬停时两条 series 同时高亮 tooltip
- LLM 理由折叠默认收起，避免首屏太挤

---

### 4.3 `/predict` — 手动预测

**目标**：贴 URL → 试一次 → 决定是否加入监控。

**数据源**：
- `POST /api/v1/predict` (不入库，仅算结果)
- `POST /api/v1/markets` (入库 + 加监控)

**Wireframe**：

```
┌──────────────────────────────────────────────────────────────────────────┐
│  手动预测                                                                │
│                                                                          │
│  贴 Polymarket 市场链接，AI 会算 YES 概率并告诉你模型理由。              │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │ https://polymarket.com/event/bitcoin-above-on-may-17     │ [试一次]  │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                          │
│  ╔════════════════════════════════════════════════════════════════════╗  │
│  ║  预测结果                                                           ║  │
│  ║                                                                    ║  │
│  ║  Bitcoin above $108,000 on May 17?                                ║  │
│  ║  结算: 2026-05-17 12:00 UTC (剩 8h)                                ║  │
│  ║                                                                    ║  │
│  ║  AI 概率                                                           ║  │
│  ║  ┌─────────────────────────────┐ 72%                              ║  │
│  ║  └─────────────────────────────┘                                   ║  │
│  ║                                                                    ║  │
│  ║  量化基础     0.68    BTC 现货 $107,500    年化波动率 45%           ║  │
│  ║  LLM 调整    +0.04    置信度 medium                                ║  │
│  ║                                                                    ║  │
│  ║  ▼ LLM 理由                                                        ║  │
│  ║    近期 BTC 价格突破历史新高，市场情绪偏...                          ║  │
│  ║                                                                    ║  │
│  ║  ▼ 参考新闻 (3 条)                                                 ║  │
│  ║    1. [Bitcoin Surges Past...] coindesk.com                       ║  │
│  ║    2. ...                                                          ║  │
│  ║                                                                    ║  │
│  ║                                          [+ 加入监控并定时跟踪]    ║  │
│  ╚════════════════════════════════════════════════════════════════════╝  │
└──────────────────────────────────────────────────────────────────────────┘
```

**交互**：
- URL 输入框 + Zod 校验：必须是 polymarket.com 域名 + 路径含 `/event/` 或 `/market/`，否则前端 inline 错误
- 「试一次」按钮：调 `POST /predict`，loading 期间按钮变 spinner，下方显示骨架
- 结果显示后「加入监控并定时跟踪」按钮：调 `POST /markets`，成功后 Toast「已加入监控」+ 跳 `/markets/{new_id}`
- 错误（422 各种码）→ Toast + 输入框下方 inline 错误信息（红字）

**验收标准**：
- 输入合法 URL + 后端正常时，「试一次」完成时间 ≤ 30s（受 OpenAI + Tavily 影响）
- 输入非法 URL 立即前端校验拒绝，不发请求
- 已加入监控的市场再点「加入监控」返回 409 → Toast「该市场已存在，点击跳转」并提供链接

---

### 4.4 `/history` — 推送历史

**目标**：浏览所有信号事件，按维度筛选与复盘。

**数据源**：
- `GET /api/v1/signals?kind=...&market_id=...&from=...&to=...&limit=100`

**Wireframe**：

```
┌──────────────────────────────────────────────────────────────────────────┐
│  推送历史                                                                │
│                                                                          │
│  筛选: [全部类型 ▼] [全部市场 ▼] [近 7 天 ▼] [全部状态 ▼]   [导出 CSV]   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ 时间        │ 类型          │ 市场              │ 价差   │ 推送 │    │
│  ├─────────────┼───────────────┼───────────────────┼────────┼──────┤    │
│  │ 5/15 08:35  │ ENTRY_LONG 🟠 │ BTC above $108K   │ +0.17  │ ✅   │    │
│  │ 5/14 22:10  │ EXIT_SHORT ✅ │ BTC above $110K   │ -0.02  │ ✅   │    │
│  │ 5/14 15:00  │ ENTRY_SHORT 🔴│ BTC above $112K   │ -0.15  │ ⚠ 失败│    │
│  │ ...                                                                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  分页: ← 上一页  1/12  下一页 →                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**交互**：
- 行点击展开侧栏（Dialog 半屏）显示完整 signal_event 详情：完整 prediction 快照、推送时间、错误信息、卡片预览
- 筛选条件变化 → 自动 refetch
- 「导出 CSV」按钮：前端直接把当前筛选结果转 CSV 下载（不调后端额外接口）
- 推送失败行：右侧加「重试」按钮，调 `POST /signals/{id}/retry`（v1 未必实现这个接口，UI 上预留但灰显）→ 改为「等待自动重试」提示
- 分页：标准前后页按钮 + 「跳转到」输入框

**验收标准**：
- 50 条数据一页渲染 < 200ms
- 时间筛选支持「今天」「近 7 天」「近 30 天」「自定义区间（DatePicker）」

---

### 4.5 `/settings` — 设置

**目标**：单页所有配置 + 验证按钮。

**数据源**：
- `GET /api/v1/settings`
- `PATCH /api/v1/settings`
- `POST /api/v1/settings/test_feishu`
- `GET /api/v1/scheduler/jobs`
- `POST /api/v1/scheduler/trigger`

**Wireframe**：

```
┌──────────────────────────────────────────────────────────────────────────┐
│  设置                                                                    │
│                                                                          │
│  ╔════════════════════════════════════════════════════════════════════╗  │
│  ║ ① 监控参数                                                          ║  │
│  ║   入场阈值 (entry_threshold)    [0.150]  (0.01–0.50)                ║  │
│  ║   去抖窗口 (debounce_minutes)   [10] 分钟  (≥1)                     ║  │
│  ║   价格轮询 (price_poll_minutes) [5] 分钟  (≥1)                      ║  │
│  ║   AI 重预测 (predict_ttl_hours) [24] 小时 (≥1)                      ║  │
│  ║                                                  [保存]             ║  │
│  ╚════════════════════════════════════════════════════════════════════╝  │
│                                                                          │
│  ╔════════════════════════════════════════════════════════════════════╗  │
│  ║ ② 发现规则                                                          ║  │
│  ║   关键词 (discovery_keywords)   [bitcoin] [btc] [+ 添加]            ║  │
│  ║   最大到期天数 (max_days)        [30]                                ║  │
│  ║                                                  [保存]             ║  │
│  ╚════════════════════════════════════════════════════════════════════╝  │
│                                                                          │
│  ╔════════════════════════════════════════════════════════════════════╗  │
│  ║ ③ AI 模型                                                           ║  │
│  ║   OpenAI API Key   [sk-...***hidden***]   [修改]                    ║  │
│  ║   OpenAI Model     [gpt-5 ▼]                                        ║  │
│  ║   Web 搜索 Provider [tavily ▼]                                      ║  │
│  ║   Web 搜索 API Key [tvly-...***hidden***] [修改]                    ║  │
│  ║                                                  [保存]             ║  │
│  ╚════════════════════════════════════════════════════════════════════╝  │
│                                                                          │
│  ╔════════════════════════════════════════════════════════════════════╗  │
│  ║ ④ 飞书推送                                                          ║  │
│  ║   Webhook URL  [https://open.feishu.cn/...***hidden***]  [修改]     ║  │
│  ║                                       [发送测试卡片]  [保存]        ║  │
│  ╚════════════════════════════════════════════════════════════════════╝  │
│                                                                          │
│  ╔════════════════════════════════════════════════════════════════════╗  │
│  ║ ⑤ 调度状态                                                          ║  │
│  ║                                                                    ║  │
│  ║   ✅ daily_discovery       下次: 2026-05-16 00:00 UTC  [手动触发]   ║  │
│  ║   ✅ price_poll           下次: 5 分钟后              [手动触发]   ║  │
│  ║   ✅ ai_repredict_check   下次: 47 分钟后             [手动触发]   ║  │
│  ║   ✅ feishu_retry         下次: 8 分钟后              [手动触发]   ║  │
│  ║   ✅ price_tick_cleanup   下次: 明日 03:00 UTC                       ║  │
│  ║                                                                    ║  │
│  ║   最近运行: [展开看 job_run 表 ▼]                                   ║  │
│  ╚════════════════════════════════════════════════════════════════════╝  │
│                                                                          │
│  ╔════════════════════════════════════════════════════════════════════╗  │
│  ║ ⑥ 数据维护                                                          ║  │
│  ║   清理 30 天前 price_tick    [立即清理]                              ║  │
│  ║   导出 signal_event CSV     [下载]                                   ║  │
│  ║   危险区: 重置所有市场为 WATCHING  [需二次确认]                       ║  │
│  ╚════════════════════════════════════════════════════════════════════╝  │
└──────────────────────────────────────────────────────────────────────────┘
```

**交互**：
- 每个表单 section 独立保存按钮（局部 patch，不一锅端）
- 输入越界（如 entry_threshold = 0.8）：前端 Zod 校验 inline 错误，禁用「保存」
- 密钥字段默认 masked + 「修改」按钮 → 切换为输入框（输入会覆盖原值）
- 「发送测试卡片」→ POST /test_feishu → Toast「✅ 飞书可达」/「❌ 失败: <reason>」
- 「手动触发」→ `POST /scheduler/trigger` → Toast「已加入队列」+ 5 秒后自动展开「最近运行」section
- 「立即清理」→ Dialog 确认 → 调 cleanup（v1 后端可不开独立接口，复用 trigger）
- 「重置所有市场为 WATCHING」→ Dialog 双重确认 + 大红警告：「这会清空所有状态机进度，确定吗？」→ 调 PATCH 或专门接口（v1 可手工 DB 操作，UI 上预留按钮但提示「该功能待开发」）

**验收标准**：
- 每个 section 保存后立即生效（前端调 PATCH，后端 60s 内对调度生效，无需重启）
- 密钥从未在前端 console 或 DOM 中明文显示（masked 值由后端给）
- 表单字段与后端 setting 表字段名一一对应，不发明前端独有字段

---

## 5. 公共组件库

### 5.1 视觉/数据组件

| 组件 | 输入 | 输出 |
|------|------|------|
| `<StateBadge state />` | `'WATCHING' \| ...` | 圆角徽章 + 色板对应背景 |
| `<SignalKindBadge kind />` | `'ENTRY_LONG' \| ...` | 同上 |
| `<MarketCard market />` | `MarketWithLatest` | 仪表盘卡片 |
| `<PriceChart predictions ticks />` | 两个数组 | Recharts 双线 LineChart |
| `<PredictionCard prediction />` | `Prediction` | 详情页右上小卡 |
| `<PredictionTimeline predictions />` | `Prediction[]` | 可折叠列表 |
| `<SignalTimeline signals />` | `SignalEvent[]` | 同上 |
| `<KpiTile label value tone? />` | `string, string, 'default'\|'danger'` | 仪表盘大数字 tile |
| `<TimeAgo timestamp />` | ISO string | 「2m ago」自动每 30s 刷新 |
| `<Countdown to />` | ISO string | 「剩 8h 23m」每 60s 刷新 |
| `<EmptyState title cta />` | `{title, cta?}` | 占位插画 + 行动按钮 |

### 5.2 表单组件

| 组件 | 用途 |
|------|------|
| `<ThresholdForm />` | 监控参数 section |
| `<DiscoveryForm />` | 发现规则 section |
| `<AiModelForm />` | AI 模型 section |
| `<FeishuForm />` | 飞书 section |
| `<SchedulerStatusTable />` | 调度状态 section |
| `<DataMaintenancePanel />` | 数据维护 section |

### 5.3 命名约定

- `components/ui/*`：shadcn 生成的原子组件，不改源码
- `components/*.tsx`：业务组件，PascalCase
- `hooks/use-*.ts`：TanStack Query hooks，每个一文件
- `lib/api.ts`：所有 fetch 调用入口（自带 throw + Toast）

---

## 6. 设计规范

### 6.1 色板

主色（Tailwind 类）：
- 主背景: `bg-slate-50`
- 卡片: `bg-white border border-slate-200`
- 主操作: `bg-emerald-600 hover:bg-emerald-700`
- 次操作: `bg-slate-100 hover:bg-slate-200`

状态色：
- `WATCHING`: `bg-slate-100 text-slate-700` (灰)
- `ENTERED_LONG`: `bg-amber-100 text-amber-800 border-l-4 border-amber-500` (橙)
- `ENTERED_SHORT`: `bg-rose-100 text-rose-800 border-l-4 border-rose-500` (红)
- `EXPIRED`: `bg-slate-200 text-slate-500 opacity-60` (淡灰)
- 临近结算徽章: `bg-violet-100 text-violet-800`

信号类型色（与状态色保持视觉一致）：
- `ENTRY_LONG`: 🟠 amber
- `ENTRY_SHORT`: 🔴 rose
- `EXIT_LONG`: ✅ emerald
- `EXIT_SHORT`: ✅ emerald
- `EXPIRED`: ⚪ slate

KPI 危险色: `text-rose-600 font-semibold`

### 6.2 间距

- 卡片内边距: `p-6`
- 卡片间距: `gap-4`
- section 之间: `space-y-8`
- 顶部页面容器最大宽度: `max-w-7xl mx-auto px-6 py-8`

### 6.3 字体

- 标题: `text-2xl font-semibold` / `text-xl font-semibold`
- 主体: `text-sm`
- 数字: 等宽字体（`font-mono` + tabular-nums）
- 图表 tooltip: `text-xs`

### 6.4 图表样式

Recharts LineChart：
- AI 线：amber-500，2.5px 实线，阶梯插值（`type="stepAfter"`，反映 24h 重跑离散性）
- Market 线：blue-500，1.5px 平滑线
- 网格：浅灰 dashed
- y 轴固定 0–1，5 个 tick (0/0.25/0.5/0.75/1)
- x 轴时间格式 `MM/dd HH:mm`（浏览器本地化）
- Tooltip 同时显示两条 series + 价差

---

## 7. UX 细节

### 7.1 时间显示

- 列表页相对时间（`<TimeAgo />`）
- 详情页绝对时间 + 相对时间 tooltip
- 所有时间显示用浏览器本地化（`Intl.DateTimeFormat`），但 hover tooltip 显示 UTC 原值
- 倒计时（`<Countdown />`）每 60s 刷新一次

### 7.2 自动刷新

- 仪表盘 & 详情页：30s refetch
- 历史页：手动刷新（避免破坏分页/筛选状态）
- 设置页：仅保存后 refetch
- 不引 WebSocket（v1 简单优先）

### 7.3 Loading

- 首次加载：骨架屏（每页针对性骨架，不用通用 spinner）
- 二次加载（refetch）：TanStack Query `placeholderData: keepPreviousData`，无视觉抖动
- 按钮操作 loading：按钮内 spinner + 禁用，不全屏遮罩

### 7.4 错误展示

- API 4xx/5xx：右下角 Toast
- 表单错误：inline 红字（字段下方）
- 全站不可用（连续多次失败）：顶部 banner 红条 + 调试链接到 /settings 调度状态

### 7.5 删除/危险操作

- 删除市场：Dialog 二次确认，标红按钮
- 重置状态机：Dialog 双重确认（先勾选「我理解风险」再点按钮）

### 7.6 移动端

- v1 不针对移动端优化，但 Tailwind 响应式断点自动让仪表盘从 3 列变 1 列、表格横向滚动；最低支持 768px 宽
- iPad/横屏可用，手机端「能看」但不「好用」

---

## 8. API 封装与状态管理

### 8.1 `lib/api.ts`

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

export class ApiError extends Error {
  constructor(public code: string, message: string, public details?: unknown, public status?: number) {
    super(message);
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: { code: "UNKNOWN", message: res.statusText } }));
    throw new ApiError(body.error?.code ?? "UNKNOWN", body.error?.message ?? "Unknown error", body.error?.details, res.status);
  }
  return res.json();
}
```

- 所有 hooks 走 apiFetch
- 全局 `QueryClient` 配置 `onError`：捕 `ApiError` 弹 Toast
- 404 不弹 Toast（页面自己处理）

### 8.2 TanStack Query hooks 例

```typescript
// hooks/use-markets.ts
export function useMarkets(params: MarketFilter) {
  return useQuery({
    queryKey: ["markets", params],
    queryFn: () => apiFetch<MarketListResponse>(`/markets?${qs(params)}`),
    refetchInterval: 30_000,
    placeholderData: keepPreviousData,
  });
}
```

### 8.3 Mutation

```typescript
export function useAddMarket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (url: string) => apiFetch("/markets", { method: "POST", body: JSON.stringify({ polymarket_url: url }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["markets"] }),
  });
}
```

---

## 9. 表单与校验（Zod schema 与后端对齐）

```typescript
// lib/schemas.ts
export const SettingPatchSchema = z.object({
  entry_threshold: z.number().min(0.01).max(0.50).optional(),
  debounce_minutes: z.number().int().min(1).optional(),
  price_poll_minutes: z.number().int().min(1).optional(),
  predict_ttl_hours: z.number().int().min(1).optional(),
  discovery_keywords: z.array(z.string()).min(1).optional(),
  discovery_max_days_to_resolve: z.number().int().min(1).max(365).optional(),
  feishu_webhook_url: z.string().url().optional(),
  openai_api_key: z.string().min(1).optional(),
  openai_model: z.string().min(1).optional(),
  web_search_provider: z.enum(["tavily", "exa", "brave", "openai"]).optional(),
  web_search_api_key: z.string().min(1).optional(),
});

export const PolymarketUrlSchema = z.string()
  .url()
  .refine(u => new URL(u).host.endsWith("polymarket.com"))
  .refine(u => /\/(event|market)\//.test(new URL(u).pathname), "URL 必须包含 /event/ 或 /market/");
```

- 与 backend Pydantic schema 由人工同步（无 OpenAPI 自动生成，v1 简化）
- 后端是真相源，前端校验只为提前阻断明显错误

---

## 10. 测试策略

### 10.1 单元/组件测试（Vitest + RTL）

| 测试 | 用例 |
|------|------|
| `<PriceChart />` | mock 数据渲染、y 轴范围、空数据态 |
| `<StateBadge />` | 4 种状态颜色与文案 |
| `<MarketCard />` | gap 正/负/0、临近结算、stale 灰显 |
| `<ThresholdForm />` | 越界校验、保存调用 mutation |
| `<FeishuForm />` | 测试卡片按钮触发 mutation |
| `apiFetch` | 4xx/5xx 抛 ApiError；2xx 解析 JSON |
| `PolymarketUrlSchema` | 各种 URL 形态通过/拒绝 |

覆盖率目标 ≥ 60%（关键组件 ≥ 80%）。

### 10.2 手动验收清单

`docs/qa-checklist.md`（实现期补）：
1. 仪表盘加载、KPI 准确、卡片样式正确
2. 手动添加合法/非法 URL
3. 详情页双线图、重跑预测
4. 设置页所有 section 保存生效
5. 测试卡片实际收到飞书
6. 删除市场、跳转 Polymarket
7. 推送历史筛选 + CSV 下载
8. 调度状态展示与手动触发

### 10.3 不做

- Playwright E2E
- 视觉回归测试
- 浏览器矩阵覆盖（默认 Chrome 最新版）

---

## 11. 性能与可访问性

### 11.1 性能

- 路由分页（next/dynamic 不强需，但首屏 < 100KB JS）
- 图表数据点限制：detail 页最多 720 个 tick（30 天 hourly），超出走聚合
- 列表分页：history 默认 50 / 页
- 不引 SSR（个人本地工具，无 SEO 价值）

### 11.2 可访问性

- 颜色对比度 ≥ AA（4.5:1，状态徽章已校验）
- 所有按钮带 `aria-label`
- 表单 label 与 input 关联
- 键盘 Tab 顺序合理（顶栏 → 主内容 → 操作按钮）
- 不强制 ARIA Live 区域（个人使用范围）

---

## 12. 开发与构建

### 12.1 本地开发

```bash
cd frontend
pnpm install
pnpm dev   # http://localhost:3000
```

`.env.local`：
```
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
```

### 12.2 Docker 构建

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM node:22-alpine AS runtime
WORKDIR /app
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./
ENV NODE_ENV=production
EXPOSE 3000
CMD ["pnpm", "start"]
```

### 12.3 Lint & Format

```bash
pnpm lint       # next lint (eslint)
pnpm typecheck  # tsc --noEmit
pnpm format     # prettier --write
```

---

文档结束。后端实现见 `backend-PRD.md`，产品需求见 `PRD.md`。
