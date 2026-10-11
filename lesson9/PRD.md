# Polymarket BTC 套利信号工具 PRD

> 文档版本：v1.0
> 编写日期：2026-05-17
> 参考站点：https://polymarket.com/
> 目标：本地跑、面向个人交易者的 Polymarket BTC 价格预测市场套利信号工具——后端定时发现 BTC 相关市场、AI（量化 + LLM）给出 YES 概率预测、与市场实时价格比对，发现错价或机会兑现时通过飞书推送提醒

> 风险声明：本工具仅作个人研究与信号提醒，不构成投资建议；预测市场涉及资金与合规风险，参与前请阅读 Polymarket 官方规则并自行判断地缘合规

---

## 0. 文档读法

本 PRD 仅描述产品需求与功能边界，不写实现细节。
- 后端实现：见 `backend-PRD.md`（架构、服务、数据库、API、调度、错误处理、测试）
- 前端实现：见 `frontend-PRD.md`（路由、页面、组件、状态管理、UX）
- 课程相关背景：见 `docs/Polymarket-调研.md`

每个功能模块按「目标 → 行为 → 输入输出 → 验收标准」描述。

---

## 1. 产品概述

### 1.1 一句话定义

一个本地跑、面向个人交易者的 Polymarket BTC 价格预测市场套利信号工具。后端定时发现 BTC 相关市场、AI（量化 + LLM）给出 YES 概率预测、与市场实时价格比对，发现错价机会或机会兑现时通过飞书推送提醒。

### 1.2 价值主张

| 痛点 | 我们的价值 |
|------|-----------|
| Polymarket 上 BTC 相关市场分散，手动盯盘成本高 | 每日自动发现 + 按规则筛选活跃市场 |
| 「市场价是真概率吗」难以判断 | 量化模型给基础概率 + LLM 读近期新闻调整，给出可解释预测 |
| 即使发现错价，也容易错过价格回归窗口 | 实时轮询 + 状态机判定 + 飞书推送，错价出现与兑现都不漏 |
| 想跟踪多个市场但又怕被噪音骚扰 | 入场阈值 + 去抖窗口 + 临近结算停推三重过滤 |

### 1.3 商业模式

无。个人使用工具，不向他人收费、不接外部用户、不出售数据。

### 1.4 范围说明

**v1 包含**：
- 自动发现 Polymarket 上 BTC 相关二元（YES/NO）市场
- 手动输入市场 URL 触发预测
- 量化模型 + OpenAI LLM 调整的混合预测
- Web 搜索 API 给 LLM 灌近期新闻
- 市场价 5 分钟轮询、AI 预测 24 小时重跑
- 状态机驱动的入场/兑现信号
- 飞书 Webhook 推送
- Next.js 前端：仪表盘、市场详情、手动预测、推送历史、设置
- docker-compose 本地一键起

**v1 不做**（明确列入 Future Scope，本期不实现也不预留接口）：
- 实际下单（不接 Polymarket CLOB 下单 API、不接钱包）
- 多用户 / 登录系统
- 多结果市场（≥3 outcomes，如「BTC 5月底处于哪个区间」）
- BTC 以外的标的（代码层面市场过滤基于关键词、扩展只需改配置，但 v1 默认仅 BTC）
- 止损推送（市场反向走、扩大亏损时的告警）
- Telegram / Discord / 邮件等其他通知通道
- 历史预测准确率打分 / 回测平台
- 自动数据迁移工具、CI/CD、多环境部署

### 1.5 成功标准（个人验收）

| 指标 | 目标 |
|------|------|
| 每日自动发现的 BTC 市场数 | 5–30 个（取决于 Polymarket 当日活跃情况） |
| 自动发现 job 失败率 | < 5%（30 天滚动窗口） |
| 价格轮询 job 失败率 | < 1%（30 天滚动窗口） |
| 入场信号到飞书推送的延迟 | p99 < 30 秒 |
| 飞书推送失败后自动重试成功率 | > 95% |
| 仪表盘加载时间 | < 1 秒（本地访问） |
| 一次启动后稳定运行 | ≥ 7 天无人工介入 |

