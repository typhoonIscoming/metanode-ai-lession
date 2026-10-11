## Why

当前量化项目所有产出都在 CLI（脚本打印 + 散落的 PNG），缺一个"打开就能演示"的可视化入口。要向同事 / 评委 / 学员展示"我有什么策略、它们跑出来什么样"，目前只能 `python -c "..."` 或翻 PNG 文件 —— 演示成本高、观众认知负担重。一个本地单页 web dashboard 能把"挑策略 → 跑回测 → 看曲线和指标"压缩成 3 次点击，**显著提升项目的展示度与可演示性**。

## What Changes

- 新增 `project/web/` 目录，放置一个**自包含的 Flask 单页应用**：
  - `web/app.py` — Flask 后端，注册 `dual_ma` / `rsi_reversal` / `buy_and_hold` 三个策略
  - `web/templates/index.html` — 单页前端（表单 + 结果区，Tailwind CDN）
  - `web/static/results/` — 回测产物（PNG）输出目录（gitignored）
  - `web/__init__.py` — 让 web 成为可导入包
  - `web/README.md` — 启动说明 + 截图（如有）
- 新增唯一第三方依赖：**flask**（最小版本约束，写进 `web/requirements.txt`）
- **不修改**任何现有文件：`backtest.py`、`strategies/`、`btc_kline.py`、`seed_db.py`、`openspec/` 既有规范均保持原样
- 在 `.gitignore` 追加 `web/static/results/`（PNG 产物不进版本库）

## Capabilities

### New Capabilities

- `web-dashboard`: 本地 web 单页应用；允许用户在浏览器里选策略 + 标的 + K 线根数，触发后端跑 `backtest.run_backtest`，回显指标 / 曲线 / 中文总结

### Modified Capabilities

<!-- 无 -->

## Impact

- **新增文件**:
  - `project/web/app.py`、`project/web/__init__.py`、`project/web/templates/index.html`、`project/web/requirements.txt`、`project/web/README.md`
  - `project/web/static/results/.gitkeep`（让空目录可入库）
- **修改文件**:
  - `project/.gitignore`（追加 `web/static/results/*` 排除规则，保留 `.gitkeep`）
- **不影响**: `backtest.py`、`strategies/`（任意一个）、`btc_kline.py`、`seed_db.py`、`prices.db` schema、既有 OpenSpec specs
- **新增运行依赖**: `flask>=3.0`（写进 `web/requirements.txt`，**与主项目隔离** —— 不污染顶层 install 清单）
- **新增外部依赖**: Tailwind CSS CDN（`cdn.tailwindcss.com`，**仅前端**，演示时机器需联网）
- **教学影响**: lesson 6-7 可以用这个 dashboard 直接演示策略对比；面试 / 路演场景下"打开 localhost:5000"比"运行 python 命令"更具说服力
