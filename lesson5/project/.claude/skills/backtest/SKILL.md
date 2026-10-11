---
name: backtest
description: Use when the user asks to backtest a crypto trading strategy on historical OHLC data — translate the user's natural-language strategy into a Python callable matching `def strategy(df: DataFrame) -> Series` returning +1/0/-1 signals, then call backtest.run_backtest. Returns Sharpe / max drawdown / win rate / cumulative return + PNG curve + Chinese summary.
---

# backtest skill

调用 `project/backtest.py` 的 `run_backtest()`，用学员描述的策略回测一次 BTC/ETH 历史行情，返回结构化指标 + 一张曲线图 + 一段中文总结。

## 何时触发

用户说"评估 / 回测 / backtest 这个策略 ..."，或者描述了一个交易规则希望看到表现。

## 输入约定

用户给的策略描述（自然语言）。例子：
- "BTC 7 日均线穿越 14 日均线时买入，反向时卖出"
- "始终满仓做多"
- "RSI < 30 买入，RSI > 70 卖出"

可选参数（用户没说则用默认）：
- symbol（默认 `BTCUSDT`）
- interval（默认 `1d`）
- limit（K 线行数，默认 30）

## 步骤

1. **翻译策略**：把用户的自然语言描述写成一个 Python 函数：
   ```python
   def strategy(df: pd.DataFrame) -> pd.Series:
       # 在这里实现规则
       # df 列：open / high / low / close / volume
       # 返回 Series：索引同 df.index，值为 +1（做多）/ 0（空仓）/ -1（做空）
       ...
   ```
   命名规范：策略名贴近用户描述的 snake_case，例如 `ma7_cross_ma14`。

2. **校验**：策略函数实现后，先在脑里 dry-run 一次：信号边界对吗？lookahead bias 有吗？（你不能用今天的 close 决定今天的信号 —— 必须先 shift(1) 再用，但这是 backtest.run_backtest 内部已经处理的事，你写策略时直接基于 df 里的列即可。）

3. **调用 run_backtest**：在同一会话里跑：
   ```python
   from backtest import run_backtest
   result = run_backtest(your_strategy, symbol="BTCUSDT", interval="1d", limit=30)
   ```

4. **解读结果**：用 result["summary"] 给用户文字总结；如有需要补充 sharpe/max_drawdown/win_rate 中具体数字的解读；告诉用户 PNG 曲线在 `result["png_path"]` 可以查看。

5. **可选**：用户希望同时对比多个策略时，重复 1-4 各一次，最后写一段对比段。

## 反模式

- ❌ 不要替用户改策略（只翻译，不优化）
- ❌ 不要在 pandas Series 里夹杂 NaN 不 fillna —— `run_backtest` 会 reindex/fillna(0)，但提早处理更稳
- ❌ 不要用 `df["close"].iloc[-1]` 这种"今天就拿到收盘价"的写法 —— 用 rolling/shift 表达"基于历史"

## 示例

`example_strategies.py` 里有两个起手模板，必要时引用或复制。
