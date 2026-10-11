"""
project/web/

量化策略可视化 dashboard 的 Flask 入口。

打开 http://localhost:5000 即可选策略 / 标的 / K 线根数 → 触发后端
backtest.run_backtest → 浏览器看到指标、累计收益曲线、中文总结。

启动：在 project/ 目录下执行 `python -m web.app`
"""
