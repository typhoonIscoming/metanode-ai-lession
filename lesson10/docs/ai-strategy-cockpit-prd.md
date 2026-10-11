# AI Strategy Cockpit PRD

> **产品类型：** 黑客松 Demo 型 AI 量化交易策略驾驶舱  
> **目标目录：** `lesson10/docs/ai-strategy-cockpit-prd.md`  
> **版本：** v1.0  
> **状态：** MVP PRD  
> **核心原则：** 现场稳定、视觉完整、讲解清楚、避免真实交易风险

---

## 1. 产品概述

### 1.1 产品名称

**AI Strategy Cockpit**

中文名：**AI 策略驾驶舱**

### 1.2 一句话定位

一个面向黑客松 Demo 的 AI 量化交易策略驾驶舱：用户输入交易目标和风险偏好后，系统一键完成市场分析、策略选择、参数建议、模拟回测和结果可视化。

### 1.3 产品目标

本项目不是要做真实自动交易系统，而是要做一个**看起来完整、讲得清楚、现场稳定**的黑客松原型。

现场观众应该能在 1-2 分钟内理解：

1. 用户可以用自然语言或表单描述交易目标；
2. 系统读取离线历史行情数据并计算基础指标；
3. LLM 解释当前市场状态、机会和风险；
4. LLM 在预置策略中选择最合适的策略，并微调少量参数；
5. 回测和模拟交易由确定性代码执行，而不是由 LLM 任意生成交易逻辑；
6. 最终结果以一屏驾驶舱形式展示，包括收益曲线、关键指标、AI 理由、策略卡片和模拟交易日志。

### 1.4 产品形态

MVP 形态为一个 Web 单页应用：

- 左侧/顶部：用户输入区；
- 中间：收益曲线和关键回测结果；
- 右侧：AI 分析与推荐策略；
- 底部：交易日志、风险提示、数据来源说明。

---

## 2. Demo 主线

### 2.1 选定方案

采用 **方案 A：一键 AI 策略驾驶舱**。

用户输入目标和风险偏好后，系统自动完成：

1. 读取离线行情数据；
2. 计算市场指标；
3. LLM 生成市场解读；
4. LLM 从 3 个预置策略中选择 1 个；
5. LLM 给出少量策略参数建议；
6. 确定性回测引擎执行模拟交易；
7. 页面展示完整驾驶舱结果。

### 2.2 黑客松成功瞬间

成功瞬间是：

> 观众看到一个像真实产品一样完整的 AI 策略驾驶舱：有输入、有图表、有 AI 理由、有策略卡、有关键指标、有交易日志，并且一键运行后稳定生成完整结果。

### 2.3 P0 核心闭环

P0 必须完成以下闭环：

1. 用户选择或输入：
   - 币种：BTC / ETH / SOL，MVP 可默认 BTC；
   - 风险偏好：保守 / 均衡 / 激进；
   - 交易目标：稳健收益 / 捕捉趋势 / 控制回撤；
2. 系统读取本地离线历史行情 CSV；
3. 系统计算基础市场指标；
4. LLM 输出市场状态解释；
5. LLM 从 3 个策略中选择 1 个：
   - 趋势跟随；
   - 均值回归；
   - 突破策略；
6. LLM 给出少量参数建议，例如窗口期、止损比例、仓位系数；
7. 回测引擎根据确定性代码运行模拟交易；
8. 页面展示：
   - 收益曲线；
   - 总收益率；
   - 最大回撤；
   - 胜率；
   - 交易次数；
   - AI 分析理由；
   - 被选中的策略卡片；
   - 模拟交易日志；
9. 页面明确标注：仅用于教学和模拟，不构成投资建议。

---

## 3. 用户与使用场景

### 3.1 目标用户

MVP 面向黑客松现场观众和课程学员：

1. **黑客松评委 / 观众**
   - 关注 Demo 是否完整、清晰、有视觉冲击；
   - 不一定理解量化交易细节；
   - 需要在短时间内看到 AI 带来的价值。

2. **课程学员 / 开发者**
   - 关注 LLM 如何参与交易策略系统；
   - 需要理解哪些部分由 AI 决策，哪些部分由确定性代码执行；
   - 需要能基于 PRD 拆分开发任务。

3. **Web3 / DeFi 爱好者**
   - 关注与 Hyperliquid、永续合约、策略交易的关联；
   - 希望看到类似真实交易终端的体验，但不承担真实资金风险。

