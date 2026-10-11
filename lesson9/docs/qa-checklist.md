# Polymarket BTC 套利信号工具 · QA 验收清单

> 文档版本：v1.0
> 编写日期：2026-05-18
> Owner: QA
> 用途：发版前人工逐项打勾验收；周一上午冒烟巡检；新 RC 候选构建质检

---

## 0. 使用说明

- 每一项的 **「通过条件」** 写得很严格，**任何一条不满足都打 FAIL**，记录原因。
- 不区分「主路径」与「边角路径」，全部都验。
- 配合 `scripts/smoke.sh` 一起跑：smoke.sh 自动跑机器可读部分，本 checklist 跑 UI / 体感部分。
- 跑完把 PASS/FAIL 统计写在文末「本次结果」。
- 跑出 FAIL 必须开 issue（GitHub 或 Linear）登记，把 issue 编号填到「跟踪」列。

---

## 1. 启动与健康检查（5 项）

| # | 步骤 | 预期结果 | 通过条件 | 跟踪 |
|---|------|----------|----------|------|
| 1.1 | 干净环境 `docker compose up -d` | 5 个 compose 服务 30s 内变 healthy | `docker compose ps` 全列 healthy | |
| 1.2 | `curl localhost:8000/api/v1/healthz` | 200 + `{"status":"ok"}` | jq 解析 `.status=="ok"` | |
| 1.3 | `curl localhost:8000/api/v1/readyz` | 200 + 6 components 全 ok | `.status=="ok"` 且 `.components.*` 无 "fail" | |
| 1.4 | 浏览器开 `localhost:3000` | 302 跳到 `/dashboard`，1 秒内渲染 | 顶栏 ₿ logo + 4 个导航项 + 右侧绿灯 | |
| 1.5 | 关掉 backend 容器后刷 `/dashboard` | 顶部红 banner「无法连接后端」 | banner 含可见错误信息 + 重试按钮 | |

---

## 2. 仪表盘 `/dashboard`（7 项）

| # | 步骤 | 预期结果 | 通过条件 | 跟踪 |
|---|------|----------|----------|------|
| 2.1 | 数据库已有 ≥ 3 个 WATCHING 市场 → 打开仪表盘 | 4 个 KPI tile + 3 张以上市场卡片 | KPI 数字与 DB 实际行数一致 | |
| 2.2 | KPI tile「未推送」有未推送 signal_event 时 | 数字显红色 | 字色 `text-rose-600 font-semibold` | |
| 2.3 | 一张 ENTERED_LONG 卡片 | 左边框橙色 `border-l-4 border-amber-500` | 颜色与 §6.1 色板一致 | |
| 2.4 | 一张距 resolve_at < 1h 的市场 | 右上角紫色「临近结算」徽章 | 文案准确，颜色 violet | |
| 2.5 | 一张 `metadata.stale=true` 的市场 | 整张卡灰显 + 悬停 tooltip「价格数据异常」 | 透明度可见区分 | |
| 2.6 | 静置 30s | 自动 refetch，KPI 与卡片刷新无视觉抖动 | 无闪烁、无 spinner 全屏遮罩 | |
| 2.7 | 点击任意卡片 | 跳 `/markets/{id}`，URL 含真实 id | 浏览器 history 正确 | |

---

## 3. 市场详情 `/markets/[id]`（8 项）

| # | 步骤 | 预期结果 | 通过条件 | 跟踪 |
|---|------|----------|----------|------|
| 3.1 | 进入一个有 ≥ 5 条 prediction + ≥ 50 条 tick 的市场 | 双线图渲染完整 | 1s 内完成首屏 | |
| 3.2 | y 轴固定 0–1，5 个 tick (0/0.25/0.5/0.75/1) | 不出现「自动缩放」 | 视觉断言 | |
| 3.3 | AI 线 amber 阶梯插值（`stepAfter`） | 颜色与样式与 §6.4 一致 | 视觉断言 | |
| 3.4 | Market 线 blue 平滑 | 同上 | 视觉断言 | |
| 3.5 | 鼠标 hover 图表 | 十字线 + tooltip 同时显示两条 series + 价差 | tooltip 字段齐全 | |
| 3.6 | 点击「立即重跑预测」 | 30s 内右侧 PredictionCard 数字更新 + Toast「预测已更新」 | model_version 时间戳变化 | |
| 3.7 | 点击右上垃圾桶 → 二次确认 → 删除 | 跳回 `/dashboard`，该市场消失 | DB 该 market.state='EXPIRED' | |
| 3.8 | 访问不存在的 id（`/markets/999999`） | 404 页 | 不渲染骨架 | |

