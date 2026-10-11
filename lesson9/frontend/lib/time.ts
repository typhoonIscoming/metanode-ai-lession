// UTC ↔ 本地化时间工具
// 项目约定：所有时间存 UTC，展示用 Intl.DateTimeFormat 本地化，tooltip 显示 UTC 原值
import { formatDistanceToNowStrict, formatISO, parseISO } from "date-fns";

/**
 * Date → ISO8601 UTC，强制带 Z 后缀
 */
export function toUtcIso(date: Date): string {
  return formatISO(date, { representation: "complete" }).replace(/[+-]\d{2}:\d{2}$/, "Z");
}

/**
 * ISO 字符串 → Date 对象（带时区信息）
 */
export function fromIso(iso: string): Date {
  return parseISO(iso);
}

/**
 * 浏览器本地化（页面正文展示），秒级精度，24h 制
 */
export function formatLocal(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(parseISO(iso));
}

/**
 * 表格 / 列表用紧凑格式：MM/dd HH:mm（本地化）
 */
export function formatLocalCompact(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(parseISO(iso));
}

/**
 * tooltip 显示：UTC 原值 + 本地化对照
 */
export function formatUtcTooltip(iso: string): string {
  return `${iso} (本地 ${formatLocal(iso)})`;
}

/**
 * 相对时间："2 分钟前" / "刚刚"
 */
export function formatRelativeFromNow(iso: string): string {
  const d = parseISO(iso);
  const diffMs = Date.now() - d.getTime();
  if (diffMs < 60_000) return "刚刚";
  return `${formatDistanceToNowStrict(d, { addSuffix: false })} 前`;
}

/**
 * 倒计时："剩 8h 23m" / "剩 3d 5h" / "已过期"
 */
export function formatCountdown(iso: string): string {
  const target = parseISO(iso);
  const diffMs = target.getTime() - Date.now();
  if (diffMs <= 0) return "已过期";
  const totalMinutes = Math.floor(diffMs / 60_000);
  const days = Math.floor(totalMinutes / (60 * 24));
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
  const minutes = totalMinutes % 60;
  if (days > 0) return `剩 ${days}d ${hours}h`;
  if (hours > 0) return `剩 ${hours}h ${minutes}m`;
  return `剩 ${minutes}m`;
}

/**
 * 距 ISO 还有多少毫秒（用于状态机临近结算判定）
 */
export function msUntil(iso: string): number {
  return parseISO(iso).getTime() - Date.now();
}

/**
 * 今天 00:00 UTC 的 ISO（用于「今日推送」类查询）
 */
export function todayStartUtcIso(): string {
  const now = new Date();
  const utc = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  return utc.toISOString();
}

/**
 * N 天前 UTC ISO
 */
export function daysAgoUtcIso(days: number): string {
  return new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();
}
