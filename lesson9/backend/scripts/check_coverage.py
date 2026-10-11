"""分级覆盖率门禁脚本。

由 `make test-cov-strict` 调用。读取 `coverage.json`（由 `pytest --cov-report=json` 写出），
按 docs/test-strategy.md §3.1 的三级阈值断言：

- 关键模块（资金安全相关）≥ 95%
- 其他业务模块 ≥ 85%
- 整体阈值由 pytest 自带的 `--cov-fail-under=80` 兜底，本脚本不重复检查

无 stdlib 外依赖，可在 venv 之外直接 `python scripts/check_coverage.py` 跑。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 与 docs/test-strategy.md §3.1 表格保持完全一致；改动需同步文档
CRITICAL_THRESHOLD = 95.0
BUSINESS_THRESHOLD = 85.0

CRITICAL_FILES = {
    "src/btc_arb/services/signal_engine.py",
    "src/btc_arb/services/quant_model.py",
    "src/btc_arb/services/notification.py",
}

# 这些子目录里的所有 .py（除已列入 critical 与 __init__）按业务阈值卡
BUSINESS_DIRS = {
    "src/btc_arb/services",
    "src/btc_arb/adapters",
}

# 这些文件即便落在 BUSINESS_DIRS 里也豁免（与 [tool.coverage.run].omit 对齐）
EXCLUDE_FILES = {
    "src/btc_arb/services/__init__.py",
    "src/btc_arb/adapters/__init__.py",
}


def classify(path: str) -> str | None:
    """返回 'critical' | 'business' | None。None 表示不在分级门禁范围。"""
    norm = path.replace("\\", "/")
    if norm in EXCLUDE_FILES:
        return None
    if norm in CRITICAL_FILES:
        return "critical"
    if any(norm.startswith(d + "/") for d in BUSINESS_DIRS):
        return "business"
    return None


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    cov_path = repo_root / "coverage.json"
    if not cov_path.exists():
        print(
            f"ERROR: {cov_path} 不存在；先跑 `pytest --cov=src/btc_arb --cov-report=json`",
            file=sys.stderr,
        )
        return 2

    with cov_path.open(encoding="utf-8") as f:
        data = json.load(f)

    files = data.get("files", {})
    if not files:
        print("ERROR: coverage.json.files 为空", file=sys.stderr)
        return 2

    failures: list[tuple[str, str, float, float]] = []
    missing_critical: list[str] = []
    checked: list[tuple[str, str, float]] = []

    # 关键文件没在覆盖率报告里 = 没被测过 = 失败
    seen_files = {p.replace("\\", "/") for p in files.keys()}
    for cf in CRITICAL_FILES:
        if cf not in seen_files and not _any_implementation_missing(cf, repo_root):
            missing_critical.append(cf)

    for path, info in files.items():
        cls = classify(path)
        if cls is None:
            continue
        pct = float(info.get("summary", {}).get("percent_covered", 0.0))
        threshold = CRITICAL_THRESHOLD if cls == "critical" else BUSINESS_THRESHOLD
        checked.append((path, cls, pct))
        if pct + 1e-9 < threshold:
            failures.append((path, cls, pct, threshold))

    _print_report(checked, failures, missing_critical)

    if failures or missing_critical:
        return 1
    return 0


def _any_implementation_missing(cf: str, repo_root: Path) -> bool:
    """如果某个 critical 文件目前还没被 backend 实装（B-12 / B-09 / B-15 之前），
    coverage 不会扫到 → 视为「尚未到检查时机」，不视为失败。

    只要文件存在就必须满足阈值；不存在则跳过（含提示）。
    """
    return not (repo_root / cf).exists()


def _print_report(
    checked: list[tuple[str, str, float]],
    failures: list[tuple[str, str, float, float]],
    missing_critical: list[str],
) -> None:
    print()
    print("=" * 76)
    print("  分级覆盖率门禁（docs/test-strategy.md §3.1）")
    print("=" * 76)
    print(f"  关键模块阈值: {CRITICAL_THRESHOLD:.1f}% │ 业务模块阈值: {BUSINESS_THRESHOLD:.1f}%")
    print(f"  本次检查文件数: {len(checked)}")
    print()

    if checked:
        print(f"  {'文件':<55} {'类别':<10} {'覆盖率':>8}")
        print(f"  {'-' * 55} {'-' * 10} {'-' * 8}")
        for path, cls, pct in sorted(checked, key=lambda x: x[2]):
            print(f"  {path:<55} {cls:<10} {pct:>7.2f}%")
        print()

    if missing_critical:
        print("  关键文件尚未被 backend 实装（B-09/12/15 之前，跳过不算失败）：")
        for cf in missing_critical:
            print(f"    - {cf}")
        print()

    if failures:
        print("  FAIL 列表：")
        for path, cls, pct, threshold in failures:
            print(f"    [{cls}] {path}: {pct:.2f}% < {threshold:.1f}%")
        print()
        print(f"  结果: FAILED （{len(failures)} 个文件未达阈值）")
    else:
        print("  结果: PASSED")
    print("=" * 76)


if __name__ == "__main__":
    raise SystemExit(main())