---

## 4. 手动预测 `/predict`（6 项）

| # | 步骤 | 预期结果 | 通过条件 | 跟踪 |
|---|------|----------|----------|------|
| 4.1 | 贴一个合法 Polymarket BTC 二元市场 URL → 「试一次」 | 30s 内展示 AI 概率条 + 量化基础 + LLM 调整 + 理由 + 新闻列表 | 所有字段非空 | |
| 4.2 | 贴非 polymarket.com 域名 URL（如 `https://example.com/event/x`） | 输入框下方 inline 红字错误，不发请求 | 网络面板无请求 | |
| 4.3 | 贴合法 URL 但路径不含 `/event/` 或 `/market/` | 同上 inline 拒绝 | 同上 | |
| 4.4 | 贴一个非 BTC 市场（如 ETH/SOL） | 「试一次」请求返回 422，Toast 显示 `MARKET_NOT_SUPPORTED` | 错误码可见 | |
| 4.5 | 「试一次」成功后点「加入监控并定时跟踪」 | 跳 `/markets/{new_id}`，dashboard 也能看到新卡 | DB 有新 market 行 | |
| 4.6 | 重复加入同一 URL | Toast「该市场已存在，点击跳转」+ 跳转链接 | 后端 409 处理正确 | |

---

## 5. 推送历史 `/history`（5 项）

| # | 步骤 | 预期结果 | 通过条件 | 跟踪 |
|---|------|----------|----------|------|
| 5.1 | DB 有 ≥ 50 条 signal_event → 打开历史页 | 50 条/页表格，200ms 内首屏 | 含分页控件 | |
| 5.2 | 筛选「近 7 天」+「ENTRY_LONG」 | 表格只显示符合条件行 | 表头按钮高亮 | |
| 5.3 | 自定义时间区间（DatePicker） | 起止时间过滤生效 | 边界包含 | |
| 5.4 | 点击任意行 | 半屏 Dialog 展示完整 signal_event：完整 prediction 快照、推送时间、错误信息、卡片预览 | 字段齐全 | |
| 5.5 | 点击「导出 CSV」 | 浏览器下载文件，文件名含时间戳 | UTF-8 BOM 中文不乱码 | |

---

## 6. 设置 `/settings`（10 项）

| # | 步骤 | 预期结果 | 通过条件 | 跟踪 |
|---|------|----------|----------|------|
| 6.1 | ① 监控参数：把 entry_threshold 从 0.150 改 0.250 → 保存 | Toast「保存成功」 | DB setting.entry_threshold = 0.250 | |
| 6.2 | 同上保存后，下一轮 SignalEngine 用 0.250 判断 | 之前会触发的 gap +0.20 不再触发 | 跑 trigger 验证 | |
| 6.3 | ① 改 price_poll_minutes=1（≥1） | 保存成功 + APScheduler 60s 内切到新间隔 | `/scheduler/jobs` 显示 interval_minutes=1 | |
| 6.4 | ① 改 price_poll_minutes=0（越界） | 表单 inline 红字 + 保存按钮禁用 | 不发请求 | |
| 6.5 | ② 关键词 从 `bitcoin/btc` 改 `ethereum` → 保存 | 下次 daily_discovery 抓 ETH 市场 | trigger 手动验证 | |
| 6.6 | ③ OpenAI Model 改 `gpt-X`（任意值） → 保存 | DB 写入新值，下次预测 prompt 用新模型 | API 调用日志确认 | |
| 6.7 | ③ OpenAI Key 字段默认 mask，点「修改」可输入 | 输入后保存，再 GET /settings 仍 mask | DB 明文存储 | |
| 6.8 | ④ Webhook URL 改成错误地址 → 「发送测试卡片」 | Toast「❌ 失败: <reason>」 | 4xx 错误码可见 | |
| 6.9 | ④ Webhook 恢复正确 → 「发送测试卡片」 | Toast「✅ 飞书可达」+ 飞书群收到样板卡 | 人工验证 | |
| 6.10 | ⑤ 调度状态：5 个 job 全列出 + 下次运行时间 | 每行有「手动触发」按钮 | 点击后 5s 内「最近运行」展开新行 | |

---

## 7. 飞书推送（6 项）

> 这部分必须真实飞书群验证；不能仅看 DB feishu_pushed=true。