### 3.2 核心使用场景

#### 场景 1：现场快速 Demo

演示者打开页面，选择：

- 币种：BTC；
- 风险偏好：均衡；
- 目标：捕捉趋势；

点击 **Run AI Strategy**，页面在几秒内生成完整结果。

#### 场景 2：风险偏好对比

演示者分别选择：

- 保守；
- 均衡；
- 激进；

观众可以看到 AI 推荐的策略参数、仓位系数和风险解释发生变化。

#### 场景 3：策略解释教学

演示者展开 AI 分析区，说明：

- LLM 如何读取指标摘要；
- LLM 为什么选择某个策略；
- 回测结果为什么必须由确定性代码生成；
- 为什么不能让 LLM 直接下单。

---

## 4. MVP 范围

### 4.1 MVP 必做功能

| 优先级 | 功能 | 说明 |
|---|---|---|
| P0 | 一键运行完整闭环 | 输入风险偏好与目标后生成完整驾驶舱结果 |
| P0 | 离线行情数据读取 | 使用本地 CSV，避免现场 API 风险 |
| P0 | 基础市场指标计算 | MA、收益率、波动率、回撤等 |
| P0 | LLM 市场解读 | 输出市场状态、风险、机会 |
| P0 | LLM 策略选择 | 从 3 个预置策略中选择 1 个 |
| P0 | 确定性回测引擎 | 不由 LLM 执行任意交易代码 |
| P0 | 一屏驾驶舱 UI | 图表、指标、AI 理由、策略卡、交易日志 |
| P0 | 风险免责声明 | 明确仅用于教学和模拟 |
| P1 | 风险偏好切换 | 保守 / 均衡 / 激进影响参数建议 |
| P1 | 币种切换 | BTC / ETH / SOL |
| P1 | Demo 数据兜底 | 数据缺失时使用内置 mock 数据 |
| P2 | 多策略对比 | 同时展示 3 个策略结果，仅作为增强项 |
| P2 | 导出报告 | 导出 AI 分析和回测结果 Markdown / PDF |

### 4.2 MVP 不做功能

为了保证黑客松现场稳定，MVP 明确不做：

- 不接真实交易下单；
- 不做钱包连接；
- 不处理真实资金；
- 不依赖实时行情 API；
- 不让 LLM 直接生成并执行任意交易代码；
- 不做复杂用户系统；
- 不做策略市场或策略上传；
- 不做多账户、多资产组合管理；
- 不承诺收益，不输出投资建议。

---

## 5. 用户流程

### 5.1 主流程

```text
打开页面
  ↓
选择币种、风险偏好、交易目标
  ↓
点击 Run AI Strategy
  ↓
系统读取离线行情数据
  ↓
系统计算市场指标摘要
  ↓
LLM 生成市场解读、策略选择和参数建议
  ↓
回测引擎执行确定性模拟交易
  ↓
驾驶舱展示收益曲线、指标、AI 理由、交易日志
  ↓
用户可切换输入再次运行
```

### 5.2 异常流程

#### 数据文件不存在

- 系统提示：`未找到本地行情数据，已切换到内置演示数据。`
- 使用内置 mock 数据继续完成 Demo。

#### LLM 调用失败

- 系统提示：`AI 分析服务暂不可用，已使用规则引擎生成策略建议。`
- 使用本地规则兜底：
  - 高趋势强度 → 趋势跟随；
  - 高波动且价格偏离均线 → 均值回归；
  - 突破近期高点/低点 → 突破策略。

#### 回测结果为空

- 系统提示：`当前参数未触发交易，已放宽阈值重新运行。`
- 自动使用兜底参数重新回测一次。

---

## 6. 页面结构：一屏驾驶舱

### 6.1 信息架构

页面采用一屏驾驶舱结构：

