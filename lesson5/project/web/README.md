# project/web/ — 量化策略可视化 Dashboard

一个本地 Flask 单页应用，把"挑策略 → 跑回测 → 看曲线和指标"压缩成 3 次点击。复用 `project/backtest.py` 的 `run_backtest()` 引擎和 `project/strategies/` 下的所有策略，零改动主项目。

## 它做什么

- 浏览器打开 `http://localhost:5000`
- 下拉选策略（当前可选：`dual_ma` / `rsi_reversal` / `buy_and_hold`）
- 下拉选标的（`BTCUSDT` / `ETHUSDT`）
- 输入 K 线根数（默认 90，范围 30 ~ 365）
- 点 **运行回测** → 同页拿到 Sharpe / 最大回撤 / 胜率 / 累计收益 + 累计收益曲线 + 中文总结

## 先决条件

1. `project/prices.db` 已 seed 过（首次跑 `python seed_db.py`，会写入 90 行 BTCUSDT + 90 行 ETHUSDT）
2. Python 3.10+（与主项目一致）

## 安装

在 `project/` 目录下：

```bash
pip install -r web/requirements.txt
```

只装一个依赖：`flask>=3.0`。pandas / matplotlib / numpy 等主项目已在用，不重装。

## 启动

在 `project/` 目录下：

```bash
python -m web.app
```

终端将打印：

```
 * Running on http://127.0.0.1:5000
 * Restarting with stat
```

浏览器打开 `http://localhost:5000` 即可。**Ctrl+C** 停服。

## 清理回测产物

每次回测都会在 `web/static/results/` 留下一张带 UTC 时间戳的 PNG（`<symbol>_<strategy>_<ts>.png`）。不会自动清理，方便对照历史；想清空时：

```bash
rm web/static/results/*.png
```

`.gitkeep` 不会被删（通配符不匹配点开头的文件）。`.gitignore` 已经把这些 PNG 排除在版本库外。

## 加一个新策略到 dashboard

3 步：

1. 在 `project/strategies/` 写新策略文件（符合 `backtest.run_backtest` 的 callable 契约）
2. 在 `web/app.py` 顶部加一行 `from strategies import <name>`，再把 `<name>` 加进 `STRATEGIES` 字典
3. **重启** `python -m web.app`（debug 模式下保存即热重载，但**新增 import** 仍建议重启确保模块状态一致）

## 常见报错

| 现象 | 原因 | 解决 |
|---|---|---|
| 启动时报 `Address already in use` | 5000 端口被占 | `lsof -ti:5000 \| xargs kill -9` 或换端口（改 `app.py` 末尾的 `port=` 参数） |
| UI 报错"先跑 python seed_db.py" | `prices.db` 没数据 / 没文件 | 在 `project/` 跑一次 `python seed_db.py` |
| UI 报错"未知策略 'xxx'" | 前端的下拉值与后端 `STRATEGIES` 不一致 | 检查 `app.py` 顶部 import 是否漏写 |
| 页面排版全乱 / 像纯文本 | Tailwind CDN 没加载（离线环境） | 临时方案：把 `tailwind.min.css` 下载到 `web/static/` 后改 `index.html` 引用 |
| `rsi_reversal` 跑出来全 0 | BTC/ETH 当前 90 日是单边偏强，RSI 没触及 30 | **预期行为**，不是 bug —— 详见 `openspec/changes/archive/2026-05-13-add-rsi-strategy/IMPLEMENTATION.md` 的"反思"段 |

## 安全提示

`app.py` 末尾用了 `debug=True`，方便本地热重载。**勿将该端口暴露公网** —— debug 模式开启时存在远程代码执行风险。要部署到公网，至少需要：

1. 关闭 `debug`，改成 `app.run(debug=False, host="0.0.0.0", port=...)`
2. 改用 production WSGI 服务器（gunicorn / waitress）
3. 反代 + HTTPS 自己接

本期不在范围内。

## 目录结构

```
web/
├── __init__.py
├── app.py                  # Flask 后端：2 个路由 + 错误处理
├── requirements.txt        # flask>=3.0
├── README.md               # 本文件
├── templates/
│   └── index.html          # 单页前端：Tailwind CDN + vanilla JS
└── static/
    └── results/
        └── .gitkeep        # 占位；PNG 产物落到这里（gitignored）
```
