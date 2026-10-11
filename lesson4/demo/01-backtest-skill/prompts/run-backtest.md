# Demo prompt: 用 backtest skill 跑两个策略对比

> **用法**：在 `lesson4/project/` 下启动 Claude Code 后，整段粘贴。

---

用 backtest skill 评估两个 BTC 策略：

1. buy_and_hold（始终满仓做多）
2. ma_crossover_7（close 高于 7 日均线时做多，否则空仓）

各 30 天日 K 线（symbol=BTCUSDT, interval=1d, limit=30），给我对比报告。

---

## 期望表现

Claude 调用 backtest skill 两次，每次：
1. 把策略名翻译成一个 Python callable（参考 `example_strategies.py`，可直接 import 复用）
2. 调 `run_backtest(strategy, symbol="BTCUSDT", interval="1d", limit=30)`
3. 把 result["summary"] 摘要给用户

最后输出一段中文对比，约 150-200 字，覆盖两个策略的 sharpe / cumulative_return / max_drawdown 差异。

**不应该**做的事：
- 自己重写 backtest 逻辑（应当复用 `backtest.run_backtest`）
- 跳过 PNG 路径不告诉用户
