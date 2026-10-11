## Context

`project/` 当前所有产出都在 CLI：`python btc_kline.py` 打印 + PNG，`python strategies/dual_ma.py` 打印 summary。要向"非 Python 用户"或评委做演示，体验断层明显：

- 学员 / 评委不一定有 Python 环境
- 多策略对比要开多个终端跑、再翻 PNG，缺统一视图
- 没有一个"开机即看"的入口让人立刻感受到"项目能做什么"

约束：

- **不破坏既有 CLI 流程** —— `python btc_kline.py` / `python strategies/dual_ma.py` 必须依然能用
- **不重写既有引擎** —— 复用 `backtest.run_backtest`，避免出现两份指标 / 画图实现互相漂移
- **依赖足够少** —— 单一 Python 依赖 + 单一前端 CDN，方便课堂上现场 `pip install` 5 秒搞定
- **沿用项目两条硬规约** —— UTC 时间、中文注释

## Goals / Non-Goals

**Goals:**

- 浏览器打开 `http://localhost:5000` 即看到"策略 / 标的 / K 线数"三个下拉 + Run 按钮
- 点 Run 之后 < 2s 在同页拿到指标表 + 累计收益曲线 + 中文总结
- 复用 `backtest.run_backtest`、`strategies/*.py`，**零修改**
- 自包含在 `project/web/` 下，新增依赖只有 `flask`

**Non-Goals:**

- 多用户 / 账号 / 权限
- 持久化历史回测（每次跑完只展示最新一次；旧 PNG 留在文件系统但 UI 不索引）
- 实时行情推送（WebSocket / 长轮询）
- 移动端响应式精修（桌面浏览器看清楚即可）
- 部署到公网（仅本地 `flask run` / `python -m web.app`，无 nginx / gunicorn / Dockerfile）
- 国际化 / 多语言切换（界面文案中文，与 `summary` 同步）

## Decisions

### 1. 后端框架：Flask（而非 FastAPI / Streamlit / 静态 HTML）

| 方案 | 优势 | 劣势 |
|---|---|---|
| **A. Flask**（选用） | 学员认知度最高；最少抽象（一个 `app.py`、两个路由就跑起来）；模板与静态资源约定俗成 | 同步阻塞；但本场景单请求 < 200ms 不痛 |
| B. FastAPI | 异步、Pydantic、自动 OpenAPI 文档 | 课程没讲过 async，引入新概念；模板需自接 Jinja2 |
| C. Streamlit | 一行 import 就有 UI；图表内置 | 全局状态难解释；UI 不像"自己的网站"，更像 Streamlit 的；课堂演示反而显得"作弊" |
| D. 纯静态 HTML | 零依赖；可托管 GitHub Pages | 失去"交互跑回测"的核心价值 —— 与目标"提高展示度"相悖 |

> 选 Flask 是因为它在"教学成本 / 演示效果 / 代码量"三轴上的最优解。

### 2. 前端：Tailwind CDN + 原生 fetch（而非 React / Vue / 全手写 CSS）

| 方案 | 优势 | 劣势 |
|---|---|---|
| **A. Tailwind CDN + vanilla JS**（选用） | 零构建；一个 `<script src=…>`、`<script>fetch(…)`</script>` 搞定；样式现代 | 离线场景 CDN 不可用 |
| B. React + Vite | 现代化体验 | 学员要装 Node、跑 build；超出"web 单页"承诺 |
| C. 纯 HTML + 手写 CSS | 完全自包含 | 视觉效果土，违背"提升展示度"初衷 |

> 演示机器都假定能上网（项目本身就在打 Binance API），CDN 不构成新约束。

### 3. 路由结构：`GET /` 渲染模板 + `POST /api/backtest` 返回 JSON

```
GET  /                  → render index.html（含策略列表，由后端注入）
POST /api/backtest      → JSON body {strategy, symbol, limit}
                          → 返回 {sharpe, max_drawdown, win_rate, cumulative_return,
                                  png_url, summary, rows}
GET  /static/results/<file>  → Flask 默认静态路由直发 PNG
```

> 注意：`run_backtest` 返回的是文件系统绝对路径 `png_path`；后端需要把它转成 URL `png_url = "/static/results/<basename>"`，否则浏览器拿不到。

### 4. 策略注册：显式字典（而非反射扫包）

```python
# web/app.py 顶部
from strategies import dual_ma, rsi_reversal
from .strategies_extra import buy_and_hold  # 或直接定义在 app.py