---

## 2. 用户角色与场景

### 2.1 角色

唯一角色：**Operator（你自己）**。不区分游客/普通用户/管理员，全部权限。

### 2.2 关键场景

- **S1 起床看信号**：早上打开飞书，看到 1–3 条入场信号卡片 → 点击「打开仪表盘详情」→ 浏览器看价格走势 + LLM 解释 → 判断是否值得手动到 Polymarket 下单。
- **S2 手动预测**：在 X 上看到某 BTC 预测市场讨论 → 复制 URL → `/predict` 页贴上 → 「试一次」看 AI 当下预测 → 满意则「加入监控」。
- **S3 信号兑现**：午饭时收到兑现卡片「市场涨到 0.72，你的预测点已触达」→ 决定是否手动 Polymarket 平仓。
- **S4 调参**：发现一天推 10 条信号太多 → `/settings` 把入场阈值从 0.15 调到 0.20。
- **S5 看历史复盘**：周末打开 `/history` 看一周所有推送 → 对照 Polymarket 实际价格走势，主观判断模型质量。
- **S6 排错**：飞书突然没推送 → `/settings` 调度状态面板看是否 job 失败 → 点「发送测试卡片」验证 Webhook 是否仍然有效。

---

## 3. 信息架构

### 3.1 前端路由

```
/                       → redirect /dashboard
/dashboard              仪表盘
/markets/[id]           市场详情
/predict                手动预测
/history                推送历史
/settings               设置
```

### 3.2 模块清单

| 模块 | 用途 | 涉及表 |
|------|------|--------|
| 市场发现 | 每日定时扫 Polymarket BTC 市场 + 手动添加 | market |
| 预测引擎 | 量化 + LLM 混合预测 | prediction |
| 价格轮询 | 5 分钟拉一次市场 YES 价 | price_tick |
| 信号引擎 | 状态机驱动入场/兑现判定 | market, signal_event |
| 推送通道 | 飞书 Webhook 卡片 | signal_event |
| 设置 | 全局参数配置 | setting |
| 调度观测 | job 执行历史 + 手动触发 | job_run |

---

## 4. 核心功能详述

### 4.1 市场发现

**目标**：自动维护一份当前应该被监控的 BTC 相关市场清单。

**行为**：
- **自动发现**：APScheduler 每日 UTC 00:00 触发 `daily_discovery_job`。从 Polymarket Gamma API 拉所有 `active=true` 市场，过滤条件：
  1. 标题或描述包含设置里 `discovery_keywords`（默认 `bitcoin`/`btc`，大小写不敏感）任一关键词
  2. `outcomes` 长度 = 2（仅二元 YES/NO 市场）
  3. `resolve_at` 在未来 `discovery_max_days_to_resolve`（默认 30）天以内
  4. `condition_id` 不在已有 `market` 表中
- 通过过滤的市场写入 `market`，`source='discovery'`，状态默认 `WATCHING`，立即触发一次预测（同步等结果），写完后下次轮询周期即可参与状态判定。
- **手动添加**：用户在 `/predict` 页提交 Polymarket URL。后端解析 URL → 取该市场元数据 → 同样写入 `market`（`source='manual'`）+ 立即跑一次预测并返回结果。
- **去重**：`condition_id` 唯一约束保证同一市场不会被重复添加；手动添加已存在市场返回 409。

**输入输出**：
- 输入（auto）：无
- 输入（manual）：`{ polymarket_url: string }`
- 输出：`{ market, prediction }` 或错误 `{ error: { code, message } }`

