import Link from 'next/link';
import { api } from '@/lib/api';
import { JobCard } from '@/components/job-card';
import { TagChip } from '@/components/tag-chip';

export const revalidate = 30;

interface PageProps {
  searchParams: Promise<{ tag?: string; remote?: string; q?: string; page?: string; sort?: string }>;
}

export default async function JobsPage({ searchParams }: PageProps) {
  const sp = await searchParams;
  const page = sp.page ? Number(sp.page) : 1;
  const tag = sp.tag;
  const remote = sp.remote === '1' || sp.remote === 'true';
  const q = sp.q?.trim();
  const sort = (sp.sort === 'salary' ? 'salary' : 'recent') as 'recent' | 'salary';

  const [{ data, meta }, tags] = await Promise.all([
    api.jobs.list({ page, limit: 25, tag, remote: remote || undefined, q, sort }),
    api.tags.popular(40),
  ]);

  const heading = tag ? toTitleCase(tag) + ' Jobs' : remote ? 'Remote Web3 Jobs' : 'Web3 Jobs';

  return (
    <>
      <section className="mx-auto max-w-7xl px-6 pt-14 pb-6">
        <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">
          /{tag ? `${tag}-jobs` : remote ? 'remote-jobs' : 'jobs'}
        </div>
        <h1 className="text-4xl md:text-5xl font-semibold tracking-tight">
          {heading}
        </h1>
        <p className="mt-3 text-zinc-400">
          {meta.pagination.total.toLocaleString()} roles found · sorted by {sort === 'salary' ? 'salary' : 'most recent'}.
        </p>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-3">
        <form className="flex flex-wrap items-center gap-2">
          <input
            type="text"
            name="q"
            defaultValue={q}
            placeholder="Search title or description…"
            className="px-3 py-2 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm placeholder:text-zinc-500 w-72"
          />
          <label className="flex items-center gap-2 text-sm text-zinc-400">
            <input type="checkbox" name="remote" value="1" defaultChecked={remote} className="accent-cyan-400" /> Remote only
          </label>
          <select name="sort" defaultValue={sort} className="bg-white/5 border border-white/10 rounded-md px-2 py-2 text-sm">
            <option value="recent">Most recent</option>
            <option value="salary">Highest salary</option>
          </select>
          {tag && <input type="hidden" name="tag" value={tag} />}
          <button className="btn-glow rounded-md px-4 py-2 text-sm">Apply</button>
          {(tag || remote || q || sort !== 'recent') && (
            <Link href="/jobs" className="text-sm text-zinc-500 hover:text-cyan-300">Clear</Link>
          )}
        </form>

        <div className="mt-5 flex flex-wrap gap-1.5">
          {tags.slice(0, 24).map((t) => (
            <TagChip key={t.slug} slug={t.slug} name={t.name} category={t.category} />
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-20 grid gap-3">
        {data.length === 0 && (
          <div className="glass rounded-xl p-10 text-center text-zinc-500">
            No jobs match these filters. <Link href="/jobs" className="text-cyan-300 hover:underline">Reset filters →</Link>
          </div>
        )}
        {data.map((j) => <JobCard key={j.id} job={j} />)}
      </section>

      {meta.pagination.totalPages > 1 && (
        <nav className="mx-auto max-w-7xl px-6 pb-20 flex items-center justify-between text-sm">
          {page > 1 ? (
            <Link href={pageHref({ ...sp, page: String(page - 1) })} className="text-zinc-300 hover:text-cyan-300">← Prev</Link>
          ) : <span />}
          <span className="font-mono text-zinc-500">Page {page} / {meta.pagination.totalPages}</span>
          {page < meta.pagination.totalPages ? (
            <Link href={pageHref({ ...sp, page: String(page + 1) })} className="text-zinc-300 hover:text-cyan-300">Next →</Link>
          ) : <span />}
        </nav>
      )}
    </>
  );
}

function pageHref(sp: Record<string, string | undefined>) {
  const usp = new URLSearchParams();
  Object.entries(sp).forEach(([k, v]) => { if (v) usp.set(k, v); });
  return '/jobs?' + usp.toString();
}

function toTitleCase(slug: string): string {
  return slug.split(/[-_ ]+/).map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
}
