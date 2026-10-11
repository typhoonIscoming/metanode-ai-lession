#!/usr/bin/env node
// 关键组件覆盖率分级门禁（与 docs/test-strategy.md §3.1 对齐）。
// 整体阈值 60% 由 vitest.config.ts 的 thresholds 兜底，本脚本只补 per-file 关键组件 ≥ 80%。
// 关键组件文件若尚未实装（F-03 之前）自动跳过不算失败。
import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, "..");
const COV_PATH = resolve(REPO_ROOT, "coverage/coverage-summary.json");
const CRITICAL_THRESHOLD = 80.0;

// 与 frontend-PRD §10.1 + test-strategy §4 对齐的关键组件清单
const CRITICAL = [
  "components/price-chart.tsx",
  "components/market-card.tsx",
  "components/state-badge.tsx",
  "components/signal-kind-badge.tsx",
  "components/threshold-form.tsx",
  "components/feishu-form.tsx",
  "lib/api.ts",
  "lib/schemas.ts",
];

if (!existsSync(COV_PATH)) {
  console.error(`ERROR: ${COV_PATH} 不存在；先跑 \`pnpm test:coverage\``);
  process.exit(2);
}

const data = JSON.parse(readFileSync(COV_PATH, "utf8"));
const failures = [];
const checked = [];
const missing = [];

for (const rel of CRITICAL) {
  const abs = resolve(REPO_ROOT, rel);
  if (!existsSync(abs)) {
    missing.push(rel);
    continue;
  }
  const entry = data[abs] ?? data[rel];
  if (!entry) {
    failures.push({
      path: rel,
      reason: "在 coverage-summary.json 找不到（可能没被任何测试 import 过）",
    });
    continue;
  }
  const pct = entry.lines?.pct ?? 0;
  checked.push({ path: rel, pct });
  if (pct + 1e-9 < CRITICAL_THRESHOLD) {
    failures.push({ path: rel, reason: `${pct.toFixed(2)}% < ${CRITICAL_THRESHOLD}%` });
  }
}

console.log();
console.log("=".repeat(70));
console.log("  前端关键组件覆盖率门禁（docs/test-strategy.md §3.1）");
console.log("=".repeat(70));
console.log(`  关键组件阈值: ${CRITICAL_THRESHOLD.toFixed(1)}%`);
console.log(`  检查文件数: ${checked.length}`);
console.log();

if (checked.length) {
  for (const { path, pct } of checked.sort((a, b) => a.pct - b.pct)) {
    console.log(`  ${path.padEnd(45)} ${pct.toFixed(2).padStart(6)}%`);
  }
  console.log();
}
if (missing.length) {
  console.log("  关键组件尚未实装（F-03 之前），跳过：");
  for (const p of missing) console.log(`    - ${p}`);
  console.log();
}
if (failures.length) {
  console.log("  FAIL 列表：");
  for (const f of failures) console.log(`    ${f.path}: ${f.reason}`);
  console.log();
  console.log(`  结果: FAILED （${failures.length} 个文件未达阈值）`);
  console.log("=".repeat(70));
  process.exit(1);
}
console.log("  结果: PASSED");
console.log("=".repeat(70));