| # | 步骤 | 预期结果 | 通过条件 | 跟踪 |
|---|------|----------|----------|------|
| 7.1 | smoke.sh STEP 5+6 触发 ENTRY_LONG | 飞书群收到橙底「🟠 入场信号 · 看涨 (买 YES)」卡 | 卡片渲染无异常 | |
| 7.2 | 卡片字段：市场名（链接） / AI 预测 vs 市场价 / 价差 / 模型版本 / 置信度 / LLM 理由（可折叠展开） / 剩余时间 | 全部齐全 | 逐项核对 | |
| 7.3 | 卡片底部两个按钮「查看市场」「打开仪表盘详情」 | 第一个跳 Polymarket event；第二个跳 `localhost:3000/markets/{id}` | 浏览器跳转正确 | |
| 7.4 | 手动触发 EXIT_LONG（psql 把 p_ai 调到 < 当前 mid 后 trigger price_poll） | 飞书群收到绿底「✅ 兑现信号 · 平 YES」 | 颜色与文案正确 | |
| 7.5 | 手动构造 ENTRY_SHORT（psql 把 p_ai 调到 mid - 0.25） | 飞书群收到红底「🔴 入场信号 · 看跌 (买 NO)」 | 同上 | |
| 7.6 | 关 backend 后再起，待自动重试一次 | 之前失败的卡片在「最多 24h 内」补推到 | 飞书群确实收到 | |

---

## 8. 调度器（5 项）

| # | 步骤 | 预期结果 | 通过条件 | 跟踪 |
|---|------|----------|----------|------|
| 8.1 | `GET /scheduler/jobs` | 返回 5 个 job 名 + next_run_at | 数量精确为 5 | |
| 8.2 | `POST /scheduler/trigger {"job":"daily_discovery"}` | 200 + job_run_id；几秒后 `/scheduler/runs?job_name=daily_discovery` 多一行 | status='success' 或 'running' | |
| 8.3 | `POST /scheduler/trigger {"job":"ai_repredict","market_id":X}` | 200 + 该 market 后续有新 prediction 行 | created_at 在调用之后 | |
| 8.4 | docker compose restart backend | APScheduler 重启后 5 个 job 自动从 setting 表恢复间隔；已 ENTERED_* 的 market 保持原 state | psql 验证 + `/scheduler/jobs` 验证 | |
| 8.5 | 故意改 setting.price_poll_minutes 之后 60s 内 | 下次 tick 用新间隔 | `next_run_at` 反映 | |

---

## 9. 错误与降级（6 项）

> 用 .env 把对应 key 改坏 / 用 docker network 拔掉服务模拟。

| # | 故障 | 预期降级行为 | 通过条件 | 跟踪 |
|---|------|--------------|----------|------|
| 9.1 | OpenAI key 改错 | 新 prediction 仍生成，但 `model_version` 含 `-llm-fail`，`llm_adjustment=0`，`llm_confidence='low'` | 详情页 PredictionCard 标「LLM 调整不可用」 | |
| 9.2 | Binance 不可达（防火墙阻断 api.binance.com） | 新 prediction 仍生成，`model_version` 含 `-stale-spot` | 详情页标「现货数据滞后」 | |
| 9.3 | Tavily key 改错 | 新 prediction 仍生成，`news_sources=[]`，`llm_adjustment` 被 clip 到 ±0.05 | 详情页「无近期新闻」 | |
| 9.4 | Polymarket CLOB 不可达 | 单 tick 失败；连续 6 次后 market 卡片灰显 | UI 仪表盘可见 | |
| 9.5 | 飞书 webhook 改错 | 推送重试 3 次后 `feishu_pushed=false`，`feishu_error` 非空；KPI 显「未推送 N」红色 | 仪表盘可见 | |
| 9.6 | 9.5 之后修好 webhook，等 10 分钟（或 trigger feishu_retry） | 失败信号被自动重推成功 | DB feishu_pushed=true | |

---

## 10. 时区与时间（4 项）

| # | 步骤 | 预期结果 | 通过条件 | 跟踪 |
|---|------|----------|----------|------|
| 10.1 | API 响应所有 timestamp 字段 | 必带 `Z` 后缀 | `jq '..|.created_at? // .occurred_at? // empty' | grep -v Z` 无输出 | |
| 10.2 | 前端列表显示相对时间「2m ago」 | `<TimeAgo>` 每 30s 自动刷新 | 观察 1 分钟有变化 | |
| 10.3 | 前端详情页绝对时间 hover tooltip | 显示 UTC 原值（含 `Z`） | hover 验证 | |
| 10.4 | 距 resolve_at = 60m00s 边界 | UI 不触发「临近结算」徽章；60m01s 才不触发；59m59s 触发 | psql 改 resolve_at 精确测 | |

