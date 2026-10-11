"""
Flask dashboard 后端。

两个路由：
- GET  /              -> 渲染单页 dashboard（首屏注入策略列表）
- POST /api/backtest  -> 接收 {strategy, symbol, limit}，调用 backtest.run_backtest，返回指标 JSON

设计要点（详见 openspec/changes/.../add-web-dashboard/design.md）：
- 显式策略字典 STRATEGIES，UI 选项与后端可调用集严格一致
- run_backtest(out_dir=...) 把 PNG 写到 web/static/results/，与项目根的 CLI 输出隔离
- 跑完后立刻把 cum_<symbol>.png 重命名为 <symbol>_<strategy>_<utc_ts>.png 防 collision
- 全局 errorhandler 把引擎的 ValueError（"先跑 seed_db.py" 等）转为 400 JSON，前端就能直接弹给用户
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request

# 让 web 包能 import 同级的 backtest / strategies —— 用 project/ 作为路径根
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backtest import run_backtest  # noqa: E402  导入顺序故意：先调 sys.path
from strategies import dual_ma, rsi_reversal  # noqa: E402


def buy_and_hold(df: pd.DataFrame) -> pd.Series:
    """基线策略：始终满仓做多；用作 dashboard 上其他策略的对照。"""
    return pd.Series(1, index=df.index)


# 显式注册表：加策略 = 加一行 import + 加一行字典条目
STRATEGIES = {
    "dual_ma": dual_ma,
    "rsi_reversal": rsi_reversal,
    "buy_and_hold": buy_and_hold,
}

# Flask 默认会到 templates/ 找模板、static/ 发静态文件
app = Flask(__name__)
RESULTS_DIR = Path(app.static_folder) / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
def index():
    """渲染首页；策略列表在 SSR 时注入，避免再多一次往返。"""
    return render_template("index.html", strategies=sorted(STRATEGIES.keys()))


@app.post("/api/backtest")
def api_backtest():
    """跑一次回测，返回结构化结果。"""
    payload = request.get_json(silent=True) or {}
    strategy_name = (payload.get("strategy") or "").strip()
    symbol = (payload.get("symbol") or "BTCUSDT").strip()
    # limit 来源可能是字符串，做一次健壮转换
    try:
        limit = int(payload.get("limit", 90))
    except (TypeError, ValueError):
        return jsonify(error="limit 必须是整数"), 400

    if strategy_name not in STRATEGIES:
        available = ", ".join(sorted(STRATEGIES.keys()))
        return jsonify(error=f"未知策略 '{strategy_name}'；可选：{available}"), 400
    if limit < 1:
        return jsonify(error="limit 必须 ≥ 1"), 400

    strategy_fn = STRATEGIES[strategy_name]
    # out_dir 指到 static/results，让 PNG 走 Flask 默认静态路由
    result = run_backtest(strategy_fn, symbol=symbol, limit=limit, out_dir=RESULTS_DIR)

    # backtest 默认把 PNG 写成 cum_<symbol>.png；重命名为带 strategy + UTC 时间戳的形式
    # —— 多次回测互不覆盖，文件名一眼能读出"这是哪个策略哪一次跑的"
    old_png = Path(result["png_path"])
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    new_name = f"{symbol}_{strategy_name}_{ts}.png"
    new_png = RESULTS_DIR / new_name
    if old_png.exists():
        old_png.replace(new_png)
    result["png_path"] = str(new_png)
    result["png_url"] = f"/static/results/{new_name}"
    result["strategy"] = strategy_name
    result["symbol"] = symbol
    return jsonify(result)


@app.errorhandler(ValueError)
def on_value_error(exc: ValueError):
    """引擎里抛的 ValueError（典型："先跑 python seed_db.py"）→ 400 + JSON。"""
    return jsonify(error=str(exc)), 400


if __name__ == "__main__":
    # 仅本地用；debug 模式方便课堂演示热重载，部署到外网前请关掉
    app.run(host="127.0.0.1", port=5000, debug=True)
