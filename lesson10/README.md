# Lesson 10 实战样例：AI Strategy Cockpit

> 课程视频回放（Lesson 10）：[点击观看](https://appibxs98ig9955.h5.xet.pomoho.com/p/course/video/v_6a2ece5ce4b0694c351949ea?product_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&course_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&sub_course_id=subcourse_3EUmreviThPpAUC2IJ1NTqoDbk5)

> 一个**黑客松级**的 AI 量化策略驾驶舱 demo：用户输入交易目标 + 风险偏好，系统一键完成市场分析、策略选择、参数微调、模拟回测、结果可视化。**讲课时这个项目本身**会承担 lesson 10 "用 Hermes Agent 做 Hyperliquid 黑客松项目" 的落地角色——它既是黑客松交付物，也是 Hermes Agent 长跑 + 多入口 + 模型无关能力的应用对象。

---

## 一句话

**输入交易目标 → AI 解释市场 + 选策略 + 调参数 → 离线回测 + 模拟交易 → 一屏驾驶舱可视化**。

不真实接交易所、不真下单——重点是**现场跑得稳、讲得清、看得懂**。

---

## 这是什么 / 为什么是这个项目

Lesson 10 主线是 **用 Hermes Agent 做 Hyperliquid 黑客松项目**，本目录就是这个黑客松项目本体——一个独立的 Next.js webapp，叫 **AI Strategy Cockpit**（中文：AI 策略驾驶舱）。

它在课程里扮演两个角色：

1. **黑客松交付物**——一屏 Web UI，演示"AI 看盘 + 出策略 + 跑回测"的全链路，符合 Hyperliquid 主题（永续合约 + 链上数据）。
2. **Hermes Agent 的应用对象**——课堂上讲师会用 Hermes Agent 长跑、跨平台、多模型的能力来**辅助这个项目**：定时拉数据、Telegram 推送策略信号、不同 LLM 切换对比效果。Hermes Agent 本身不是这个 repo 的代码，而是**外挂在这个项目周围的运维 / 决策层**。

> **划重点**：这个 demo **故意不让 LLM 自己写交易逻辑**——回测和模拟交易由**确定性代码**执行，LLM 只负责**解读市场 + 在预置策略里选 + 微调少量参数**。这是黑客松级 demo 的常见安全设计：让 LLM 做它擅长的（语义、解释），让代码做它擅长的（确定性数值计算）。

---

## 快速跑通

### 前置

- Node.js ≥ 18（项目用了 `"type": "module"` 和 Node 自带 `--test`）
- 一个能用的 LLM key（默认走 AIHUBMIX 聚合层；详见下一节）

### 启动

```bash
cd lesson10
npm install          # 装依赖
cp .env.local.example .env.local   # （没有 example 就直接编辑 .env.local）
# 编辑 .env.local 填入 AIHUBMIX_API_KEY
npm run dev          # http://localhost:3000
```

期望：浏览器打开 `http://localhost:3000` 看到一屏驾驶舱 UI，输入"做 BTC 趋势策略 / 风险偏好平衡"后能拿到一段 AI 解读 + 策略卡片 + 模拟收益曲线。

### 跑测试

```bash
npm test
```

走 Node 内置 test runner（`node --test tests/*.test.mjs`），跑 4 份测试：`engine` / `click-behavior` / `llm-advisor` / `ui-copy`。

### 刷新历史数据

```bash
python scripts/download-hyperliquid-candles.py
```

从 Hyperliquid API 拉 BTC / ETH / SOL 日 K，覆盖 `data/*.csv`。**没有 key 也能跑**——`data/` 下已经预置了一份 CSV，前端默认用它。

---

## 项目结构

```
lesson10/
├── README.md                              ← 你在读
├── package.json                           ← Next.js 15 + TS + ESM
├── tsconfig.json
├── next.config.mjs
├── .env.local                             ← LLM key（不进版本库）
│
├── docs/
│   ├── ai-strategy-cockpit-prd.md         ← 完整 PRD，1000+ 行
│   └── hyperliquid-intro.md               ← Hyperliquid 新手介绍
│
├── data/                                  ← Hyperliquid 历史 K 线 CSV
│   ├── BTC.csv
│   ├── ETH.csv
│   └── SOL.csv
│
├── src/
│   ├── app/
│   │   ├── layout.tsx                     ← 全局布局
│   │   ├── page.tsx                       ← 驾驶舱主页（一屏 UI）
│   │   ├── globals.css
│   │   └── api/
│   │       └── run-strategy/
│   │           └── route.js               ← POST /api/run-strategy
│   └── lib/
│       └── engine.mjs                     ← 策略 + 回测引擎（核心）
│
├── tests/
│   ├── engine.test.mjs                    ← 引擎正确性
│   ├── llm-advisor.test.mjs               ← LLM 调用
│   ├── click-behavior.test.mjs            ← UI 交互
│   └── ui-copy.test.mjs                   ← 文案一致性
│
└── scripts/
    └── download-hyperliquid-candles.py    ← 数据拉取脚本
```

---

## 三大策略 + 三种风险偏好

引擎层（`src/lib/engine.mjs`）预置了 **3 策略 × 3 风险档** = 9 种组合。LLM 不能自创策略，只能在这 9 种里选 + 微调允许的参数。

### 策略

| 策略 | 何时用 | 关键参数 |
|---|---|---|
| `trend_following` | 行情明显单边、突破 | 快慢均线交叉（`fastMA` / `slowMA`） |
| `rsi_mean_reversion` | 行情震荡、超买超卖明显 | RSI 阈值 |
| `bollinger_bands` | 波动率扩张 / 突破带 | 上下轨标准差倍数 |

### 风险偏好

| 偏好 | positionSize | stopLoss | fastMA | slowMA | window |
|---|---|---|---|---|---|
| `conservative` | 0.4（4 成仓） | 3% | 12 | 36 | 40 |
| `balanced` | 0.6（6 成仓） | 4% | 10 | 30 | 30 |
| `aggressive` | 0.8（8 成仓） | 6% | 7 | 21 | 20 |

LLM 会根据"目标 + 行情 + 风险偏好"在 3 策略里选一个、并在风险档基础上做少量微调（在允许范围内）。

---

## 数据：Hyperliquid 历史 K 线

`data/BTC.csv`、`ETH.csv`、`SOL.csv` 是从 Hyperliquid 拉的日级 OHLCV。

- **没装 Python / 没有网**：直接用 repo 里预置的 CSV
- **想刷新**：`python scripts/download-hyperliquid-candles.py`

如果你完全没数据（CSV 也丢了），引擎里还有 `generateMockCandles()` 兜底——会生成一段带趋势 + 周期 + 突破的合成 K 线，保证现场至少能演示。

---

## LLM 接入：AIHUBMIX 聚合层

默认走 [AIHUBMIX](https://aihubmix.com) 作为模型聚合层——**一个 key 调多家 LLM**（OpenAI / Anthropic / Google / 国产模型都行）。

配 `.env.local`：

```env
AIHUBMIX_API_KEY=sk-...
AIHUBMIX_BASE_URL=https://aihubmix.com/v1
AIHUBMIX_MODEL=gpt-5.5
```

要切模型只改 `AIHUBMIX_MODEL` 这一行——`claude-opus-4-7` / `gemini-2.5-pro` / `qwen3-max` 都行。

> **黑客松小技巧**：现场可以**切两个模型对比效果**——让观众看到同一个市场环境下 GPT 和 Claude 给出的策略选择不一样。这刚好和 lesson 7 / lesson 10 都强调的"模型无关"主题对得上。

---

## API

### `POST /api/run-strategy`

请求体：

```json
{
  "symbol": "BTC",
  "riskProfile": "balanced",
  "goal": "capture_trend"
}
```

- `symbol`: `BTC` / `ETH` / `SOL`
- `riskProfile`: `conservative` / `balanced` / `aggressive`
- `goal`: 自由文本（描述交易目标）

响应：策略卡片 + 模拟回测结果 + AI 解读。

### `GET /api/run-strategy`

无参快速调用——默认 `BTC + balanced + capture_trend`，调试用。

---

## 测试

```bash
npm test
```

4 份测试：

| 文件 | 守什么 |
|---|---|
| `engine.test.mjs` | 策略引擎正确性（指标计算、回测逻辑） |
| `llm-advisor.test.mjs` | LLM 调用、参数校验、降级（key 缺失时 mock） |
| `click-behavior.test.mjs` | UI 关键交互不挂 |
| `ui-copy.test.mjs` | 关键文案一致性 |

用 Node 内置 `--test`，不依赖 Vitest / Jest。

---

## 与 Lesson 10（Hermes Agent）的关系

Lesson 10 主线讲 **Hermes Agent**——开源、自托管、跨平台、模型无关的长跑 agent。本项目（AI Strategy Cockpit）是 Hermes 的**应用对象**。

课堂演示可能的玩法：

| Hermes 能力 | 应用到本项目 |
|---|---|
| 跨平台入口（Telegram / Slack / ...） | 把策略信号定时推到 Telegram |
| 持久记忆（MEMORY.md / USER.md / FTS5） | 记录历史的策略选择 + 用户偏好，下次自动复用 |
| 模型无关 / `/model` 切换 | 同一信号让两家 LLM 各跑一遍，对比给出 confidence |
| 定时自动化（cron） | 每天早上 8 点自动跑一次驾驶舱、推前日复盘 |
| MCP 协议外挂 | Hermes 通过 MCP 调本项目的 API / 数据 / engine |

**核心理念**：本项目本身**不依赖 Hermes** 也能跑（独立 Next.js 应用，直接调 LLM）。Hermes 作为**外挂层**为它加上长跑 + 多入口能力——这刚好演示了 Hermes 的设计哲学：**它是给已有项目加 agent 能力的 layer，不是替换**。

---

## 与课程其它课的关系

| 课 | 学的能力 | 在本项目里怎么体现 |
|---|---|---|
| L1 | Claude / Cursor 工具 | 整个项目都是 AI 辅助写的 |
| L3 | MCP | Hermes 通过 MCP 调本项目 |
| L4 | Skill 设计 | 策略选择 / 风险评估可以沉淀成 Hermes skill |
| L5 | OpenSpec / Spec 驱动 | `docs/ai-strategy-cockpit-prd.md` 就是一份完整 spec |
| L6 | Harness / plan 文件 | 黑客松迭代过程可以用 plan 文件管 |
| L7 | Agent Teams / Hermes | **本项目演示 Hermes 应用** |
| L8 | Superpowers | 项目从 0 到 1 用 Superpowers 跑通 |
| L9 | Claude Agent Teams | 黑客松用 Agent Teams 协同（参见 L9 项目）|
| L10 | **本课**：Hermes 服务 Hyperliquid 项目 | 就是这个项目 |

---

## 常见问题

**Q: 跑 `npm run dev` 报 `AIHUBMIX_API_KEY is not defined`？**
A: `.env.local` 没建或 key 没填。最快验证不依赖 LLM 的部分：`npm test` 跑通 engine 测试就证明核心逻辑没问题。

**Q: AIHUBMIX 慢或拒绝？**
A: 改 `AIHUBMIX_BASE_URL` 走 OpenAI / Anthropic 原生 endpoint（设 `OPENAI_API_KEY` 之类的环境变量也支持，看 `engine.mjs` 的 fallback 逻辑）。

**Q: 想加新策略？**
A: 改 `src/lib/engine.mjs` 的 `STRATEGIES` 数组 + 加对应的纯函数实现。**不要让 LLM 在 prompt 里自己生成策略代码**——确定性引擎是这个项目的安全护栏。

**Q: 数据 CSV 怎么解读？**
A: 标准 OHLCV 列：`timestamp, open, high, low, close, volume`，按日聚合。

**Q: 现场 demo 网断了 / API 挂了？**
A: 引擎自带 `generateMockCandles()` 兜底——把 `data/*.csv` 临时移走，engine 会自动用合成数据，UI 仍然能跑。这是 PRD §18 风险与应对里的设计。

---

## 延伸阅读

- [`docs/ai-strategy-cockpit-prd.md`](./docs/ai-strategy-cockpit-prd.md) —— 1000+ 行的完整 PRD（20 个 section，含 demo 脚本、验收标准、风险与应对）
- [`docs/hyperliquid-intro.md`](./docs/hyperliquid-intro.md) —— Hyperliquid 新手向科普
- [Hyperliquid 官网](https://hyperliquid.xyz) —— 数据源 + 永续合约平台
- [AIHUBMIX](https://aihubmix.com) —— LLM 聚合层
- Lesson 7 README —— Hermes Agent 完整介绍

---

## 免责声明

本项目**仅为黑客松级 demo + 教学样例**。不构成投资建议、不接真实交易、不保证策略盈利。链上衍生品交易存在爆仓与不可逆操作风险，参与前请阅读官方文档并自行判断。