```text
┌──────────────────────────────────────────────────────────────┐
│ Header: AI Strategy Cockpit / Demo Mode / Risk Disclaimer     │
├──────────────────────────────────────────────────────────────┤
│ Input Bar: Symbol | Risk Profile | Goal | Run Button          │
├───────────────────────────────┬──────────────────────────────┤
│ Main Chart                    │ AI Analysis Panel             │
│ - Equity curve                │ - Market summary              │
│ - Price curve                 │ - Strategy reason             │
│ - Buy/Sell markers            │ - Parameter suggestion         │
├───────────────────────────────┼──────────────────────────────┤
│ Metrics Cards                 │ Strategy Card                 │
│ - Total return                │ - Selected strategy            │
│ - Max drawdown                │ - Risk level                   │
│ - Win rate                    │ - Position sizing              │
│ - Trade count                 │ - Stop loss / take profit      │
├───────────────────────────────┴──────────────────────────────┤
│ Trade Log / Simulation Timeline / Disclaimer                  │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 顶部 Header

展示内容：

- 产品名：AI Strategy Cockpit；
- 状态标签：Demo Mode；
- 数据标签：Offline Historical Data；
- 风险提示：Simulation Only, Not Financial Advice。

### 6.3 输入区

字段：

1. **Symbol**
   - BTC；
   - ETH；
   - SOL；
   - MVP 默认 BTC。

2. **Risk Profile**
   - Conservative / 保守；
   - Balanced / 均衡；
   - Aggressive / 激进。

3. **Goal**
   - Stable Growth / 稳健收益；
   - Capture Trend / 捕捉趋势；
   - Control Drawdown / 控制回撤。

4. **Run AI Strategy**
   - 主按钮；
   - 点击后触发完整流程；
   - Loading 状态文案：
     - `Reading market data...`
     - `Analyzing market regime...`
     - `Selecting strategy...`
     - `Running backtest...`
     - `Rendering cockpit...`

### 6.4 主图表区

展示：

- 资产价格曲线；
- 策略权益曲线；
- 可选基准曲线：Buy & Hold；
- 买入 / 卖出标记；
- 鼠标 hover 显示日期、价格、权益、动作。

视觉重点：

- 收益曲线要清晰；
- 当前选中策略颜色突出；
- 交易点不宜过多，避免页面混乱。

### 6.5 指标卡片区

至少展示：

1. **Total Return / 总收益率**
   - 示例：`+18.4%`

2. **Max Drawdown / 最大回撤**
   - 示例：`-6.2%`

3. **Win Rate / 胜率**
   - 示例：`58.3%`

4. **Trades / 交易次数**
   - 示例：`24`

5. **Sharpe-like Score / 简化夏普分数**（可选）
   - 示例：`1.21`

### 6.6 AI 分析面板

展示结构：

```markdown
### Market Regime
当前市场处于中等波动的上升趋势，价格位于中长期均线上方，短期动量增强。

### Opportunity
趋势延续概率较高，适合使用趋势跟随策略捕捉上涨段。

### Risk
近期波动率上升，若价格跌破短期均线，应降低仓位或触发止损。

### Why This Strategy
基于用户选择的“均衡风险偏好”和“捕捉趋势”目标，系统推荐趋势跟随策略。
```

要求：

- 语言要自然；
- 不承诺收益；
- 不出现“必然上涨”“稳赚”等表述；
- 必须强调模拟与风险。

### 6.7 策略卡片

展示被选中策略：

- 策略名称；
- 策略类型；
- 适用市场；
- 推荐原因；
- 参数建议；
- 风险等级。

示例：

```text
Selected Strategy: Trend Following
Market Fit: Trending / Medium Volatility
Parameters:
- Fast MA: 10
- Slow MA: 30
- Stop Loss: 4%
- Position Size: 60%
Risk Level: Medium
```

### 6.8 交易日志

展示模拟交易事件：

| 时间 | 动作 | 价格 | 仓位 | 原因 |
|---|---:|---:|---:|---|
| 2024-03-01 | BUY | 62400 | 60% | Fast MA crossed above Slow MA |
| 2024-03-08 | HOLD | 68120 | 60% | Trend remains intact |
| 2024-03-15 | SELL | 70210 | 0% | Stop condition / signal exit |

MVP 至少展示最近 5-10 条事件。

---

## 7. 策略设计

### 7.1 策略框架

策略需要设计成可插拔结构。每个策略暴露统一接口：

```text
StrategyInput:
- candles: OHLCV[]
- parameters: StrategyParameters
- riskProfile: conservative | balanced | aggressive

