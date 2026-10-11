# 策略规范（当前状态）

**位置**：`project/strategies/`

## 当前已实现的策略

| 名称 | 文件 | 简介 |
|---|---|---|
| `dual_ma` | `project/strategies/dual_ma.py` | 双均线交叉，short=7 / long=14，金叉做多，死叉空仓 |
| `rsi_reversal` | `project/strategies/rsi_reversal.py` | RSI 反转，period=14、超卖 30 进多、超买 70 离场（long-only） |

## 通用约定

任何加入 `strategies/` 的新策略**必须**满足：

1. 是一个 callable，签名 `def strategy(df: pd.DataFrame) -> pd.Series`
2. 返回值索引同 `df.index`，值在 {-1, 0, +1}（满仓做空 / 空仓 / 满仓做多）
3. 不允许 lookahead：信号只能基于 `df.index` 时刻或更早的数据
4. 必须能被 lesson 4 `backtest.run_backtest()` 直接调用
5. 默认 **long-only**（值域 `{0, +1}`）；若需要做空版本，**文件名加 `_long_short` 后缀**以示区分（例如 `rsi_reversal_long_short.py`）

> 这些约定不仅写在这里，也写进 `.cursor/rules/strategy-conventions.mdc` 让 Cursor / Claude 在改 `strategies/*.py` 时自动注入。
