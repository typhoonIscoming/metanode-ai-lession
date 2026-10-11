# Polymarket BTC 套利信号工具

> 课程视频回放（Lesson 9）：[点击观看](https://appibxs98ig9955.h5.xet.pomoho.com/p/course/video/v_6a2b06c1e4b0694c5bd52a5d?product_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&course_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&sub_course_id=subcourse_3EUmreviThPpAUC2IJ1NTqoDbk5)

> **Lesson 9 · AI 驱动的软件开发提效实战课**
> 用 Claude Code Agent Team 模式从 0 到 1 vibe-coded 出来的一个完整产品
>
> ⚠️ **风险声明**：本工具仅作个人研究与信号提醒，不构成投资建议。预测市场涉及资金与合规风险，参与前请阅读 Polymarket 官方规则并自行判断地缘合规。

---

## 目录

1. [这是什么](#1-这是什么)
2. [核心功能](#2-核心功能)
3. [系统架构](#3-系统架构)
4. [技术栈](#4-技术栈)
5. [快速开始（含密钥申请指南）](#5-快速开始)
6. [配置详解](#6-配置详解)
7. [使用指南](#7-使用指南)
8. [项目结构](#8-项目结构)
9. [关键概念](#9-关键概念)
10. [调度任务节奏](#10-调度任务节奏)
11. [常见问题与故障排查](#11-常见问题与故障排查)
12. [Vibe Coding 复盘：Claude Agent Team 模式](#12-vibe-coding-复盘claude-agent-team-模式)
13. [后续工作](#13-后续工作)

---

## 1. 这是什么

一个**本地跑、面向个人交易者**的 Polymarket BTC 价格预测市场套利信号工具。

```
后端定时发现 BTC 相关市场
    → 量化模型 (对数正态) 给出基础概率
    → LLM 读市场上下文做调整
    → 与 Polymarket 实时市场价比对
    → 状态机判定 ENTRY / EXIT 信号
    → 飞书机器人推送卡片
```

### 价值主张

| 痛点 | 我们的价值 |
|------|-----------|
| Polymarket 上 BTC 相关市场分散，手动盯盘成本高 | **每天自动发现** + 按规则筛选活跃市场 |
| 「市场价是真概率吗」难以判断 | **量化基础 + LLM 调整**，可解释、可追溯 |
| 即使发现错价也容易错过价格回归窗口 | **实时轮询 + 状态机**，错价出现/兑现都不漏 |
| 想跟踪多个市场但又怕被噪音骚扰 | **入场阈值 + 去抖窗口 + 临近结算停推**三重过滤 |

---

## 2. 核心功能

### Backend（FastAPI + APScheduler + Postgres）

- 🔎 **每日 BTC discovery**：每天 UTC 00:30 自动追今天 + 2 天的 `bitcoin-above-on-{date}` event，挑出 YES 中价最接近 50% 的那个子市场入库（套利信息量最大）
- 🤖 **AI 预测引擎**：对数正态模型给基础概率 → AIHubMix LLM 微调 → 套利偏向保证 `|p_ai - p_mkt| ≥ 20pp`
- 📈 **价格监控**：每 5 分钟拉一次 Polymarket CLOB midpoint
- 🔔 **信号引擎**：4 态状态机（WATCHING / ENTERED_LONG / ENTERED_SHORT / EXPIRED）+ 去抖窗口 + ε 滞回带 + EXPIRED 优先
- 📲 **飞书推送**：interactive card，按钮直链 Polymarket 真页（event slug）；webhook 未配自动 dry-run
- 🔧 **/predict 手动**：贴 Polymarket URL（支持 event 集合自动选最接近 50%） → 量化 + LLM 预测；可选「加入监控并推送」直接入库 + 跑信号 + 真推飞书

### Frontend（Next.js 16 Turbopack + Tailwind 4 + shadcn）

| 页面 | 内容 |
|---|---|
| `/dashboard` | 4 KPI 卡（总市场 / 活跃 / 入场中 / 24h 推送）+ 最近信号表 + 监控中的市场列表 |
| `/predict` | URL 输入 + 「试一次（dry-run）」+「加入监控并推送」双按钮，event 自动选 50% 子市场 |
| `/history` | 信号事件全量 + 5 种 kind 筛选 + CSV 导出 |
| `/settings` | 信号引擎参数 / 市场发现 / 飞书 / LLM 4 分组表单 + 飞书测试卡片按钮 |
| `/markets/[id]` | recharts 双线折线（AI 概率 vs 市场价）+ 最新预测 LLM rationale + 本市场信号历史 + Polymarket 外链 |

UI 风格：深色 "Bloomberg-style" 交易终端 —— glass-card、橙紫渐变、状态徽章带辉光、信号 gap 红绿粗体。

---

## 3. 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Polymarket Gamma + CLOB   Binance Spot+Klines   AIHubMix (gpt-5.5)     │
└─────────────────────────────────────────────────────────────────────────┘
         │                      │                          │
         ▼                      ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            Backend (FastAPI)                            │
│  ┌───────────┐  ┌───────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ adapters/ │  │ services/ │  │ scheduler/   │  │ routers/          │  │
│  │ polymarket│→ │ discovery │→ │ APScheduler  │→ │ /markets /signals │  │
│  │ binance   │  │ prediction│  │  - discover  │  │ /predict /settings│  │
│  │ openai    │  │ quant     │  │  - predict   │  │ /scheduler /health│  │
│  │ feishu    │  │ price_mon │  │  - poll      │  │                   │  │
│  └───────────┘  │ signal    │  │  - signal    │  └───────────────────┘  │
│                 │ notify    │  │    +notify   │           │             │
│                 └───────────┘  └──────────────┘           │             │
│                       │                                   │             │
│                       ▼                                   ▼             │
│              ┌──────────────────┐                ┌─────────────────┐    │
│              │ Postgres (16)    │                │ 飞书 Webhook    │    │
│              │  market          │                │  interactive    │    │
│              │  prediction      │                │  card with link │    │
│              │  price_tick      │                └─────────────────┘    │
│              │  signal_event    │                                       │
│              │  setting         │                                       │
│              │  job_run         │                                       │
│              └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ /api/v1/*
                              │
┌─────────────────────────────────────────────────────────────────────────┐
│                       Frontend (Next.js 16)                             │
│   /dashboard  /predict  /history  /settings  /markets/[id]              │
│   TanStack Query + Zod 镜像 backend Pydantic schemas                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 技术栈

| 层 | 技术 | 备注 |
|---|---|---|
| Backend | Python 3.12 | |
| | FastAPI 0.115 | + uvicorn[standard] |
| | SQLAlchemy 2.0 async + asyncpg | |
| | Alembic | 一次 initial schema migration |
| | APScheduler 3 | AsyncIOScheduler，4 个 job |
| | httpx 0.27 | 所有外部 HTTP |
| | structlog | JSON 结构化日志 |
| | scipy.stats.norm | 对数正态 CDF |
| | OpenAI 兼容 SDK 模式 | 直接用 httpx 调 AIHubMix |
| Frontend | Next.js 16 (App Router + Turbopack) | ⚠️ 不是你熟悉的 Next |
| | TypeScript strict | |
| | Tailwind 4 + shadcn/ui | 深色配色 |
| | TanStack Query v5 | 30s 自动 refetch |
| | Recharts | 价格走势折线 |
| | Zod | 与 Pydantic schemas 人工镜像 |
| | sonner | Toast 通知（dark theme） |
| 基础设施 | Postgres 16 | docker-compose |
| | docker-compose | 一键起 db + backend + frontend |

---

## 5. 快速开始

### 5.1 前置依赖

| 工具 | 版本 | 用途 |
|---|---|---|
| Docker + Docker Compose | 任意现代版本 | 起 Postgres（+ 可选起 backend/frontend） |
| Python | 3.12+ | 跑 backend |
| Node.js | 22+ | 跑 frontend |
| pnpm | 9+ | frontend 依赖管理 |
| (可选) WSL2 | | Windows 上推荐 |

### 5.2 获取必需的密钥

#### 🤖 AIHubMix API Key（必需，调 LLM）

AIHubMix 是一个 OpenAI 兼容的多模型聚合平台，可一站式调用 GPT-5 / Claude / Gemini 等。**国内访问无障碍**。

1. 注册：https://aihubmix.com/
2. 进入「API Keys」页面 → 「创建新 Key」
3. 复制 key（形如 `sk-xxxxxxxxxxxxxxxxxx`）→ 填到 `.env` 的 `BOOTSTRAP_OPENAI_API_KEY`
4. **充值**：建议先充 ¥10 测试，本项目每次预测调用 1 次 LLM，gpt-5.5 单次约 ¥0.05

> 也可以直接用 OpenAI 官方 key（需海外网络）：把 `BOOTSTRAP_OPENAI_BASE_URL` 改为 `https://api.openai.com/v1`，模型选 `gpt-4o-mini` 或 `gpt-4o`。

#### 📲 飞书机器人 Webhook（必需，推送信号）

1. 打开飞书，选一个群（建议建一个专门的「BTC 信号」群避免打扰）
2. 群设置 → 群机器人 → 添加机器人 → **自定义机器人**
3. 填名字（如 "BTC Arb"）→ 描述 → 头像 → 完成
4. 复制 webhook URL，形如 `https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
5. 填到 `.env` 的 `BOOTSTRAP_FEISHU_WEBHOOK_URL`

> 不填也能起服务，会进入 **dry-run 模式**：信号生成正常，飞书推送只打日志不真发。

#### 🟦 Polymarket / Binance — 无需 key

- Polymarket Gamma + CLOB API 是公开的，无 rate limit 友好
- Binance ticker + klines 也是公开的，本工具只读 BTCUSDT 现货

### 5.3 一键启动（推荐：docker-compose 全栈）

```bash
# 1. clone 项目并进入
cd /path/to/lesson9

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填上面拿到的 AIHubMix key + 飞书 webhook
vim .env

# 3. 启动全栈
docker compose up -d --build

# 4. 等 30 秒让 backend 自动跑 alembic upgrade head + bootstrap discover
docker compose logs -f backend  # 看到 "Application startup complete" + 一次 discover 跑完即可

# 5. 打开浏览器
open http://127.0.0.1:3000     # frontend 仪表盘
curl http://127.0.0.1:8000/api/v1/healthz   # 后端探活
```

### 5.4 本地开发模式（不用 docker 跑 backend/frontend）

适合改代码即时调试：

```bash
# 起 Postgres（用 docker-compose 只起 db 一个服务）
docker compose up -d db
# 如果宿主 5432 被占，编辑 docker-compose.override.yml 改成 5435

# 起 backend（手动 + 加载 .env）
cd backend
pip install -e ".[dev]"
alembic upgrade head
# 注意 DATABASE_URL 改成 host 视角，比如 localhost:5435
DATABASE_URL="postgresql+asyncpg://btc_arb:btc_arb@127.0.0.1:5435/btc_arb" \
  uvicorn btc_arb.main:app --host 0.0.0.0 --port 8002

# 起 frontend
cd frontend
pnpm install
# 改 .env.local 让 NEXT_PUBLIC_API_BASE 指向 8002（不是 8000）
echo "NEXT_PUBLIC_API_BASE=http://127.0.0.1:8002/api/v1" > .env.local
pnpm dev --port 3002

# 访问
open http://127.0.0.1:3002/dashboard
```

### 5.5 验证全链路

```bash
# 健康检查
curl http://127.0.0.1:8000/api/v1/healthz
# {"status":"ok","db":"ok","version":"0.1.0-skeleton"}

# 看 bootstrap 拉到的市场
curl http://127.0.0.1:8000/api/v1/markets | jq

# 手动触发完整流程（discover → predict → poll → signal → notify）
cd backend
DATABASE_URL=... python scripts/demo_run_once.py --seed

# 飞书群应收到一张红色/绿色 ENTRY 卡片
```

---

## 6. 配置详解

### 6.1 `.env` 字段说明

```bash
# 数据库连接串（docker 内 backend 自动覆盖为 db 服务名）
DATABASE_URL=postgresql+asyncpg://btc_arb:btc_arb@db:5432/btc_arb

# Web 服务
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=info  # debug / info / warning / error

# CORS：固定列表 + main.py 还配了正则放行所有 127.0.0.1:3xxx 端口
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Bootstrap 密钥（仅当 setting 表对应字段为空时写入；非空不覆盖）
BOOTSTRAP_OPENAI_API_KEY=sk-xxxxxxxxxxxxx
BOOTSTRAP_OPENAI_MODEL=gpt-5.5                            # AIHubMix 推荐
BOOTSTRAP_OPENAI_BASE_URL=https://aihubmix.com/v1         # 改 OpenAI 官方就用 https://api.openai.com/v1
BOOTSTRAP_FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx
BOOTSTRAP_WEB_SEARCH_API_KEY=                              # v1 未用
```

### 6.2 Setting 表运行时参数

启动后所有业务参数都存在 `setting` 表（singleton，id=1），运行期可通过 `PATCH /api/v1/settings` 或 `/settings` 页面修改，**改完立刻生效（最迟 5 分钟内被下一轮调度生效）**：

| 字段 | 默认 | 含义 |
|---|---|---|
| `entry_threshold` | 0.15 | gap 绝对值超此值触发 ENTRY 信号（demo 期间被改成 0.03 容易触发） |
| `debounce_minutes` | 10 | 状态变更后多久内禁止再次跃迁（避免噪音） |
| `price_poll_minutes` | 5 | CLOB midpoint 轮询间隔 |
| `predict_ttl_hours` | 24 | predict 在多久内视为新鲜不重算 |
| `discovery_keywords` | `["bitcoin","btc"]` | 关键词过滤（discovery 改重写后此字段实际不用了，因为只追 daily slug） |
| `discovery_max_days_to_resolve` | 2 | 「今天 + N 天」拉哪一天的 BTC 价格 event |
| `feishu_webhook_url` | bootstrap | 改了立即对下一轮 notify 生效 |
| `openai_api_key` | bootstrap | mask 显示（前 6+`***hidden***`+后 4） |
| `openai_model` | gpt-5.5 | 可在 UI 切换 |

### 6.3 Bootstrap 规则（重要）

为防 `.env` 回灌覆盖 UI 改的值：

- 启动时 `services/bootstrap.py` 遍历 `(env_attr, setting_attr)`
- env **有值** 且 setting 列 **NULL/空字符串** → 写入
- setting 列 **非空** → **跳过不覆盖**

也就是说 **`.env` 是首次部署 / DB reset 后的种子值，user 改了 UI 之后就以 DB 为准**。

---

## 7. 使用指南

### 7.1 看 dashboard

`http://127.0.0.1:3000/dashboard`

- **4 KPI**：总监控市场 / 活跃市场 / 入场中（持仓信号）/ 24h 推送数
- **最近信号表**：最近 20 条 signal_event，按 gap 颜色（绿=做多机会，红=做空机会）排序
- **监控中的市场**：当前 DB 里的市场列表，点行进详情页

### 7.2 手动预测一个市场

`http://127.0.0.1:3000/predict`

1. 复制 Polymarket URL（推荐 event 集合，如 `https://polymarket.com/event/bitcoin-above-on-may-21`）
2. 粘贴到输入框
3. 两种模式：
   - 🚀 **试一次（dry-run）**：只算预测，不入库
   - 📥 **加入监控并推送**：market 写入 DB + 立即跑信号引擎 + 真推飞书（如触发）
4. 看结果卡：
   - 蓝色「🎯 Event 集合」提示框告诉你自动选了哪个子市场（最接近 50%）
   - 大数字 P(AI) / P(量化) / LLM 调整 / 置信度
   - LLM 中文 rationale 解释为什么这么调

### 7.3 调整阈值让信号更/更少触发

`http://127.0.0.1:3000/settings` → 信号引擎组：

- 想看更多信号（demo 用）：`entry_threshold` 调到 0.03
- 想只看真有套利空间的：`entry_threshold` 调到 0.15（PRD 默认）
- 推太频繁 → `debounce_minutes` 调大（如 30）

### 7.4 关掉真实飞书推送（不打扰）

清空 `feishu_webhook_url` 字段 → 自动进入 dry-run，信号生成正常，推送只打 log。

### 7.5 看历史信号 + 导出 CSV

`http://127.0.0.1:3000/history` → 选 kind → 「导出 CSV」按钮。

---

## 8. 项目结构

```
lesson9/
├── README.md                              ← 你正在看
├── PRD.md                                 ← 产品 PRD（v1 范围 / 价值主张 / 不做的事）
├── backend-PRD.md                         ← 后端 PRD（架构 / API / 调度 / 错误处理）
├── frontend-PRD.md                        ← 前端 PRD（路由 / 页面 / 状态管理）
├── .env.example                           ← 环境变量样例
├── .env                                   ← 实际配置（gitignore）
├── docker-compose.yml                     ← 一键起全栈
├── docker-compose.override.yml            ← 本地开发覆盖（gitignore，按需）
├── scripts/
│   ├── smoke.sh                           ← 完整端到端冒烟脚本
│   └── smoke-phase0.sh                    ← Phase 0 contract 冒烟
├── docs/
│   ├── Polymarket-调研.md                  ← 课程背景调研
│   ├── test-strategy.md                    ← 测试策略文档
│   └── qa-checklist.md                     ← 75 条手动验收 checklist
├── backend/
│   ├── pyproject.toml                     ← Python 依赖 + ruff + pytest 配置
│   ├── Makefile                           ← test / test-cov / lint 快捷命令
│   ├── alembic/versions/
│   │   └── 20260518_0001_initial_schema.py
│   ├── scripts/
│   │   ├── check_coverage.py              ← 分级覆盖率断言（≥95% 核心）
│   │   └── demo_run_once.py               ← 一次跑完整 pipeline
│   ├── src/btc_arb/
│   │   ├── main.py                        ← FastAPI 入口 + lifespan
│   │   ├── config.py                      ← pydantic-settings 装 ENV
│   │   ├── db.py                          ← async engine / session factory
│   │   ├── logging.py                     ← structlog JSON 配置
│   │   ├── exceptions.py
│   │   ├── adapters/
│   │   │   ├── polymarket.py              ← Gamma + CLOB midpoint
│   │   │   ├── binance.py                 ← spot + 30d 波动率（60s 缓存）
│   │   │   ├── openai_llm.py              ← OpenAI 兼容（默认 AIHubMix）
│   │   │   └── feishu.py                  ← interactive card + dry-run
│   │   ├── services/
│   │   │   ├── quant.py                   ← 对数正态 P(BTC > strike at T)
│   │   │   ├── discovery.py               ← 每日只追 bitcoin-above-on-{date}
│   │   │   ├── prediction.py              ← quant + LLM 合成 + nudge ≥20pp
│   │   │   ├── price_monitor.py           ← 拉 midpoint 写 tick
│   │   │   ├── signal_engine.py           ← 4 态状态机
│   │   │   ├── notification.py            ← 渲染卡片 + 推送
│   │   │   └── bootstrap.py               ← ENV → setting 表自动填充
│   │   ├── scheduler/__init__.py          ← APScheduler 4 job
│   │   ├── routers/                       ← 6 个真实实现的 REST 路由
│   │   ├── schemas/                       ← Pydantic 响应 schemas
│   │   └── models/                        ← 6 张 ORM 表
│   └── tests/                             ← pytest scaffold + 少量 lib 测试
└── frontend/
    ├── package.json                       ← Next 16 + Tailwind 4 + shadcn
    ├── .env.local                         ← NEXT_PUBLIC_API_BASE 等
    ├── vitest.config.ts                   ← vitest + RTL + coverage-v8
    ├── app/
    │   ├── layout.tsx                     ← 全局 dark + navbar + footer
    │   ├── globals.css                    ← 深色 tokens + glass-card + 动画
    │   ├── dashboard/page.tsx
    │   ├── predict/page.tsx
    │   ├── history/page.tsx
    │   ├── settings/page.tsx
    │   └── markets/[id]/page.tsx
    ├── components/
    │   ├── navbar.tsx                     ← 玻璃态导航
    │   ├── footer-disclaimer.tsx
    │   ├── scheduler-health-indicator.tsx
    │   ├── query-provider.tsx
    │   └── ui/                            ← shadcn 11 个组件
    ├── lib/
    │   ├── api.ts                         ← apiFetch + ApiError（兼容 FastAPI {detail}）
    │   ├── schemas.ts                     ← Zod 镜像 backend Pydantic
    │   ├── time.ts                        ← formatRelativeFromNow
    │   └── format.ts
    └── hooks/                             ← use-markets / use-signals / use-predict 等
```

---

## 9. 关键概念

### 9.1 量化模型（`services/quant.py`）

**对数正态假设**：`log(S_T / S_0) ~ N(0, σ² · τ)`（无漂移，简化版 Black-Scholes 中性世界）

- `S_0` = 当前 BTC 现货价（Binance）
- `σ` = 30 天年化已实现波动率
- `τ` = 到结算的年化剩余时间
- 输出 `P(BTC > strike at T)` clip 到 `[0.001, 0.999]`

**退化路径**：
- 距结算 ≤ 60 秒 → 直接按当前 spot vs strike 给 0.001/0.999
- σ ≤ 0 → 同上

### 9.2 LLM 调整（`adapters/openai_llm.py`）

固定 system prompt 让 LLM 在 `[-0.30, 0.30]` 范围内给出 `adjustment`。Prompt 中文化，要求：

- 输出 JSON `{adjustment, confidence: low/medium/high, rationale}`
- 没有强烈方向性证据时 adjustment 接近 0（±0.05 以内）
- 绝对值不能超过 0.30（硬约束，超出会被裁剪）

### 9.3 套利偏向（`prediction.py: DEMO_FORCE_MIN_GAP=0.20`）

**Demo 用**：算完 `p_ai` 后如果 `|p_ai - p_mkt| < 0.20`，强制把 p_ai 推到 `p_mkt ± 0.20`（方向沿用 p_ai 当前相对 p_mkt 的方向）。

- `model_version` 加 `-nudged` 后缀，`llm_rationale` 加 `[NUDGED for demo: ...]` 前缀，透明可追溯
- **关闭**：把 `DEMO_FORCE_MIN_GAP` 改为 `0.0`

### 9.4 状态机（`services/signal_engine.py`）

```
              gap > +threshold (>15%)
WATCHING ─────────────────────────────→ ENTERED_LONG  (kind=ENTRY_LONG)
   ▲                                          │
   │                                          │ gap < +ε (0.001)
   │  gap > -ε                                ▼
   └────────────────────────────────────── (回 WATCHING, kind=EXIT_LONG)
   
              gap < -threshold (-15%)
WATCHING ─────────────────────────────→ ENTERED_SHORT (kind=ENTRY_SHORT)
   ▲                                          │
   │                                          │ gap > -ε
   │  gap > -ε                                ▼
   └────────────────────────────────────── (回 WATCHING, kind=EXIT_SHORT)

任何状态 + now ≥ resolve_at → EXPIRED (优先于其他跃迁)
```

**去抖**：`last_state_change_at` 之后 `debounce_minutes` 内不触发非 EXPIRED 跃迁。

**ε 滞回带**：避免在阈值附近反复跳。

### 9.5 Event 选 50% 子市场

Polymarket 一个 event（如 "Bitcoin above ___ on May 21?"）通常含 5-11 个不同 strike 的 sub-market（$70k/$72k/.../$80k）。我们：

- **discovery 自动跑**：每日只追 `bitcoin-above-on-{date}` event，并发拉所有 sub-market 的 CLOB midpoint，**挑 `|mid - 0.5|` 最小的入库**（套利信息量最高）
- **/predict 手动跑**：同样逻辑。前端蓝色提示框告知 user 从 N 个子市场选了哪个

---

## 10. 调度任务节奏

| Job | 触发器 | 频率 | 干什么 |
|---|---|---|---|
| `discover_bootstrap` | date (启动后立即) | 一次 | 启动后立刻跑一次 discover，避免冷启动空数据 |
| `discover` | cron 00:30 UTC | 每天 1 次 | 拉 today+2 那天的 BTC 价格 event，挑最接近 50% 子市场入库 |
| `predict` | interval | 每 30 分钟 | 对所有非 EXPIRED 市场跑预测（按 `predict_ttl_hours` 跳过新鲜的） |
| `price_poll` | interval | 每 5 分钟 | 对所有非 EXPIRED 市场拉 YES midpoint，写 tick |
| `signal_notify` | interval | 每 5 分钟（+ jitter） | 跑 signal_engine + 推飞书未推的事件 |

---

## 11. 常见问题与故障排查

### 11.1 浏览器看不到数据 / "未知错误"

99% 是浏览器**缓存了旧 bundle**。Ctrl+Shift+R 强刷，或开无痕窗口。

如果仍看不到：F12 → Network 看是否有失败的 `/api/v1/*` 请求；Console 看红字。

### 11.2 `/predict` 报「未在 Polymarket 找到 slug=...」

Polymarket 通常只**预创建未来 2-3 天**的 `bitcoin-above-on-{date}` event。给的日期太靠后会 404。

- 今天 UTC = 2026-05-18 → 可用：May 19 / 20 / 21
- May 22+ 要等下一天 Polymarket 自己建

### 11.3 LLM 调用失败 → 降级到纯量化

正常行为。`model_version` 会加 `-llm-fail` 后缀，`llm_rationale` 写 `[LLM-FAIL] 调用失败`。常见原因：

- AIHubMix 余额不足
- key 写错
- 网络问题
- 模型名错（如写成 `gpt-5.5-` 多了个 `-`）

### 11.4 飞书没收到推送

检查顺序：
1. `setting.feishu_webhook_url` 是否真有值（去 `/settings` 看，mask 后还能看到前 6+ 后 4 字符）
2. 设置页 → 飞书推送 →「🚀 发一条测试卡片」按钮 → 看群里有没有蓝色测试卡
3. 看 backend log：`grep "feishu" /tmp/btc_arb_backend.log`，正常是 `POST .../hook/... 200 OK`

### 11.5 端口冲突

- **5432 被占**（你本机已装 Postgres）：编辑 `docker-compose.override.yml` 把映射改为 `127.0.0.1:5435:5432`
- **8000 被占**：改 `APP_PORT=8002` + frontend `NEXT_PUBLIC_API_BASE` 同步
- **3000 被占**：next 自己会跳到 3001 / 3002 / 3003，CORS 已配 regex 通配 3xxx 所有端口

### 11.6 改了 `.env` 不生效

`.env` 是 **bootstrap 种子值**，启动时如果 setting 表对应字段已有非空值就**跳过不覆盖**。

要让 `.env` 生效：
1. 先把 setting 表对应字段清空：`UPDATE setting SET openai_api_key = NULL WHERE id = 1;`
2. 重启 backend
3. 看启动日志：`bootstrap.done filled=[openai_api_key]`

或者直接走 `/settings` 页面 UI 改值，更直观。

### 11.7 想重新发现市场（清 DB 测试用）

```bash
docker compose exec db psql -U btc_arb -d btc_arb -c \
  "TRUNCATE signal_event, prediction, price_tick, job_run, market RESTART IDENTITY CASCADE;"
# 触发立即 discover
curl -X POST -d '{"job_id":"discover"}' -H "Content-Type: application/json" \
  http://127.0.0.1:8000/api/v1/scheduler/trigger
```

---

## 12. Vibe Coding 复盘：Claude Agent Team 模式

> 这部分是这门课的核心 takeaway —— **怎么用 Claude Code 的多 agent team 模式从 0 到 1 vibe-code 一个完整产品**。

### 12.1 我们用的模式

整个项目通过 **3 段会话** 完成，每段都按需 spawn 不同的 agent team：

| 会话 | 团队 | 产出 |
|---|---|---|
| Session 1 | PM + frontend + backend + qa（4 人） | PRD.md + backend-PRD.md + frontend-PRD.md + 任务拆解 + 初版 skeleton |
| Session 2 | team-lead（我自己） + 3 个 worker 但中途因配额暂停 | 转为 team-lead 直接编码，完成核心闭环（adapters + services + scheduler + 4 frontend 页面） |
| Session 3 | team-lead（独立编码） | 反复迭代（discovery 重写、UI 重设计、URL 真实化、nudge、persist 等 12+ 次需求变更） |

最终 git history：**15+ 个 commit**，全部带详细 commit message。

### 12.2 Claude Agent Team 是什么

Claude Code 原生支持 `TeamCreate` + `Agent` 工具组合，让你声明一个团队 + spawn 多个独立 agent 进程并发干活：

```
TeamCreate(team_name="btc-arb", agent_type="team-lead")
  ↓
Agent(team_name="btc-arb", name="pm", subagent_type="general-purpose", prompt="...")
Agent(team_name="btc-arb", name="frontend", subagent_type="general-purpose", prompt="...")
Agent(team_name="btc-arb", name="backend", subagent_type="general-purpose", prompt="...")
Agent(team_name="btc-arb", name="qa", subagent_type="general-purpose", prompt="...")
```

每个 agent **独立进程、独立 context window**，通过 `SendMessage(to=name, message=...)` 互发消息，共享 `TaskList` / `TaskCreate` / `TaskUpdate` 协作任务。

### 12.3 工作流：team-lead → PM → 3 工程师

**第一轮**（你看到的现象）：

1. **team-lead（你/我）** 给出一句话需求："做一个 Polymarket BTC 套利信号工具"
2. **PM 自己写 PRD**：拆功能、定 v1 范围、问澄清问题（如「OpenAI 模型默认值确认 gpt-5？」、「Web 搜索 v1 只 Tavily 还是全部 4 个 provider？」）
3. **team-lead 决策回 PM**（按"不停下来澄清，做合理决策"原则）
4. **PM 用 `TaskCreate` 拆 33 个任务**（B-* backend、F-* frontend、Q-* qa），用 `addBlockedBy` 配依赖图，建议每个任务的 owner 角色
5. **3 工程师并行 check-in**：各自读 PRD + 报 1-2 个最值得改进的方向
6. **team-lead 批准任务图 + 决定 owner 分配方式**
7. **PM 同时给 3 工程师发启动消息**，强调 backend 关键路径
8. **工程师按 ID 顺序自己 claim 任务**，用 `TaskUpdate` 设 `in_progress` → 写代码 → 设 `completed`

### 12.4 实际涌现出来的协作模式

| 现象 | 含义 |
|---|---|
| QA 主动拆「不依赖业务代码的脚手架前置 PR」（Q-01a / Q-02a） | QA 不被动等业务 ready 才动手；先做 pytest config / fixture conftest 等基础设施，业务代码 land 即可用 |
| frontend 提议在 F-01 顺手把 vitest deps 装好 | 跨角色顺手帮 QA，砍掉 0.3 天 |
| PM 抓到 QA 误把 Q-04 标 completed 实际依赖未满足 | PM 主动质量守门，先 ping QA 后回滚状态 |
| team-lead 在「先回滚再讨论」和「case-by-case 判断」之间发了相互冲突的指令导致 Q-04 三次翻转 | 真实工程团队也会有的混乱，PM 复盘 + 「指令归因」明确责任归 team-lead 不在 QA |

### 12.5 痛点 / 教训

1. **token 烧得快**：4 个 agent 并发跑，每条消息都要序列化整个 context；3 轮决策 + 启动消息后已经吃掉一半配额
   - **缓解**：复杂决策让 team-lead 直接做；agent 只负责执行；少 ping、少 idle 通知
2. **agent 进程会死**：会话结束后 agent 退出，但 team config 还在 — 重启 session 后要重新 spawn
3. **PM 偶尔过度协调**：发现就明确「PM 默认信任工程师专业判断，只在涉及 PRD / 跨角色 / 阻塞时介入」
4. **dev tooling 实施细节谁拍板**：明确「PRD 只约束 user-visible；smoke 脚本 ENV 名 / fixture 命名 / Makefile target 由实施者决定」，避免 PM 当裁判
5. **指令分层混乱**：team-lead 给出「执行指令」和「策略原则」要分清，避免下属执行了具体动作又被后续原则推翻

### 12.6 什么时候用 team 模式 vs solo

| 场景 | 推荐 |
|---|---|
| 0→1 spec + 拆任务 + 多角色视角碰撞 | ✅ 用 team，PM 价值最大 |
| 已经在迭代，需求清晰，10 分钟改完 | ❌ team-lead 直接做，省 token |
| 跨多 stack 并发开发（前端写页面 + 后端写 API 互不阻塞）| ✅ 用 team，并发省时间 |
| 大量重复模板代码（如生成 50 个相似 component） | ✅ 用 team 并发 |
| 调试一个 bug | ❌ solo + systematic-debugging skill |
| 写文档 / README | ❌ solo |

### 12.7 整段 vibe coding 的核心 takeaway

> **vibe coding 不是无脑生成，而是把 PM/工程师协作的『软技能』也外包给 agent**。
>
> Claude Agent Team 让 team-lead（人或 AI）从「写代码的人」变成「拍板 + 复盘的人」。整套工程方法论（PRD → 拆任务 → 依赖图 → 关键路径 → owner 分配 → 状态守门 → 复盘）和真实公司团队**完全同构**。
>
> 配额是真正的瓶颈。不是「能不能做」，而是「在配额内能做到什么程度」。所以 **team 模式适合开局发力（让多 agent 帮你 brainstorm + 拆任务 + 跑骨架），后期迭代/修 bug 用 solo team-lead** 是当前最经济的姿势。

---

## 13. 后续工作

按优先级：

### 必须做（v1.0 完成度）

- [ ] **backend 单元测试**：signal_engine.decide_transition 纯函数 ≥95% case 覆盖、quant.quant_probability 边界 case
- [ ] **集成测试**：testcontainers-postgres 跑完整 discover → predict → poll → signal → notify 流程
- [ ] **contract tests**：4 个外部 API（Polymarket Gamma / CLOB / Binance / OpenAI 兼容）的 schema drift canary

### 想做（v1.5+）

- [ ] **frontend dashboard 实时性**：给 hooks 加 `refetchInterval`（市场 30s / 信号 15s）+ 右上「上次刷新 5s 前」标识
- [ ] **price tick mini sparkline**：在监控市场列表里给每行一条价格走势小图
- [ ] **N+1 query 优化**：signal_engine.evaluate_all_active 串行 SELECT 改成一次 distinct on 批量
- [ ] **discovery 多 event 监控**：从只追 today+2 扩展到 today+1, today+2, today+3 三天的 event 同时监控
- [ ] **真实 web search**：v1 砍了 Tavily 集成，v1.5 接上让 LLM 拿到近期 BTC 新闻
- [ ] **K 线图增强**：markets/[id] 加 30 天 BTC 价格 + Polymarket 价格双轴对比

### 不做（明确边界）

- 不下单、不接钱包、不接 CLOB 下单（这是个**信号工具**不是交易机器人）
- 不做多用户、不接登录
- 不做 BTC 以外标的（ETH/SOL/股票预测市场）
- 不做止损推送（user 自己负责仓位）

---

## License

仅作 lesson 9 课程演示，不做商业用途。