**验收标准**：
- 在 Polymarket 至少有 3 个活跃 BTC 市场时，单日自动发现应返回 ≥ 3 个；
- 手动添加同一 URL 第二次返回 409，不重复入库；
- 非 BTC、非二元、已结算市场被拒绝（422，错误码 `MARKET_NOT_SUPPORTED`、`MARKET_NOT_BINARY`、`MARKET_RESOLVED`）；
- 关键词从默认 `bitcoin`/`btc` 改成 `ethereum` 后，下次发现 job 应改抓 ETH 类市场（验证关键词可配）。

### 4.2 AI 预测

**目标**：给出每个市场 YES 概率的可解释预测。

**行为**：分两阶段。
- **量化阶段（QuantModel）**：
  - 从市场元数据解析「BTC above $X by T」中的 strike `X` 与 direction (`above`/`below`) 和 resolve time `T`。
  - 调 Binance Spot API 拉当前 BTC 现货 `S` 与近 30 日 1h K 线，算实现年化波动率 `σ`。
  - 按对数正态分布假设，求 `P_quant = Pr(S_T > X)`（above 方向；below 方向取补集）。
  - 输出 `(P_quant, S, σ)`。
- **LLM 阶段（LLMAdjuster）**：
  - 调 Web 搜索 API（默认 Tavily）抓近 24h「bitcoin」相关新闻摘要 ≤ 5 条。
  - 调 OpenAI（默认 `gpt-5`），输入 `{market_question, P_quant, S, σ, news_summaries}`，要求 structured output：
    ```
    { p_final: number 0..1, adjustment: number -0.30..0.30, confidence: 'low'|'medium'|'high', rationale: string }
    ```
  - 调整量被强制限制在 ±0.30 范围；若 LLM 返回越界值，clip 后标 `rationale` 加注「越界 clip」。
  - 若 Web 搜索返回空，LLM 仍跑但 prompt 标「无可用新闻」，`adjustment` 上限收紧到 ±0.05。
- 写一条 `prediction` 记录（`p_ai = clip(p_quant + adjustment, 0.001, 0.999)`）。
- 24h 后或用户手动重跑时再来一遍。

**输入输出**：
- 输入：`market_id`
- 输出：`{ p_ai, p_quant, llm_adjustment, llm_confidence, llm_rationale, news_sources, spot_price, realized_vol, model_version }`

**验收标准**：
- 给定一个固定的 strike + resolve_time + 模拟 spot/vol，QuantModel 输出确定的 P_quant（单元测试）；
- LLM 返回的 `p_final` 必落在 [0.001, 0.999]，`adjustment` 必落在 [-0.30, 0.30]；
- OpenAI 5xx 时回退到纯量化预测（`adjustment=0`、`confidence='low'`、`model_version` 后缀 `-llm-fail`），系统仍出预测；
- 同一市场连续两次预测之间间隔默认 24h，UI 可手动「立即重跑」。

### 4.3 价格轮询

**目标**：维护每个在监控市场的 YES 份额最新价。

**行为**：
- APScheduler 每 `price_poll_minutes`（默认 5）分钟触发 `price_poll_job`。
- 对所有 `state IN ('WATCHING','ENTERED_LONG','ENTERED_SHORT')` 的 market，并发调 Polymarket CLOB midpoint API 拉 `p_yes`，写入 `price_tick`。
- 写入后立即触发 SignalEngine.evaluate(market)。
- `price_tick` 保留 30 天（job 定期清理）。
- 单次失败：本市场本轮跳过，job_run.stats 记 `failed_markets: [...]`；连续 6 次同一市场失败 → 状态机视该市场为 stale，UI 灰显但不停轮询；下次成功后自动恢复。

**输入输出**：
- 输入：无（job 自动）；手动可调 `POST /scheduler/trigger { job: 'price_poll' }`
- 输出：写库 + 触发 SignalEngine

**验收标准**：
- 5 分钟内每个 active 市场都应有一条新 `price_tick`；
- 单个市场失败不影响其他市场；
- 连续 24h 跑下来 job_run 成功率 ≥ 99%。

