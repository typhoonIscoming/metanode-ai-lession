# Implementation Note: add-dual-ma-strategy

## 实施日期

2026-05-05T08:38:56Z

## 实施产物

- `project/strategies/dual_ma.py`（约 50 行）
- `project/strategies/__init__.py`

## 自测结果（90 日 BTCUSDT 1d K 线）

```
sharpe=1.1563
max_drawdown=-0.0938
win_rate=0.5870
cumulative_return=0.0911
```

中文 summary：

> BTCUSDT 在最近 90 根 K 线上的回测结果：累计上涨 9.11%，年化夏普 1.16，最大回撤 -9.38%，信号触发日胜率 58.70%。夏普 > 1 说明风险调整后收益尚可，配合曲线图可看到回撤分布，建议结合更长历史数据复跑确认稳健性。

## 与 design.md 的偏差

无

## 后续

合并 specs.md 接口段到 `openspec/specs/strategies.md`（已完成）