StrategyOutput:
- signals: Signal[]
- trades: Trade[]
- equityCurve: EquityPoint[]
- metrics: BacktestMetrics
```

每个策略只负责生成交易信号；回测、仓位计算、手续费、指标统计由统一回测引擎处理。

### 7.2 策略 1：趋势跟随

适用场景：

- 市场有明显趋势；
- 价格位于中长期均线上方或下方；
- 适合“捕捉趋势”目标。

基础逻辑：

- 短期均线上穿长期均线 → 买入；
- 短期均线下穿长期均线 → 卖出；
- 可结合止损和仓位限制。

参数：

| 参数 | 保守 | 均衡 | 激进 |
|---|---:|---:|---:|
| Fast MA | 12 | 10 | 7 |
| Slow MA | 36 | 30 | 21 |
| Position Size | 40% | 60% | 80% |
| Stop Loss | 3% | 4% | 6% |

### 7.3 策略 2：均值回归

适用场景：

- 市场震荡；
- 价格偏离均线后有回归倾向；
- 适合“控制回撤”或“稳健收益”目标。

基础逻辑：

- 价格显著低于均线 → 买入；
- 价格回到均线附近或高于均线 → 卖出；
- 高波动时降低仓位。

参数：

| 参数 | 保守 | 均衡 | 激进 |
|---|---:|---:|---:|
| Lookback Window | 30 | 20 | 14 |
| Entry Z-score | -2.0 | -1.5 | -1.2 |
| Exit Z-score | -0.2 | 0 | 0.3 |
| Position Size | 30% | 50% | 70% |

### 7.4 策略 3：突破策略

适用场景：

- 价格突破近期高点或低点；
- 市场波动扩大；
- 适合捕捉大波动行情。

基础逻辑：

- 价格突破 N 日高点 → 买入；
- 价格跌破 N 日低点或触发止损 → 卖出；
- 可结合成交量或波动率过滤。

参数：

| 参数 | 保守 | 均衡 | 激进 |
|---|---:|---:|---:|
| Breakout Window | 40 | 30 | 20 |
| Position Size | 35% | 55% | 75% |
| Stop Loss | 3% | 5% | 8% |
| Volatility Filter | Strict | Normal | Loose |

---

## 8. LLM 设计

### 8.1 LLM 的职责

LLM 负责：

1. 解释市场状态；
2. 根据指标摘要和用户偏好选择策略；
3. 给出少量参数建议；
4. 输出对人友好的理由；
5. 生成风险提示。

LLM 不负责：

- 不直接生成可执行交易代码；
- 不直接下单；
- 不承诺收益；
- 不绕过回测引擎；
- 不修改系统安全边界。

### 8.2 LLM 输入

LLM 输入应是结构化摘要，而不是完整原始行情。

示例：

```json
{
  "symbol": "BTC",
  "riskProfile": "balanced",
  "goal": "capture_trend",
  "marketSummary": {
    "latestPrice": 68420,
    "return30d": 0.124,
    "volatility30d": 0.038,
    "maxDrawdown30d": -0.071,
    "maFast": 67120,
    "maSlow": 64200,
    "trendStrength": "high",
    "regime": "uptrend_medium_volatility"
  },
  "availableStrategies": [
    "trend_following",
    "mean_reversion",
    "breakout"
  ]
}
```

### 8.3 LLM 输出 Schema

LLM 必须输出可解析 JSON：

```json
{
  "marketRegime": "uptrend_medium_volatility",
  "summary": "The market is in a medium-volatility uptrend...",
  "opportunity": "Trend continuation is possible if price remains above the slow moving average.",
  "risk": "Volatility has increased, so position size should be controlled.",
  "selectedStrategy": "trend_following",
  "strategyReason": "The user's goal is to capture trend with balanced risk, and the market shows strong trend signals.",
  "parameters": {
    "fastMA": 10,
    "slowMA": 30,
    "positionSize": 0.6,
    "stopLoss": 0.04
  },
  "disclaimer": "This is a simulation for educational purposes only and is not financial advice."
}
```

### 8.4 Prompt 约束

Prompt 必须包含以下约束：

```text
You are an AI strategy analyst for an educational trading simulation.
You must only choose from the provided strategies.
You must not invent new strategies.
You must not provide financial advice.
You must not promise profits.
You must output valid JSON only.
All trading execution is handled by deterministic backtesting code.
```

### 8.5 LLM 兜底规则

如果 LLM 调用失败或输出 JSON 无法解析，使用规则引擎兜底：

1. `trendStrength = high` 且 `maFast > maSlow` → 趋势跟随；
2. `volatility high` 且价格偏离均线较大 → 均值回归；
3. 价格突破近期高点 → 突破策略；
4. 默认策略 → 趋势跟随；
5. 默认风险参数 → 根据用户 riskProfile 映射。

---

## 9. 数据设计

### 9.1 行情数据来源

MVP 使用离线历史数据包：

```text
data/
  BTC.csv
  ETH.csv
  SOL.csv