### 4.4 信号引擎与状态机

**目标**：根据预测与实时价格判定何时该推送信号。

**状态定义**：
```
WATCHING        无入场信号，持续轮询
ENTERED_LONG    已推过「建议买 YES」入场信号，等待价格涨到 p_ai 兑现
ENTERED_SHORT   已推过「建议买 NO」入场信号，等待价格跌到 p_ai 兑现
EXPIRED         市场已结算或 resolve_at 已过，停止监控
```

**跃迁规则**（设 `gap = p_ai - p_mkt`，`th = entry_threshold`，默认 0.15）：

| from | 条件 | to | 推送类型 |
|------|------|----|--------|
| WATCHING | `gap >= th` 且距 resolve_at > 1h | ENTERED_LONG | ENTRY_LONG「建议买 YES」 |
| WATCHING | `gap <= -th` 且距 resolve_at > 1h | ENTERED_SHORT | ENTRY_SHORT「建议买 NO」 |
| ENTERED_LONG | `p_mkt > p_ai + 0.001` | WATCHING | EXIT_LONG「建议平 YES」 |
| ENTERED_SHORT | `p_mkt < p_ai - 0.001` | WATCHING | EXIT_SHORT「建议平 NO」 |
| 任意 | `now >= resolve_at` | EXPIRED | EXPIRED「市场已结算」 |
| 任意 | `now - last_state_change_at < debounce_minutes` | 同 from | 不推送 |

**输入输出**：
- 输入：`market`, `latest_prediction`, `latest_price_tick`
- 输出：可能写 `signal_event` 一条 + 更新 `market.state` + 异步推飞书

**验收标准**：
- 单元测试覆盖所有上表行 + 边界（gap < 0.001、临近结算、去抖窗口内）共 ≥ 12 case；
- 同一市场连续两次满足跃迁条件、间隔 < 10 分钟，只推送一次；
- 状态变更与 `signal_event` 写入在同一事务，飞书推送在事务外执行（推送失败不回滚状态）。

### 4.5 飞书推送

**目标**：把信号事件即时送达。

**行为**：
- 信号事件创建后异步进推送队列。
- 渲染对应卡片模板：
  - **ENTRY_LONG**（看涨买 YES）：橙底，标题「🟠 入场信号 · 看涨 (买 YES)」
  - **ENTRY_SHORT**（看跌买 NO）：红底，标题「🔴 入场信号 · 看跌 (买 NO)」
  - **EXIT_LONG / EXIT_SHORT**：绿底，标题「✅ 兑现信号 · 平 YES」/「✅ 兑现信号 · 平 NO」
  - **EXPIRED**：灰底，标题「⚪ 市场已结算」（仅当之前为 ENTERED_* 时推；未入场就到期不推）
- 卡片字段：市场名（链接到 Polymarket）、AI 预测 vs 市场价、价差、模型版本、置信度、LLM 理由（折叠展开）、剩余时间、底部两个按钮「查看市场」「打开仪表盘详情」
- 推送 HTTP 4xx/5xx → 重试 3 次（间隔 10/30/60s）；仍失败标 `feishu_pushed=false` + `feishu_error`，仪表盘 KPI 显红。
- 「发送测试卡片」按钮：用当前 webhook 推一条样板卡片，前端显示 200/失败原因。

**输入输出**：
- 输入：`signal_event_id`
- 输出：HTTP POST 到飞书 webhook + 更新 `signal_event.feishu_pushed/feishu_push_at/feishu_error`

**验收标准**：
- 5 种 kind 的卡片样式都能在飞书群中正常渲染（包括按钮点击跳转）；
- 推送失败 + 自动重试，UI 历史页能看到「重试中」/「永久失败」状态；
- 设置页能配置 webhook 并实时验证。

### 4.6 设置

**目标**：单页改全局参数 + 验证外部依赖。

