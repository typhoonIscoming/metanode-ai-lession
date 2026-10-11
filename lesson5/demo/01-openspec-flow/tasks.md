# Tasks: dual_ma

实现 + 验证拆解（实施时按序勾选）：

- [ ] 1. 在 `lesson5/project/strategies/__init__.py` 导出 `dual_ma`
- [ ] 2. 写 `lesson5/project/strategies/dual_ma.py`：
  - 函数签名 `dual_ma(df, short_window=7, long_window=14) -> pd.Series`
  - 按 `design.md` §3 骨架实现
  - 中文 docstring + 注释（CLAUDE.md 约定）
- [ ] 3. 跑自测：
  ```python
  from strategies.dual_ma import dual_ma
  from backtest import run_backtest
  print(run_backtest(dual_ma)["summary"])
  ```
  无 traceback 即通过
- [ ] 4. 把 `specs.md` 的接口段合并到 `lesson5/project/openspec/specs/strategies.md`，把"暂无策略"改成"已实现：dual_ma"
- [ ] 5. 在本目录加一份 `IMPLEMENTATION.md`，记录：实施日期、实际行数、自测结果、与 design.md 的偏差（若有）
- [ ] 6. 提交 commit："openspec: implement dual-ma strategy per add-dual-ma-strategy change"