```

每个 CSV 至少包含：

```csv
timestamp,open,high,low,close,volume
2024-01-01,42000,43100,41800,42800,12345.6
```

### 9.2 数据要求

- 时间粒度：日线或小时线均可，MVP 推荐日线；
- 数据长度：至少 180 条 K 线，推荐 365 条；
- 字段必须完整；
- 数值必须可解析为数字；
- 时间戳必须可排序。

### 9.3 内置 mock 数据

为了保证 Demo 稳定，应内置一份 mock 数据生成器：

- 当 CSV 不存在时自动生成；
- 生成趋势段、震荡段、突破段；
- 保证回测能产生交易；
- 保证收益曲线视觉上有起伏。

---

## 10. 回测设计

### 10.1 回测引擎职责

回测引擎负责：

1. 根据策略信号生成模拟交易；
2. 应用仓位系数；
3. 计算权益曲线；
4. 统计关键指标；
5. 输出交易日志；
6. 确保所有结果可复现。

### 10.2 默认假设

MVP 默认：

- 初始资金：10,000 USDC；
- 只做多；
- 不使用杠杆；
- 手续费：0.05% 每笔；
- 滑点：0.02% 每笔；
- 每次只允许一个仓位；
- 不考虑资金费率；
- 不考虑真实订单簿深度。

### 10.3 指标计算

至少计算：

| 指标 | 计算说明 |
|---|---|
| Total Return | `(finalEquity - initialEquity) / initialEquity` |
| Max Drawdown | 权益曲线峰值到谷值的最大跌幅 |
| Win Rate | 盈利交易数 / 总交易数 |
| Trade Count | 完成交易数量 |
| Final Equity | 最终权益 |

可选计算：

- Volatility；
- Sharpe-like Score；
- Average Trade Return；
- Profit Factor。

---

## 11. 技术架构建议

### 11.1 推荐架构

MVP 可采用前后端一体或轻量全栈结构：

```text
Frontend
  - One-page cockpit UI
  - Chart rendering
  - Input controls
  - Result visualization

Backend / API
  - Load offline CSV
  - Calculate indicators
  - Call LLM or fallback rule engine
  - Run backtest
  - Return structured result

Core Engine
  - Data loader
  - Indicator calculator
  - Strategy modules
  - Backtest engine
  - Metrics calculator
```

### 11.2 推荐目录结构

```text
lesson10/
  data/
    BTC.csv
    ETH.csv
    SOL.csv
  docs/
    hyperliquid-intro.md
    ai-strategy-cockpit-prd.md
  src/
    app/
      page.tsx
      api/
        run-strategy/
          route.ts
    components/
      CockpitHeader.tsx
      StrategyInputPanel.tsx
      EquityChart.tsx
      MetricsCards.tsx
      AIAnalysisPanel.tsx
      StrategyCard.tsx
      TradeLog.tsx
    lib/
      dataLoader.ts
      indicators.ts
      llmStrategyAdvisor.ts
      fallbackAdvisor.ts
      backtestEngine.ts
      metrics.ts
      types.ts
    strategies/
      trendFollowing.ts
      meanReversion.ts
      breakout.ts
  tests/
    indicators.test.ts
    backtestEngine.test.ts
    strategies.test.ts
