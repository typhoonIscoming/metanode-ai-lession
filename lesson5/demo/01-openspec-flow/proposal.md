# Proposal: 双均线策略

## 问题

- lesson 4 backtest skill 已就绪，但 `lesson5/project/strategies/` 里只有 lesson 4 提供的两个 example（buy_and_hold / ma_crossover_7）
- buy_and_hold 是基线，没有交易决策；ma_crossover_7 是单条均线突破，没有"反转信号"
- 需要至少一个能在不同行情阶段都触发买卖（双向）的策略，作为 lesson 5-7 的研究对象

## 提案

实现一个**双均线交叉**策略 `dual_ma`：

- 短均线（默认 7 日）和长均线（默认 14 日）
- 短均线**上穿**长均线时给信号 `+1`（做多）
- 短均线**下穿**长均线时给信号 `0`（空仓 —— 不做空，简化教学）
- 其他情况维持上一日信号

## 影响范围

- 新增：`lesson5/project/strategies/dual_ma.py`
- 修改：`lesson5/project/openspec/specs/strategies.md`（变更完成后追加"已实现：dual_ma"）
- 不影响：lesson 4 的 backtest skill（直接消费即可）

## 验收

- 调用 `run_backtest(dual_ma)` 不报错
- 返回 dict 含 sharpe / max_drawdown / win_rate / cumulative_return / png_path / summary
- summary 文字总结里包含"dual_ma"或同义词