**字段**：见数据模型 `setting` 表（backend-PRD §4）。前端把字段分 6 块展示。

**行为**：
- GET 返回当前设置（敏感字段 mask）
- PATCH 部分字段更新；变更立即生效（无需重启）；APScheduler interval 类参数变更时通过 `reschedule_job` 平滑应用
- 「发送测试卡片」按钮：调 `POST /settings/test_feishu`

**验收标准**：
- 修改 `entry_threshold` 后下一轮 SignalEngine 立即用新值；
- 修改 `price_poll_minutes` 后 APScheduler 下次 tick 用新间隔（旧 job 不立即取消但 60 秒内切换）；
- 改坏的 webhook 测试按钮明确给出 4xx/网络错原因。

---

## 5. 非功能性需求

### 5.1 性能

- 单机 docker-compose（4C8G）能稳定监控 ≤ 100 个市场，5 分钟轮询 + 24h 重预测周期不丢任务
- 飞书推送 p99 < 30 秒（信号生成到送达）
- 前端任意页面交互响应 < 200ms（本地访问、无网络瓶颈）

### 5.2 可靠性

- 单一外部依赖失败不应造成全系统下线（详细矩阵见 `backend-PRD.md §7`）
- DB 是真相源；信号写入 → 飞书推送解耦
- 自动重试有上限，超限走「持久失败」标记 + UI 显眼提示

### 5.3 可观测性

- 所有 job 执行写 `job_run` 表，UI `/scheduler/runs` 直接读
- 所有信号触发与推送结果写 `signal_event` 表
- structlog 结构化日志 + docker volume 滚动 7 天
- 不引 Prometheus / Grafana（个人使用范围超额成本）

### 5.4 安全

- 所有 API Key（OpenAI、Tavily、飞书 Webhook）存 DB 加密字段或 .env，前端 GET 时 mask 显示
- 后端默认仅监听 `127.0.0.1`（docker-compose 端口映射），不对外暴露
- 不收集任何外部用户数据
- `.env.example` 不含真实密钥

### 5.5 时区与时间

- 全栈使用 UTC：DB 字段 `timestamptz`，Python 用 `datetime.now(timezone.utc)`，前端展示时浏览器本地化（用 `Intl.DateTimeFormat`）
- 日志、API 返回值、卡片字段中的时间必带 `Z` 后缀
- 严格遵循项目 `.cursor/rules/project-conventions.mdc` 第 1 条

### 5.6 国际化与文案

- v1 中文界面、中文卡片文案、注释/文档/string 内容全中文
- 标识符（代码层）保持英文

### 5.7 合规与免责

- 本工具不在 Polymarket 上代为下单、不接钱包、不接 CLOB 下单 API → 不触发 Polymarket 地缘限制下单合规问题
- README 与每个推送卡片底部均有「本工具仅作个人研究信号提醒，不构成投资建议」字样

---

## 6. 边界情况清单