```

### 11.3 前端技术建议

- Next.js / React；
- Tailwind CSS；
- Recharts 或 ECharts；
- 单页驾驶舱布局；
- 深色主题更适合交易终端感。

### 11.4 后端技术建议

- Next.js API route 或轻量 Node API；
- CSV 解析；
- LLM 调用封装；
- 本地 fallback 规则；
- 所有结果以 JSON 返回。

---

## 12. API 设计

### 12.1 运行策略接口

`POST /api/run-strategy`

请求：

```json
{
  "symbol": "BTC",
  "riskProfile": "balanced",
  "goal": "capture_trend"
}
```

响应：

```json
{
  "symbol": "BTC",
  "riskProfile": "balanced",
  "goal": "capture_trend",
  "dataSource": "offline_csv",
  "aiAnalysis": {
    "marketRegime": "uptrend_medium_volatility",
    "summary": "市场处于中等波动的上升趋势。",
    "opportunity": "价格保持在慢速均线上方，趋势延续概率较高。",
    "risk": "近期波动率上升，需要控制仓位。",
    "selectedStrategy": "trend_following",
    "strategyReason": "用户目标是捕捉趋势，当前市场趋势信号较强。",
    "disclaimer": "仅用于教学和模拟，不构成投资建议。"
  },
  "strategy": {
    "id": "trend_following",
    "name": "Trend Following",
    "parameters": {
      "fastMA": 10,
      "slowMA": 30,
      "positionSize": 0.6,
      "stopLoss": 0.04
    }
  },
  "metrics": {
    "totalReturn": 0.184,
    "maxDrawdown": -0.062,
    "winRate": 0.583,
    "tradeCount": 24,
    "finalEquity": 11840
  },
  "chart": {
    "equityCurve": [
      { "timestamp": "2024-01-01", "equity": 10000 },
      { "timestamp": "2024-01-02", "equity": 10080 }
    ],
    "priceCurve": [
      { "timestamp": "2024-01-01", "close": 42800 },
      { "timestamp": "2024-01-02", "close": 43120 }
    ]
  },
  "trades": [
    {
      "timestamp": "2024-03-01",
      "action": "BUY",
      "price": 62400,
      "positionSize": 0.6,
      "reason": "Fast MA crossed above Slow MA"
    }
  ]
}
```

---

## 13. 状态与交互设计

### 13.1 页面状态

| 状态 | 页面表现 |
|---|---|
| Idle | 显示输入区和示例空态 |
| Loading | 显示分阶段 loading 文案 |
| Success | 显示完整驾驶舱结果 |
| LLM Fallback | 显示结果，并标记使用规则引擎兜底 |
| Data Fallback | 显示结果，并标记使用内置演示数据 |
| Error | 显示可理解错误和重试按钮 |

### 13.2 空态文案

```text
Choose a symbol, risk profile, and goal to launch your AI strategy cockpit.
```

### 13.3 Loading 文案

```text
Reading offline market data...
Calculating market indicators...
Asking AI to analyze the market...
Selecting strategy and parameters...
Running deterministic backtest...
Rendering cockpit results...
```

### 13.4 风险提示文案

页面底部固定展示：

```text
This demo is for educational and simulation purposes only. It does not execute real trades and does not constitute financial advice.
```

中文可选：

```text
本演示仅用于教学和模拟，不执行真实交易，不构成投资建议。
```

---

## 14. 视觉风格

### 14.1 设计关键词

- AI-native；
- Trading cockpit；
- Dark mode；
- Data-rich but readable；
- Hackathon polished；
- Futuristic but practical。

### 14.2 推荐配色

- 背景：深色 `#0B1020`；
- 卡片：`#111827` / `#172033`；
- 主色：蓝紫色 `#7C3AED`；
- 收益绿色：`#22C55E`；
- 风险红色：`#EF4444`；
- 辅助文字：`#94A3B8`；
- 分割线：`#1E293B`。

### 14.3 图表要求

- 权益曲线必须视觉突出；
- 买卖点使用小圆点或三角标记；
- 指标卡片使用大数字；
- AI 分析区使用分段标题，避免大段文字；
- 策略卡片要有明显 selected 状态。

---

## 15. 验收标准

### 15.1 P0 验收标准

1. 打开页面后可以看到完整一屏驾驶舱布局；
2. 用户可以选择币种、风险偏好和交易目标；
3. 点击运行后，系统能在无网络行情 API 的情况下完成演示；
4. 页面能展示 AI 市场分析；
5. 页面能展示被选中的策略和参数；
6. 页面能展示收益曲线；
7. 页面能展示总收益、最大回撤、胜率、交易次数；
8. 页面能展示模拟交易日志；
9. LLM 失败时仍能用规则引擎输出结果；
10. 数据文件缺失时仍能用 mock 数据输出结果；
11. 页面明确展示“非投资建议”免责声明；
12. 不存在真实下单、钱包连接或资金操作入口。

### 15.2 Demo 验收标准

