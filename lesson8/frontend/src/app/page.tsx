import Link from 'next/link';
import { api } from '@/lib/api';
import { JobCard } from '@/components/job-card';
import { TagChip } from '@/components/tag-chip';
import { NewsletterForm } from '@/components/newsletter-form';
import { StatCounter } from '@/components/stat-counter';
import { HeroScene } from '@/components/hero-scene-mount';

export const revalidate = 60;

export default async function HomePage() {
  const [jobs, tags] = await Promise.all([
    api.jobs.list({ limit: 12, sort: 'recent' }).catch(() => ({ data: [], meta: { pagination: { total: 0 } as any } })),
    api.tags.popular(40).catch(() => []),
  ]);
  const totalJobs = jobs.meta?.pagination?.total ?? jobs.data.length;
  const totalCompanies = new Set(jobs.data.map((j) => j.company?.id).filter(Boolean)).size || 7;

  return (
    <>
      {/* Hero */}
      <section className="relative">
        <HeroScene />
        <div className="mx-auto max-w-7xl px-6 pt-20 pb-12 md:pt-28 md:pb-20">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-zinc-400 mb-6">
              <span className="h-1.5 w-1.5 rounded-full bg-lime-400 animate-pulse" />
              <span className="font-mono">LIVE · {totalJobs.toLocaleString()} on-chain roles indexed</span>
            </div>

            <h1 className="text-5xl md:text-7xl font-semibold tracking-tight leading-[1.05]">
              The job board for <span className="holo-text">web3 builders</span>.
            </h1>
            <p className="mt-6 text-lg text-zinc-400 max-w-2xl">
              Discover blockchain, smart contract and crypto jobs at the most-funded protocols, audits, L2s and on-chain games. Updated every block.
            </p>

            <div className="mt-8">
              <NewsletterForm source="home_hero" />
            </div>
          </div>

          {/* Stats */}
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-8 border-y border-white/5 py-8">
            <StatCounter value={totalJobs} label="Open roles" />
            <StatCounter value={Math.max(totalCompanies, 7)} label="Live protocols" />
            <StatCounter value={631_803} label="Monthly readers" />
            <StatCounter value={41_000} label="Twitter followers" suffix="+" />
          </div>
        </div>
      </section>

      {/* Tag cloud */}
      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="flex flex-wrap gap-2">
          {tags.slice(0, 36).map((t) => (
            <TagChip key={t.slug} slug={t.slug} name={t.name} category={t.category} />
          ))}
          <Link href="/jobs" className="chip chip-cyan">all tags →</Link>
        </div>
      </section>

      {/* Latest jobs */}
      <section className="mx-auto max-w-7xl px-6 pt-10 pb-20">
        <div className="flex items-end justify-between mb-6">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">Latest opportunities</h2>
            <p className="text-sm text-zinc-500 mt-1">Hand-picked roles indexed in the last 14 days.</p>
          </div>
          <Link href="/jobs" className="text-sm text-cyan-300 hover:text-cyan-200">Browse all →</Link>
        </div>

        <div className="grid gap-3">
          {jobs.data.length === 0 && (
            <p className="text-zinc-500 text-sm">No jobs indexed yet — run <code className="font-mono text-cyan-300">pnpm db:seed</code> in the backend.</p>
          )}
          {jobs.data.map((j) => (
            <JobCard key={j.id} job={j} />
          ))}
        </div>
      </section>
    </>
  );
}