| 情况 | 期望行为 |
|------|---------|
| `p_ai` 与 `p_mkt` 几乎相等（差距 < 0.001） | 不视为兑现，不推送，等下一轮 |
| 距 `resolve_at` < 1 小时 | 暂停入场判定与推送，UI 仪表盘卡片角标「临近结算」 |
| Polymarket CLOB 返回空 orderbook 或 5xx | 本轮 tick 跳过；连续 6 次失败 → 卡片灰显 + 悬停提示「数据异常」 |
| Polymarket Gamma 5xx | 自动发现 job 失败，写 job_run；下次定时再试；连续 3 次失败推一次「工具异常」飞书卡片 |
| OpenAI 5xx / rate limit | 重试 3 次（1/4/16s 退避）；仍失败回退到纯量化预测 |
| OpenAI 返回非合法 JSON | structured output 已强约束；万一失败按 5xx 处理 |
| Web 搜索 API 异常或空结果 | LLM 仍跑，prompt 标「无可用新闻」，`adjustment` clip 到 ±0.05 |
| Binance Spot API 异常 | QuantModel 用最近一次缓存 spot+vol，`model_version` 加后缀 `-stale-spot` |
| 飞书 webhook 4xx/5xx | 重试 3 次（10/30/60s）；仍失败永久标记，UI 红条 |
| 市场被 Polymarket 撤下 | 下次 discover/repredict 时检测到 `active=false` 或 `condition_id` 消失 → 强制 EXPIRED |
| 手动 URL 不可解析或非 BTC/非二元 | API 返回 422 + 错误码（`URL_INVALID` / `MARKET_NOT_SUPPORTED` / `MARKET_NOT_BINARY`） |
| 同一市场重复发现/手动添加 | UNIQUE 约束保护，返回 409 |
| 用户改设置时把 `price_poll_minutes` 改到 < 1 | 后端校验拒绝，前端表单 inline 错误 |
| docker-compose 重启 | APScheduler 重启后从 setting 表读最新间隔，已 ENTERED_* 的市场保持原状态继续监控 |
| 同时跑了 2 个后端实例 | v1 不支持，README 注明；DB 行锁可避免重复推送但状态会乱 |

---

## 7. Future Scope（明确不进 v1）

- 直接接 Polymarket CLOB 下单 API + 钱包，进入「全自动套利」
- 多结果市场（≥3 outcomes）支持
- 多资产（ETH/SOL/...）、配置多套关键词与对应现货 API
- 止损推送：ENTERED_* 状态下市场反向走、扩大亏损时告警
- 多通知通道（Telegram、Discord、邮件、企微）
- 历史预测准确率打分 + 模型 A/B 对比
- WebSocket 接 Polymarket 实时价格代替轮询
- 多账户/多 webhook 配置（按市场分组推送到不同群）
- 移动端 PWA
- 真正的 CI/CD、多环境部署

---

## 8. 词汇表

| 术语 | 含义 |
|------|------|
| Polymarket | 一家预测市场平台，用户对未来事件买卖份额，价格 ≈ 概率 |
| 二元市场 | 仅 YES / NO 两种结果的市场（如「BTC above $108K on May 17?」） |
| condition_id | Polymarket 内部市场唯一标识（基于合约层 conditional token） |
| Gamma API | Polymarket 的 REST API，主要提供市场元数据（无需鉴权读） |
| CLOB API | Polymarket 的撮合层 API，提供订单簿与成交（midpoint 读不需鉴权） |
| YES 份额价 (`p_mkt`) | 当前市场上 1 份 YES 份额的成交价（$0–$1，近似当前市场认为的事件概率） |
| AI 预测 (`p_ai`) | 本系统输出的 YES 概率预测（[0.001, 0.999]） |
| 量化预测 (`p_quant`) | 仅用 BTC 现货 + 历史波动率算出的基础概率（对数正态假设） |
| LLM 调整 (`llm_adjustment`) | 在 `p_quant` 基础上的 LLM 加减量（[-0.30, 0.30]） |
| 价差 (`gap`) | `p_ai - p_mkt`，正数表示看涨 YES，负数表示看跌 YES |
| 入场阈值 (`entry_threshold`) | `|gap|` 大于此值时触发入场信号，默认 0.15（15pp） |
| 去抖窗口 (`debounce_minutes`) | 同一市场两次状态变更之间最少间隔，默认 10 分钟 |
| 状态机 | WATCHING / ENTERED_LONG / ENTERED_SHORT / EXPIRED 四态 |
| 入场信号 | 价差超过阈值，模型建议建仓 |
| 兑现信号 | 市场价已走到模型预测点，模型建议平仓 |
| Skim/Slug | Polymarket URL 路径里的 slug，如 `bitcoin-above-on-may-17` |
| pp | percentage point，百分点；20pp = 0.20 的概率差 |

---

文档结束。实现详见 `backend-PRD.md` 与 `frontend-PRD.md`。
