export function formatSalary(min?: number | null, max?: number | null, currency = 'USD'): string {
  if (!min && !max) return 'Salary undisclosed';
  const fmt = (n: number) => (n >= 1000 ? `${Math.round(n / 1000)}k` : `${n}`);
  const symbol = currency === 'USD' ? '$' : currency + ' ';
  if (min && max) return `${symbol}${fmt(min)} – ${symbol}${fmt(max)}`;
  if (min) return `${symbol}${fmt(min)}+`;
  return `up to ${symbol}${fmt(max!)}`;
}

export function relativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const diff = Date.now() - d.getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hrs = Math.floor(min / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  return `${Math.floor(months / 12)}y ago`;
}

export function formatCount(n: number): string {
  return new Intl.NumberFormat('en-US').format(n);
}
