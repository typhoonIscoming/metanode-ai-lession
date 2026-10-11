## 1. 编写策略

- [x] 1.1 在 `project/strategies/rsi_reversal.py` 中创建模块，写入中文模块 docstring（说明：RSI 反转、long-only、参数默认值、防 lookahead）
- [x] 1.2 实现 `_rsi(close: pd.Series, period: int) -> pd.Series`：用 `close.shift(1).diff()` 算 delta，`.clip(lower=0)` / `(-delta).clip(lower=0)` 拆 gain/loss，再用 `ewm(alpha=1/period, adjust=False).mean()` 算平均；对 `avg_loss == 0` 用 `replace(0, np.nan)` 防除零
- [x] 1.3 实现 `rsi_reversal(df, period=14, oversold=30, overbought=70) -> pd.Series`：
  - 数据不足（`len(df) < period + 1`）→ 返回全 0 Series
  - 计算 RSI 和它的 `shift(1)`（前一根）
  - `cross_up = (rsi > oversold) & (rsi.shift(1) <= oversold)`
  - `cross_dn = (rsi < overbought) & (rsi.shift(1) >= overbought)`
  - 用 `pd.Series(np.nan).where(...).ffill().fillna(0).astype(int)` 维持仓位
- [x] 1.4 给关键步骤加中文行内注释（不写"显而易见的什么"，只写"为什么这一步要这么做"）

## 2. 暴露在包顶层

- [x] 2.1 编辑 `project/strategies/__init__.py`，新增 `from .rsi_reversal import rsi_reversal`
- [x] 2.2 把 `rsi_reversal` 追加进 `__all__`

## 3. 自测

- [x] 3.1 在 `project` 目录执行 `python -c "from strategies import rsi_reversal; from backtest import run_backtest; r = run_backtest(rsi_reversal); print(r['summary'])"`，确认无 traceback
- [x] 3.2 用 `python strategies/rsi_reversal.py` 自测块（仿照 `dual_ma.py` 末尾的 `if __name__ == "__main__":` 模式）打印 `result["summary"]`
- [x] 3.3 手工抽查：打开生成的 `cum_BTCUSDT.png`，确认曲线在 RSI 进多 / 离场切换点处有可观察到的台阶
- [x] 3.4 边界用例：构造一个 `len(df) == 5`、`period == 14` 的 DataFrame，确认返回全 0、无异常
- [x] 3.5 输出值域检查：断言 `set(sig.unique()).issubset({0, 1})`

## 4. 同步规范文件

- [x] 4.1 在 `project/openspec/specs/strategies.md` 的"已实现的策略"表追加一行：`rsi_reversal` / `project/strategies/rsi_reversal.py` / RSI 反转，period=14、超卖 30 进多、超买 70 离场
- [x] 4.2 在该文件"通用约定"段落下追加一条说明（如果之前没有）：策略默认 long-only；如新增做空版本，请在文件名加 `_long_short` 后缀以示区分

## 5. 实施记录

- [x] 5.1 在本变更目录下新建 `IMPLEMENTATION.md`，按 `add-dual-ma-strategy/IMPLEMENTATION.md` 的栏目记录：实施日期（UTC ISO 8601）、实际行数、自测的四个指标（sharpe / max_drawdown / win_rate / cumulative_return）、与 design.md 的偏差（如无写"无"）
- [x] 5.2 在 IMPLEMENTATION.md 末尾追加一段"反思"：如果 RSI 反转在 90 日样本里 Sharpe < 0，明确说"教学样本里反转策略可能跑不过 buy_and_hold，这是预期的：单边行情就是反转策略的失效模式"

## 6. 提交与归档

- [ ] 6.1 `git add` 仅本变更涉及的文件（`strategies/rsi_reversal.py`、`strategies/__init__.py`、`openspec/specs/strategies.md`、`openspec/changes/add-rsi-strategy/`），**避免** `git add -A` 把 `prices.db` / `*.png` / `__pycache__` 误带进去（已在 `.gitignore`，但仍需肉眼确认）
- [ ] 6.2 提交信息：`openspec: implement rsi-reversal strategy per add-rsi-strategy change`
- [x] 6.3 运行 `openspec validate add-rsi-strategy --strict` 确认变更结构合法
- [x] 6.4 准备就绪后由 `/opsx:archive` 把 `specs/strategies/spec.md` 增量合并进 `openspec/specs/strategies.md`（**不在此变更内手工合并**，留给 archive 阶段以保持流程清晰） — 归档于 2026-05-13（UTC），用 `--skip-specs` 跳过 CLI 自动合并：canonical 是 flat `openspec/specs/strategies.md`、CLI 期望目录式 `openspec/specs/strategies/spec.md`，layout 不一致；4.1/4.2 已手工同步表与约定条目
