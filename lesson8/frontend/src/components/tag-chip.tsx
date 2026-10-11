import Link from 'next/link';
import { cn } from '@/lib/cn';

const PALETTE: Record<string, string> = {
  skill:    'chip',
  chain:    'chip chip-cyan',
  role:     'chip chip-violet',
  benefit:  'chip',
  region:   'chip chip-cyan',
  seniority:'chip chip-violet',
};

export function TagChip({ slug, name, category, asLink = true }: { slug: string; name: string; category?: string; asLink?: boolean }) {
  const cls = cn(PALETTE[category ?? 'skill'] ?? 'chip', 'whitespace-nowrap');
  if (asLink) return <Link href={`/jobs?tag=${slug}`} className={cls}>{name}</Link>;
  return <span className={cls}>{name}</span>;
}
