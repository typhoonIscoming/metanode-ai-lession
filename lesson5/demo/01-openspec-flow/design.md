# Design: dual_ma 策略

## 备选方案对比

| 方案 | 实现复杂度 | 教学清晰度 | 选择 |
|---|---|---|---|
| A. close vs MA（简单突破） | 低 | 高，但和 lesson 4 ma_crossover_7 雷同 | ❌ |
| B. 短 MA vs 长 MA（金叉死叉，本提案） | 中 | 高，经典量化教科书例 | ✅ |
| C. MACD（DIF/DEA） | 高 | 高，但额外引入 EMA 概念，超出 25 min | ❌ |

## 关键技术决策

### 1. 用 `shift(1)` 防 lookahead

每条均线在计算后再 `.shift(1)`，让"今日的 ma_s" 实际是"截至昨日的 7 日均值"。这是策略层防护；`backtest.run_backtest` 内部还会再 shift 一次（信号→下日收益），共两层。

### 2. 不做空

教学定位是"看清趋势跟踪与持仓管理"，加做空会让回撤指标和胜率解读变复杂。`return 0` 即空仓。

### 3. 状态保持

金叉之后到死叉之前**所有日子**都返回 `+1`，而不是只在金叉那一天给信号。这样 `signal.shift(1) * daily_return` 计算累计收益时，持有期间每天都参与。

```python
# 关键骨架
cross_up = (ma_s > ma_l) & (ma_s_prev <= ma_l_prev)
cross_dn = (ma_s < ma_l) & (ma_s_prev >= ma_l_prev)
sig = pd.Series(np.nan, index=df.index)
sig[cross_up] = 1
sig[cross_dn] = 0
sig = sig.ffill().fillna(0)  # 持仓维持 + 起始期空仓
```

### 4. 参数默认值

`short_window=7, long_window=14` —— 对 30 日 K 线足够触发 1-2 次交叉，可见效果；学员后续可以扫参。

## 不在范围

- 仓位金字塔加仓 / 减仓
- 止损止盈
- 多币种联动