1. 演示者可以在 1-2 分钟内讲完整条主线；
2. 一键运行不会因为行情 API 或网络失败中断；
3. AI 分析理由与图表结果能对应上；
4. 页面看起来像一个完整产品，而不是脚本输出；
5. 观众可以明确区分 AI 决策与确定性回测代码的边界。

---

## 16. 黑客松执行计划

### 16.1 1 天 MVP 版本

如果只有 1 天，实现范围：

1. 搭建单页驾驶舱 UI；
2. 准备 BTC 离线 CSV 或 mock 数据；
3. 实现指标计算；
4. 实现 1 个策略：趋势跟随；
5. 实现回测引擎；
6. 接入 LLM 或用 mock AI 分析；
7. 展示收益曲线、指标、AI 理由、交易日志；
8. 加上免责声明。

### 16.2 2 天增强版本

如果有 2 天，实现范围：

1. 支持 BTC / ETH / SOL；
2. 实现 3 个策略；
3. 接入真实 LLM 调用；
4. 实现 LLM JSON schema 校验；
5. 实现 fallback 规则引擎；
6. 增强图表交互；
7. 支持风险偏好影响参数；
8. 优化视觉和 Demo 脚本。

### 16.3 任务拆分建议

| 角色 | 任务 |
|---|---|
| 前端开发 | 驾驶舱页面、图表、卡片、交易日志 |
| 后端/核心开发 | 数据读取、指标、策略、回测、API |
| AI 开发 | LLM prompt、JSON schema、fallback 规则 |
| Demo/产品 | 文案、视觉打磨、演示脚本、风险提示 |

---

## 17. Demo 脚本

### 17.1 开场

> 今天我们展示的是 AI Strategy Cockpit，一个面向 Hyperliquid 量化策略教学场景的 AI 策略驾驶舱。它不会执行真实交易，而是用离线历史数据模拟一个完整的策略分析和回测流程。

### 17.2 操作步骤

1. 选择 BTC；
2. 选择风险偏好：Balanced；
3. 选择目标：Capture Trend；
4. 点击 Run AI Strategy；
5. 等待页面生成结果；
6. 讲解 AI 市场分析；
7. 讲解为什么选择该策略；
8. 讲解收益曲线和关键指标；
9. 讲解交易日志；
10. 强调这是教学模拟，不构成投资建议。

### 17.3 重点讲解词

> 这里的关键点是：LLM 不直接写交易代码，也不直接下单。它负责解释市场、选择策略和建议参数；真正的交易模拟由确定性回测引擎执行。这样既能展示 AI 的推理能力，又能保证系统可控、可复现。

### 17.4 收尾

> 这个 Demo 可以扩展到更多策略、更多资产、Hyperliquid 历史数据 API，甚至未来接入真实交易前的 paper trading 环境。但 MVP 阶段我们刻意保持离线和模拟，确保黑客松现场稳定。

---

## 18. 风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| LLM 输出不可解析 | Demo 中断 | 强制 JSON schema + fallback 规则 |
| 数据文件缺失 | 无法回测 | 内置 mock 数据生成器 |
| 图表效果不明显 | 视觉冲击弱 | 准备趋势明显的示例数据 |
| 策略不产生交易 | 页面空洞 | 参数兜底并自动放宽阈值 |
| 被误解为投资建议 | 合规风险 | 页面和口播都强调 simulation only |
| 实现时间不足 | 功能不完整 | 优先完成一键闭环和驾驶舱视觉 |

---

## 19. 后续扩展方向

MVP 之后可扩展：

1. 接入 Hyperliquid 历史行情 API；
2. 支持 paper trading；
3. 支持多策略对比；
4. 支持策略插件上传；
5. 支持自然语言生成策略配置；
6. 支持导出 AI 回测报告；
7. 支持更多风险指标；
8. 支持多资产组合回测；
9. 支持回测参数可视化调优；
10. 支持真实交易前的人工确认流程。

---

## 20. 最终定义

AI Strategy Cockpit 的 MVP 成功定义为：

> 在黑客松现场，演示者可以打开一个一屏驾驶舱，选择币种、风险偏好和交易目标，一键生成 AI 市场分析、策略选择、参数建议、模拟回测曲线、关键收益指标和交易日志。整个流程不依赖实时行情 API，不执行真实交易，并且在视觉上像一个完整可用的 AI 交易策略产品。
