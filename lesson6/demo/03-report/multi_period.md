# 多周期回测报告 — dual_ma 策略

> 6 个场景：BTCUSDT / ETHUSDT × limit ∈ {30, 60, 90}。回测引擎：`lesson6/project/backtest.py`。生成时间：UTC 2026-05-12.

## Executive Summary

双均线（dual_ma）策略在 BTC 与 ETH 的中等时间窗口（limit=60、90）上整体表现稳健：Sharpe 落在 1.16–2.64 区间、胜率 0.57–0.65、累计收益正且回撤可控（≤ 13%）。短窗口（limit=30）两个币种均全零，这是因为均线参数尚未走完 warmup 期、未产生任何有效信号，并非策略失效。BTC 在 limit=60 表现最好（Sharpe 2.64），ETH 则在 limit=90 收益最高（cum=0.20）。综合看，策略可在 ≥ 60 根 K 线的窗口上使用，短窗口不可用。

## 结果表

| symbol | limit | sharpe | max_dd | win_rate | cum_return |
|---|---|---|---|---|---|
| BTCUSDT | 30 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| BTCUSDT | 60 | 2.6388 | -0.0424 | 0.6538 | 0.1237 |
| BTCUSDT | 90 | 1.1563 | -0.0938 | 0.5870 | 0.0911 |
| ETHUSDT | 30 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| ETHUSDT | 60 | 1.5682 | -0.0644 | 0.5789 | 0.1008 |
| ETHUSDT | 90 | 1.6456 | -0.1271 | 0.5750 | 0.2019 |

> 注：limit=30 两行全零是因为双均线的长周期窗口尚未走完 warmup，整段区间未产生任何买卖信号，不是策略产生了零收益，而是没有任何交易。

## 定性分析（3 句）

1. **哪个 scenario 表现最好？** BTCUSDT × limit=60 的 Sharpe 最高（2.64）、最大回撤最浅（-4.2%）、胜率最高（65%），综合风险调整后收益是 6 个 scenario 里最好的。
2. **时间窗口越长越稳吗？** 不一定——limit 从 30 → 60 是从"无信号"跳到"高 Sharpe"，60 → 90 反而让 BTC 的 Sharpe 从 2.64 掉到 1.16、回撤翻倍，更长窗口引入了更多反向行情而非更稳的趋势。
3. **BTC vs ETH 哪个更适合 dual_ma？** BTC 在中窗口（60）Sharpe 显著高于 ETH（2.64 vs 1.57），但 ETH 在长窗口（90）累计收益翻倍领先（0.20 vs 0.09），两者各有侧重——追求 Sharpe 选 BTC + 60，追求绝对收益选 ETH + 90。

## Reproduce

```bash
cd lesson6/project/
python -c "from strategies import dual_ma; from backtest import run_backtest; r = run_backtest(dual_ma, symbol='BTCUSDT', limit=30); print(r)"
# 重复 6 次，limit ∈ {30, 60, 90}, symbol ∈ {BTCUSDT, ETHUSDT}
```