---

## 11. 删除 / 危险操作（3 项）

| # | 步骤 | 预期结果 | 通过条件 | 跟踪 |
|---|------|----------|----------|------|
| 11.1 | 详情页右上垃圾桶 → 二次确认 → 取消 | 不删 | DB 该行 state 不变 | |
| 11.2 | 同上 → 确认 | 软删（state='EXPIRED'），跳 /dashboard，该卡消失 | DB state='EXPIRED' | |
| 11.3 | /settings ⑥ 数据维护「重置所有市场为 WATCHING」 | 双重确认 + 大红警告；v1 可点击但提示「该功能待开发」 | 不能误触 | |

---

## 12. 安全与密钥（4 项）

| # | 步骤 | 预期结果 | 通过条件 | 跟踪 |
|---|------|----------|----------|------|
| 12.1 | `GET /settings` 响应 | 所有 *_key / webhook_url 字段 mask（前 6 / 后 4） | jq 检查 含 `***hidden***` | |
| 12.2 | 前端 DOM 检查 | masked 字段不出现在 console.log / DOM tree 明文 | DevTools 验证 | |
| 12.3 | structlog 日志输出 | 不含 api_key / webhook_url 明文 | `docker logs backend | grep -E "sk-|tvly-|tenant_access_token"` 无输出 | |
| 12.4 | docker port mapping | 全部绑定 `127.0.0.1`，不对外暴露 | `docker compose ps` 端口列校验 | |

---

## 13. 性能（3 项）

| # | 步骤 | 目标 | 通过条件 | 跟踪 |
|---|------|------|----------|------|
| 13.1 | 仪表盘加载 100 个市场 | < 1s 首屏 | DevTools Performance | |
| 13.2 | 集成测试套件 `make test-cov` | < 5 min | `time` 命令 | |
| 13.3 | 飞书推送 p99 延迟（信号生成到送达） | < 30s | structlog `signal.fired` → `feishu.pushed` 时差 | |

---

## 14. 文档（3 项）

| # | 项 | 通过条件 | 跟踪 |
|---|------|----------|------|
| 14.1 | README.md 含「单实例运行限制」+「资金/合规风险声明」 | 文档有对应段落 | |
| 14.2 | 推送卡片 footer 含「本工具仅作个人研究信号提醒，不构成投资建议」 | 飞书群肉眼可见 | |
| 14.3 | 前端 footer 同上 | 浏览器肉眼可见 | |

---

## 15. 关键场景（PRD §2.2 的 S1–S6，与 smoke.sh STEP 8 对应）

> smoke.sh 自动跑这部分；如果跑的是「半自动手动验收」也按本节走。

| # | 场景 | 关键路径 | 通过条件 |
|---|------|----------|----------|
| S1 | 起床看信号 | 早上看飞书 → 点卡片底部「打开仪表盘详情」→ 跳 `/markets/{id}` | 跳转成功 + 详情页字段齐全 |
| S2 | 手动预测 | `/predict` 贴 URL → 「试一次」→ 「加入监控」 | 30s 内出预测，加入后 dashboard 可见 |
| S3 | 信号兑现 | 收到 EXIT_* 卡片 → 卡片字段含「市场已涨/跌到 p_ai 兑现点」 | 卡片文案准确 |
| S4 | 调参 | `/settings` 改 entry_threshold → 下一轮按新值判断 | trigger 验证生效 |
| S5 | 看历史复盘 | `/history` 看一周推送 → 筛选 + 详情展开 | 全部字段无错 |
| S6 | 排错 | 飞书没推送 → `/settings` 调度状态找原因 → 「发送测试卡片」验证 webhook | 错误信息准确 |

---

## 本次结果

| 字段 | 值 |
|------|-----|
| 验收人 | _____ |
| 验收日期（UTC） | YYYY-MM-DD |
| Backend 版本（commit hash） | _____ |
| Frontend 版本（commit hash） | _____ |
| PASS 数 / 总项数 | _____ / _____ |
| FAIL 列表 | _____ |
| 阻塞 / 关键问题 | _____ |
| 是否同意发布 | YES / NO |
| 备注 | _____ |

---

文档结束。FAIL 项必须开 issue 登记；阻塞项必须由 team-lead 签字才能发布。
