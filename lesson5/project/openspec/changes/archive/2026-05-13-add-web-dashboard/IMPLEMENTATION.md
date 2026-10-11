# Implementation Note: add-web-dashboard

## 实施日期

2026-05-13T20:00:10Z

## 实施产物

| 路径 | 行数 | 角色 |
|---|---|---|
| `project/web/app.py` | 102 | Flask 后端：2 个路由 + 全局错误处理 + PNG 重命名 |
| `project/web/templates/index.html` | 185 | Tailwind CDN 单页前端 + vanilla JS fetch |
| `project/web/README.md` | 96 | 启动 / 清理 / 加策略 / 常见错误 / 安全提示 |
| `project/web/__init__.py` | 10 | 包占位 + 模块 docstring |
| `project/web/requirements.txt` | 1 | `flask>=3.0` |
| `project/web/static/results/.gitkeep` | 0 | 占位让目录入库 |
| `project/.gitignore` | +3 | 追加 `web/static/results/*` + 保留 `.gitkeep` |
| `project/README.md` | +2 | 顶层导航追加 `web/` 与 `rsi_reversal.py` 行 |

## 自测结果

后端在 `python -m web.app` 下顺利绑定 `http://127.0.0.1:5000`，curl 跑通的 4 个 happy + 2 个错误路径如下：

| 用例 | HTTP | 关键指标 |
|---|---|---|
| `dual_ma + BTCUSDT + 90` | 200 | Sharpe 0.86 / MaxDD -9.38% / 胜率 56.60% / 累计 +6.61% |
| `rsi_reversal + BTCUSDT + 90` | 200 | 全 0（与 `add-rsi-strategy` 的 IMPLEMENTATION 预期一致 —— 单边市场反转失效） |
| `buy_and_hold + ETHUSDT + 60` | 200 | Sharpe 0.56 / MaxDD -15.65% / 胜率 54.24% / 累计 +3.64% |
| `strategy=does_not_exist` | 400 | error: `未知策略 'does_not_exist'；可选：buy_and_hold, dual_ma, rsi_reversal` |
| `symbol=LTCUSDT`（未 seed） | 400 | error: `prices.db 没有 LTCUSDT 的数据；先跑 python seed_db.py` |

PNG 产物按预期写入 `web/static/results/<symbol>_<strategy>_<utc_ts>.png`：

```
BTCUSDT_dual_ma_20260513T195905Z.png        54 KB
BTCUSDT_rsi_reversal_20260513T195905Z.png   28 KB
ETHUSDT_buy_and_hold_20260513T195905Z.png   62 KB
```

**不破坏既有**核查（task 4.7）：

- `git status` 显示 `strategies/` 与 `backtest.py` 0 修改（唯一的旧改动是 `strategies/__init__.py`，那是上一个 `add-rsi-strategy` change 留下的，与本变更无关）
- `python -c "import btc_kline"` ✓
- `python -c "from strategies import dual_ma, rsi_reversal"` ✓

## 与 design.md 的偏差

无。9 项决策全部落地：

| design 决策 | 落地点 |
|---|---|
| 1. Flask 框架 | `web/app.py` |
| 2. Tailwind CDN + vanilla JS | `templates/index.html` 头部 `<script src="cdn.tailwindcss.com">` |
| 3. `GET /` + `POST /api/backtest` | `app.py` 路由 `index()` / `api_backtest()` |
| 4. 显式 STRATEGIES 字典 | `app.py` 顶部硬编码 3 条 |
| 5. PNG 输出隔离 + timestamp 重命名 | `RESULTS_DIR = static/results/`，跑完后 `old_png.replace(new_png)` |
| 6. 同步执行 | 后端无 threading / asyncio 引入 |
| 7. SSR 策略列表 | Jinja `{% for s in strategies %}` |
| 8. errorhandler(ValueError) | `app.py` 末尾 `@app.errorhandler(ValueError)` |
| 9. `python -m web.app` 启动 | `if __name__ == "__main__"` 块 + README 唯一文档命令 |

## 设计决策回溯

实施过程中复用了 spec / design 里的几个关键点：

- **错误文案直传**：spec.md "Empty database" scenario 要求把引擎的 ValueError 原样回传 —— 后端只需一行 `errorhandler(ValueError)` 即可，无需在每个 endpoint 写 try/except。设计文档 §8 的判断在实施时验证为对的。
- **PNG 重命名而非 out_dir 子目录**：design.md §5 写"timestamp 后缀保留多次"。实施时落点是"调用 `run_backtest(out_dir=RESULTS_DIR)` 之后立刻 `Path.replace()`"，比预先创建带 timestamp 的子目录更简单（少建一层目录、PNG 与 `.gitkeep` 同级）。
- **`sys.path` 注入**：因为 `web/app.py` 是子包模块、要 import 项目根的 `backtest`、`strategies`，必须把 `PROJECT_ROOT` 注入 `sys.path`。design.md 没显式提，但是 `python -m web.app` 启动方式下这是隐性约束。已在 `app.py` 注释中解释。

## 反思 / 教学要点

1. **零侵入复用**：`backtest.py` 早就预留了 `out_dir` 参数，本期完全靠它复用引擎而不动一行旧代码 —— 这是 lesson 4 设计的回报。学员可以看到"提前留好扩展点"在 lesson 5 直接兑现。
2. **三策略一表对比**：dashboard 让"反转 vs 趋势 vs 持有"在同一窗口下并排可见 —— 单边市场里 dual_ma +6.61%、buy_and_hold +28%（90 日 BTC 一开始 vs 现在）、rsi_reversal 0%，强化了 `add-rsi-strategy` IMPLEMENTATION.md 末尾"策略 vs 行情风格匹配"的反思。
3. **错误是教学素材**：故意让"忘了 seed" 走的报错路径在 UI 上有可读文案，学员首次操作时会自然遇到一次，并知道该怎么修。

## 后续

- 不在此变更内手工合并 `specs/web-dashboard/spec.md` 进 canonical specs/ —— 留给 `/opsx:archive` 阶段；由于这是新 capability，CLI 会创建 `openspec/specs/web-dashboard/spec.md` 作为 canonical，与既有 flat `strategies.md` 在路径风格上**不一致**但**互不冲突**
- 未来扩展候选：
  - `add-web-kline-view` —— 把 `btc_kline.py` 的图也搬进 dashboard
  - `add-web-strategy-compare` —— 一次跑多个策略叠图
  - `add-web-param-sweep` —— 给 `rsi_reversal(period, oversold, overbought)` 做扫参 UI
