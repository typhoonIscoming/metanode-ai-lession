// 数值格式化工具：后端返字符串 Decimal，UI 层负责解析与显示精度
// 设计原则：所有函数对 null/undefined 友好（返回占位 "—"）

const DASH = "—";

/**
 * 把字符串/数字转 number；解析失败返回 null，调用方决定回退。
 */
export function toNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : null;
}

/**
 * 概率值（0..1）格式化为百分比字符串：0.7234 → "72%"（默认 0 位小数）
 */
export function formatPercent(
  value: string | number | null | undefined,
  fractionDigits = 0,
): string {
  const n = toNumber(value);
  if (n === null) return DASH;
  return `${(n * 100).toFixed(fractionDigits)}%`;
}

/**
 * 概率值（0..1）保留 4 位小数：0.7234 → "0.7234"
 */
export function formatProbability(value: string | number | null | undefined): string {
  const n = toNumber(value);
  if (n === null) return DASH;
  return n.toFixed(4);
}

/**
 * 价差（gap = p_ai - p_mkt）格式化：+0.17 / -0.03 / 0.00（带符号）
 */
export function formatGap(value: string | number | null | undefined): string {
  const n = toNumber(value);
  if (n === null) return DASH;
  const sign = n > 0 ? "+" : "";
  return `${sign}${n.toFixed(2)}`;
}

/**
 * 价差正负判定，用于配色：positive 看涨 / negative 看跌 / neutral 接近 0
 */
export type GapTone = "positive" | "negative" | "neutral";
export function gapTone(value: string | number | null | undefined, eps = 0.01): GapTone {
  const n = toNumber(value);
  if (n === null || Math.abs(n) < eps) return "neutral";
  return n > 0 ? "positive" : "negative";
}

/**
 * 现货价格格式化：107500.00 → "$107,500"
 */
export function formatSpotPrice(value: string | number | null | undefined): string {
  const n = toNumber(value);
  if (n === null) return DASH;
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

/**
 * 行权价格式化
 */
export function formatStrikePrice(value: string | number | null | undefined): string {
  return formatSpotPrice(value);
}

/**
 * 年化波动率：0.45 → "45.0%"
 */
export function formatVolatility(value: string | number | null | undefined): string {
  return formatPercent(value, 1);
}

/**
 * 模型版本简写：透传，后续可在此处加标签化处理
 */
export function formatModelVersion(version: string): string {
  return version;
}

/**
 * 信号 kind 中文化标题
 */
export function signalKindLabel(kind: string): string {
  switch (kind) {
    case "ENTRY_LONG":
      return "入场 · 看涨";
    case "ENTRY_SHORT":
      return "入场 · 看跌";
    case "EXIT_LONG":
      return "兑现 · 平 YES";
    case "EXIT_SHORT":
      return "兑现 · 平 NO";
    case "EXPIRED":
      return "市场已结算";
    default:
      return kind;
  }
}

/**
 * 市场状态中文化
 */
export function marketStateLabel(state: string): string {
  switch (state) {
    case "WATCHING":
      return "监控中";
    case "ENTERED_LONG":
      return "已入场 · 看涨";
    case "ENTERED_SHORT":
      return "已入场 · 看跌";
    case "EXPIRED":
      return "已结算";
    default:
      return state;
  }
}

/**
 * LLM 置信度中文化
 */
export function confidenceLabel(c: string | null | undefined): string {
  if (!c) return DASH;
  switch (c) {
    case "low":
      return "低";
    case "medium":
      return "中";
    case "high":
      return "高";
    default:
      return c;
  }
}

/**
 * 数字千位分隔
 */
export function formatInt(value: number | null | undefined): string {
  if (value === null || value === undefined) return DASH;
  return value.toLocaleString();
}