STRATEGIES = {
    "dual_ma": dual_ma,
    "rsi_reversal": rsi_reversal,
    "buy_and_hold": buy_and_hold,
}
```

理由：

- 显式注册让"前端下拉里能选什么"和"后端能跑什么"严格一致，没有"加了策略但 UI 看不到"的歧义
- 比反射 `importlib.iter_modules` 类思路代码少 80%，可读性高
- 添加策略时只需一行；学员后续做 `add-bollinger-strategy` 等变更时知道改这里

### 5. PNG 输出目录：`web/static/results/<symbol>_<strategy>_<ts>.png`

| 决策 | 理由 |
|---|---|
| 不写到 `project/cum_<symbol>.png`（CLI 默认位置） | CLI 输出和 web 输出隔离；CLI 演示和 web 演示互不破坏 |
| 用 `static/results/` 子目录 | Flask 默认会从 `static/` 直发；不用单写一个 send_file 路由 |
| 文件名带 timestamp | 多次 run 不互相覆盖；用户可手翻历史；同时配合 .gitignore 不让产物入库 |
| `.gitkeep` 占空目录 | 让目录可入版本库，避免新 clone 后跑不起来 |

`backtest.run_backtest` 的签名已经接受 `out_dir: Path | None`；后端只需传 `out_dir=Path(__file__).parent / "static/results"` 即可，**无需改 backtest.py**。

> 文件名 collision 行为（spec.md 最后一条 scenario 要求 design 明确选择）：**timestamp 后缀，保留多次** —— 用户可对照不同跑次。

### 6. 同步执行（不开线程 / 任务队列）

- BTCUSDT 90 日 1d 数据 + dual_ma 在我的机器实测 < 200ms（含 PNG 写盘）
- 不需要 spinner / 进度条 —— 点完按钮立即 await `fetch().then()`
- 不需要 `asyncio` / Celery / RQ —— Flask 默认同步即可

风险：如果以后加 `limit=10000` 或多年回测，请求会阻塞 → 留给未来 change（不在此 scope）

### 7. 静态首屏：服务端渲染策略列表（而非前端拉一次 GET /api/strategies）

- 少一次往返；首屏可立即看到下拉
- 用 Jinja `{% for s in strategies %}<option>{{ s }}</option>{% endfor %}`
- 没必要为 3-5 个策略做异步加载抽象

### 8. 错误处理：捕获到顶层 → JSON `{error: "..."}` + HTTP 4xx

```python
@app.errorhandler(ValueError)
def on_value_error(e):
    return jsonify(error=str(e)), 400
```

引擎里现成的 `ValueError("prices.db 没有 XXX 的数据；先跑 python seed_db.py")` 会被原样回传到前端 —— 学员第一次跑的时候大概率忘了 seed，这条文案就是给他们看的。

### 9. 启动命令：`python -m web.app`（而非 `flask run`）

`python -m` 形式好处：

- 不需要设 `FLASK_APP` 环境变量
- 不依赖 `flask` 命令行进 PATH（某些 venv 配置下 `flask` 可能 not found）
- 与 `python btc_kline.py` 风格对齐

`web/app.py` 底部加 `if __name__ == "__main__": app.run(debug=True, port=5000)` 即可。

## Risks / Trade-offs

- **[CDN 依赖]** → 演示机器需联网才能加载 Tailwind；线下没网时 UI 退化为无样式 HTML 但功能仍能用 → **mitigation**：在 README 里点明；如果团队走线下演示再考虑把 tailwind.min.css 下载进 static/
- **[同步阻塞]** → 长 limit 会卡 UI → **mitigation**：在表单上限制 limit ≤ 365；说明文档解释为什么
- **[Flask debug 模式生产风险]** → `debug=True` 默认开，演示用够，但勿暴露公网 → **mitigation**：README 显著位置写"仅本地用，公网部署需关 debug"
- **[results/ 越攒越大]** → 每次回测新增一个 PNG → **mitigation**：.gitignore 屏蔽；README 提供一行 `rm web/static/results/*.png` 清理命令；不在代码里加自动清理（避免误删）
- **[strategy 注册表与文档漂移]** → 加了策略忘了同步 README → **mitigation**：注册表是显式字典，加 import + 一行 dict entry 自然成对，漂移成本低；不引入元数据扫包

## Migration Plan

不涉及上线 / 数据迁移；纯新增目录。回滚 = `rm -rf project/web/` + 撤掉 `.gitignore` 的那一行。

## Open Questions

- 是否要在 dashboard 里加"K 线图"页签（复用 btc_kline.py）？**默认不加** —— 本变更只做"策略回测"展示；K 线展示留给未来 `add-web-kline-view` 变更
- 是否要展示 buy_and_hold 的对照基线？**加** —— 注册表里已包含；学员可显式选它对比，无需自动叠加
- 是否要在前端按时间倒序展示历史回测？**不做** —— 见 Non-Goals 第 2 条；本期只展示最新一次
