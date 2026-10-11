## 1. 目录骨架与依赖

- [x] 1.1 创建目录树：`project/web/`、`project/web/templates/`、`project/web/static/results/`
- [x] 1.2 在 `project/web/static/results/` 放一个 `.gitkeep`（空文件），让目录可入库
- [x] 1.3 写 `project/web/__init__.py`（带中文模块 docstring，说明 web 是策略 dashboard 的 Flask 入口）
- [x] 1.4 写 `project/web/requirements.txt`：仅一行 `flask>=3.0`
- [x] 1.5 编辑根 `.gitignore`，追加 `web/static/results/*` 和 `!web/static/results/.gitkeep`（让 PNG 被忽略但保留占位）

## 2. Flask 后端

- [x] 2.1 写 `project/web/app.py`：
  - Flask 实例 + 模板/static 默认目录
  - 顶部导入 `dual_ma`、`rsi_reversal`，再定义本地的 `buy_and_hold(df)` 函数（或独立小模块）
  - 显式字典 `STRATEGIES = {"dual_ma": dual_ma, "rsi_reversal": rsi_reversal, "buy_and_hold": buy_and_hold}`
  - 路由 `GET /` → `render_template("index.html", strategies=sorted(STRATEGIES.keys()))`
- [x] 2.2 路由 `POST /api/backtest`：
  - 解析 JSON body：`{strategy, symbol, limit}`
  - 校验 strategy ∈ STRATEGIES（不在则 400 + error JSON）
  - 调 `backtest.run_backtest(STRATEGIES[strategy], symbol=symbol, limit=int(limit), out_dir=Path(app.static_folder) / "results")`
  - 拿到 result dict 后构造 `png_url`：把绝对 `result["png_path"]` 转成 `/static/results/<basename>`
  - 返回 JSON：metrics + png_url + summary + rows
- [x] 2.3 全局错误处理：捕获 `ValueError`（引擎抛的"先跑 seed_db"等）→ 400 + `{error: str(e)}`
- [x] 2.4 路径处理细节：用 `pathlib.Path` 处理 `app.static_folder` 与 `out_dir`，保证跨平台
- [x] 2.5 文件名 collision：让 `out_dir` 接收一个**带 timestamp 的子路径**或在 `run_backtest` 调用后立即把生成的 `cum_<symbol>.png` 移动 / 重命名为 `<symbol>_<strategy>_<utc_ts>.png`（用 `datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")`）
- [x] 2.6 `if __name__ == "__main__":` 块：`app.run(host="127.0.0.1", port=5000, debug=True)`

## 3. 前端模板

- [x] 3.1 写 `project/web/templates/index.html`：
  - `<!DOCTYPE html>`、`<html lang="zh-CN">`、`<head>` 引 Tailwind CDN `<script src="https://cdn.tailwindcss.com">`
  - `<title>` 中文："量化策略 Dashboard" 或类似
  - 顶部 hero 区：项目名 + 一段中文介绍（≤ 2 行）
  - 表单（卡片样式）：
    - `<select>` 策略（从 Jinja 注入）
    - `<select>` symbol（BTCUSDT / ETHUSDT）
    - `<input type="number">` limit，默认 90，min=30, max=365
    - `<button>` "运行回测"
  - 结果区初始隐藏；按钮点击后用 fetch POST `/api/backtest`，成功显示：
    - 4 个指标卡片（sharpe / max_drawdown / win_rate / cumulative_return）
    - `<img>` 显示 png_url
    - `<p>` 显示 summary
  - 错误区：fetch 非 200 时显示红色 banner，文字取自 JSON.error
- [x] 3.2 视觉：用 Tailwind utility classes 做出 ≥ 中等审美 —— 卡片圆角、阴影、合理留白、配色不刺眼（建议中性灰 + 一个强调色，如 emerald/indigo）
- [x] 3.3 数字格式化：百分比类（max_drawdown / win_rate / cumulative_return）渲染为 `±X.XX%`，sharpe 渲染为 `0.00` 两位小数

## 4. 自测

- [x] 4.1 确认 `prices.db` 已 seed（否则先 `python seed_db.py`）
- [x] 4.2 在 `project/` 目录跑 `python -m web.app`，看终端 `Running on http://127.0.0.1:5000` 出现
- [x] 4.3 打开浏览器或用 `curl -X POST localhost:5000/api/backtest -H 'Content-Type: application/json' -d '{"strategy":"dual_ma","symbol":"BTCUSDT","limit":90}'` 验证返回的 JSON 包含 7 个字段（sharpe/max_drawdown/win_rate/cumulative_return/png_url/summary/rows），无 traceback
- [x] 4.4 浏览器手测三条路径：
  - `dual_ma + BTCUSDT + 90` → 看到曲线 + 正数 sharpe
  - `rsi_reversal + BTCUSDT + 90` → 看到全 0 的曲线（按 IMPLEMENTATION.md 预期）
  - `buy_and_hold + ETHUSDT + 60` → 看到基线对照
- [x] 4.5 错误路径：故意提交 `strategy=does_not_exist` → 看 UI 红色 banner 显示后端错误文案
- [x] 4.6 错误路径：临时把 `prices.db` 改名后跑 → 看 UI 显示"先跑 python seed_db.py"
- [x] 4.7 不破坏既有：`python btc_kline.py` 仍能跑、`python strategies/dual_ma.py` 仍能跑（`git diff --stat` 验证 strategies/ 与 backtest.py 0 byte 改动）

## 5. 文档

- [x] 5.1 写 `project/web/README.md`：
  - 一段话介绍这个 dashboard 做什么
  - **Prerequisites**：项目根已 `python seed_db.py` 一次
  - **Install**：`pip install -r web/requirements.txt`
  - **Run**：`cd project && python -m web.app`（或等价命令）
  - **Stop**：Ctrl+C
  - **Cleanup**：`rm web/static/results/*.png`（不会动 `.gitkeep`）
  - **Common errors** 表：3-4 行（端口占用 / 找不到 prices.db / strategy 名拼错 / Tailwind CDN 加载失败时的 fallback）
  - **如何加一个新策略**：3 步小清单（写策略 → 在 STRATEGIES 字典里加一行 → 重启）
- [x] 5.2 在 `project/README.md`（lesson5 根）追加一行"web dashboard：见 `web/README.md`"，让顶层导航能找到

## 6. 同步规范

- [x] 6.1 不修改 `openspec/specs/strategies.md`（本变更与策略目录无关）
- [x] 6.2 写 `openspec/changes/add-web-dashboard/IMPLEMENTATION.md`：实施日期（UTC ISO 8601）、实际行数、自测的截图占位 / 命令输出、与 design.md 的偏差（如无写"无"）
- [x] 6.3 IMPLEMENTATION.md 末尾追加一段：哪几个 spec 决策实施时被复用 / 微调，留给后人决策回溯

## 7. 验证与归档准备

- [x] 7.1 `openspec validate add-web-dashboard --strict` 通过
- [x] 7.2 整理本变更最终触及的文件清单（应只有：`web/**`、`.gitignore`、`README.md`、`openspec/changes/add-web-dashboard/**`），确保未误改其他文件
- [ ] 7.3 提交准备：`git status`、`git diff --stat`，把变更范围给用户确认
- [x] 7.4 commit 与 archive 留给用户授权后执行（用 `/opsx:archive add-web-dashboard` 走归档；`--skip-specs` 因为新 capability 的 spec layout 仍是 CLI 目录式） — 归档于 2026-05-13（UTC）；commit 仍留给用户授权
