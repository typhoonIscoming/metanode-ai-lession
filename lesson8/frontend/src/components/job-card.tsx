import Link from 'next/link';
import type { JobSummary } from '@/lib/api';
import { TagChip } from './tag-chip';
import { formatSalary, relativeTime } from '@/lib/format';
import { Tilt } from './tilt';

export function JobCard({ job }: { job: JobSummary }) {
  return (
    <Tilt className="fade-up">
      <Link
        href={`/jobs/${job.slug}`}
        className="glass group block rounded-xl p-5"
      >
      <div className="flex items-start gap-4">
        <div className="relative h-12 w-12 shrink-0 rounded-lg border border-white/10 bg-gradient-to-br from-violet-500/20 to-cyan-500/20 grid place-items-center overflow-hidden">
          <span className="font-mono text-sm text-cyan-200">{job.company?.name.slice(0, 2).toUpperCase() ?? 'W3'}</span>
          <span className="absolute inset-0 ring-1 ring-cyan-400/0 group-hover:ring-cyan-400/40 transition rounded-lg" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <h3 className="font-medium text-[15px] text-zinc-50 truncate group-hover:text-cyan-200 transition-colors">
                {job.title}
              </h3>
              <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12.5px] text-zinc-400">
                <span className="text-zinc-200">{job.company?.name ?? 'Independent'}</span>
                <span className="text-zinc-600">·</span>
                <span className="flex items-center gap-1">
                  {job.isRemote ? <span className="text-lime-400">◉</span> : <span className="text-zinc-500">◌</span>}
                  {job.location ?? 'Remote'}
                </span>
                <span className="text-zinc-600">·</span>
                <span className="font-mono text-cyan-300">{formatSalary(job.salaryMin, job.salaryMax, job.salaryCurrency)}</span>
                <span className="text-zinc-600">·</span>
                <span className="font-mono text-zinc-500">{relativeTime(job.postedAt)}</span>
              </div>
            </div>
          </div>

          <div className="mt-3 flex flex-wrap gap-1.5">
            {job.tags.slice(0, 6).map((t) => (
              <TagChip key={t.slug} slug={t.slug} name={t.name} category={t.category} asLink={false} />
            ))}
            {job.tags.length > 6 && (
              <span className="chip">+{job.tags.length - 6}</span>
            )}
          </div>
        </div>
      </div>
      </Link>
    </Tilt>
  );
}
