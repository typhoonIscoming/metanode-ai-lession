import Link from 'next/link';
import { notFound } from 'next/navigation';
import { api } from '@/lib/api';
import { TagChip } from '@/components/tag-chip';
import { formatSalary, relativeTime } from '@/lib/format';
import type { Metadata } from 'next';

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  try {
    const job = await api.jobs.bySlug(slug);
    return {
      title: `${job.title} at ${job.company?.name} — web3.career`,
      description: job.description.slice(0, 160),
    };
  } catch {
    return { title: 'Job not found' };
  }
}

export default async function JobDetailPage({ params }: PageProps) {
  const { slug } = await params;
  let job;
  try { job = await api.jobs.bySlug(slug); } catch { notFound(); }
  if (!job) notFound();

  return (
    <article className="mx-auto max-w-5xl px-6 pt-14 pb-20">
      <div className="text-xs font-mono text-zinc-500 mb-6">
        <Link href="/jobs" className="hover:text-cyan-300">/jobs</Link>
        <span className="text-zinc-700"> / </span>
        <span className="text-zinc-400">{job.slug}</span>
      </div>

      <header className="glass rounded-xl p-7">
        <div className="flex items-start gap-5">
          <div className="h-16 w-16 shrink-0 rounded-xl border border-white/10 bg-gradient-to-br from-violet-500/30 to-cyan-500/30 grid place-items-center">
            <span className="font-mono text-base text-cyan-200">{job.company?.name.slice(0, 2).toUpperCase() ?? 'W3'}</span>
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">{job.title}</h1>
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1.5 text-sm text-zinc-400">
              <span className="text-zinc-200">{job.company?.name}</span>
              <span className="text-zinc-700">·</span>
              <span>{job.isRemote ? '◉ Remote' : `◌ ${job.location}`}</span>
              <span className="text-zinc-700">·</span>
              <span className="font-mono text-cyan-300">{formatSalary(job.salaryMin, job.salaryMax)}</span>
              <span className="text-zinc-700">·</span>
              <span className="font-mono text-zinc-500">posted {relativeTime(job.postedAt)}</span>
              <span className="text-zinc-700">·</span>
              <span className="font-mono text-zinc-500">{job.viewsCount} views</span>
            </div>
            <div className="mt-4 flex flex-wrap gap-1.5">
              {job.tags.map((t) => <TagChip key={t.slug} slug={t.slug} name={t.name} category={t.category} />)}
            </div>
            <div className="mt-6 flex flex-wrap gap-3">
              {job.applyType === 'external' && job.applyUrl ? (
                <a href={job.applyUrl} target="_blank" rel="noopener noreferrer" className="btn-glow rounded-md px-6 py-2.5 text-sm font-medium">
                  Apply on company site ↗
                </a>
              ) : (
                <button className="btn-glow rounded-md px-6 py-2.5 text-sm font-medium">
                  Apply via web3.career
                </button>
              )}
              <button className="rounded-md px-4 py-2.5 text-sm border border-white/10 hover:border-cyan-400/40 hover:text-cyan-300 transition">
                Save · 𝄞
              </button>
              <button className="rounded-md px-4 py-2.5 text-sm border border-white/10 hover:border-cyan-400/40 hover:text-cyan-300 transition">
                Share · ⌁
              </button>
            </div>
          </div>
        </div>
      </header>

      <section className="prose prose-invert mt-10 max-w-none">
        <h2 className="text-xl font-semibold tracking-tight mb-3 text-zinc-100">About the role</h2>
        <div className="text-zinc-300 leading-relaxed whitespace-pre-wrap">{job.description}</div>
      </section>

      <section className="mt-12 border-t border-white/5 pt-8">
        <h3 className="text-sm uppercase tracking-widest text-zinc-500 mb-3">Job metadata</h3>
        <dl className="grid grid-cols-2 md:grid-cols-4 gap-y-4 gap-x-8 font-mono text-sm">
          <Meta k="seniority" v={job.seniority ?? '—'} />
          <Meta k="type" v={job.employmentType ?? '—'} />
          <Meta k="location" v={job.location ?? 'Remote'} />
          <Meta k="apply" v={job.applyType} />
        </dl>
      </section>
    </article>
  );
}

function Meta({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-zinc-500 text-xs uppercase">{k}</dt>
      <dd className="text-zinc-200">{v}</dd>
    </div>
  );
}
