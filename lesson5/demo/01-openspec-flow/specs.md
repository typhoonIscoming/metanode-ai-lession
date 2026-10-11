# Spec: dual_ma 策略

## 接口

### `dual_ma.dual_ma(df, short_window=7, long_window=14)`

**输入**：
- `df: pd.DataFrame`：来自 `backtest.load_ohlc()`，索引 UTC 时间戳，列含 `close`（其他列可能存在但不强制使用）
- `short_window: int`：短均线窗口（默认 7）
- `long_window: int`：长均线窗口（默认 14）

**输出**：
- `pd.Series`：索引同 `df.index`，值 ∈ {0, +1}（本策略不做空）

## 行为细则

### 信号规则

设 `ma_s = df["close"].rolling(short_window).mean()`、`ma_l = df["close"].rolling(long_window).mean()`。

| 状态 | 当日信号 |
|---|---|
| `ma_s > ma_l` 且 昨日 `ma_s ≤ ma_l`（金叉） | `+1` |
| `ma_s < ma_l` 且 昨日 `ma_s ≥ ma_l`（死叉） | `0` |
| 其他（持仓维持） | 与昨日信号相同 |

### 边界

- `df` 行数 < `long_window` 时返回全 `0`
- 起始期（任一 MA 为 NaN）信号为 `0`

### lookahead 防护

`ma_s` 和 `ma_l` 用 `df["close"].shift(1).rolling(...)` 计算，确保信号决定时不读今日 close。

## 不支持

- 做空（短均线下穿不返回 -1，仅返回 0）
- 仓位分级（始终全仓 / 空仓二态）
- 自定义价格列（仅用 close）

## 兼容性

可被 `backtest.run_backtest(dual_ma)` 直接调用（仅依赖 `df["close"]`）。
