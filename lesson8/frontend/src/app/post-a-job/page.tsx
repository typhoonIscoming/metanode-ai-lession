'use client';
import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useSession } from '@/lib/auth';
import { api, createJob, type TagDto } from '@/lib/api';

const SENIORITIES = ['intern', 'junior', 'mid', 'senior', 'lead', 'exec'] as const;
const EMPLOYMENT  = ['full_time', 'part_time', 'contract', 'internship'] as const;

export default function PostJobPage() {
  const router = useRouter();
  const { user, loading } = useSession();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('Remote');
  const [isRemote, setIsRemote] = useState(true);
  const [seniority, setSeniority] = useState<typeof SENIORITIES[number]>('senior');
  const [employmentType, setEmploymentType] = useState<typeof EMPLOYMENT[number]>('full_time');
  const [salaryMin, setSalaryMin] = useState<string>('120000');
  const [salaryMax, setSalaryMax] = useState<string>('180000');
  const [applyUrl, setApplyUrl] = useState('');
  const [allTags, setAllTags] = useState<TagDto[]>([]);
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [status, setStatus] = useState<'idle' | 'loading' | 'err'>('idle');
  const [message, setMessage] = useState('');

  useEffect(() => {
    api.tags.popular(80).then(setAllTags).catch(() => setAllTags([]));
  }, []);

  useEffect(() => {
    if (!loading && !user) router.replace('/login?next=/post-a-job');
  }, [loading, user, router]);

  const canEmploy = user?.role === 'employer' || user?.role === 'admin';
  const groupedTags = useMemo(() => {
    const m = new Map<string, TagDto[]>();
    for (const t of allTags) {
      const arr = m.get(t.category) ?? [];
      arr.push(t);
      m.set(t.category, arr);
    }
    return Array.from(m.entries());
  }, [allTags]);

  function toggleTag(slug: string) {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug); else next.add(slug);
      return next;
    });
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('loading');
    setMessage('');
    try {
      if (description.length < 30) throw new Error('Description must be at least 30 characters.');
      if (selectedTags.size === 0) throw new Error('Select at least one tag.');
      const job = await createJob({
        title, description, location: location || undefined, isRemote,
        seniority, employmentType,
        salaryMin: salaryMin ? Number(salaryMin) : undefined,
        salaryMax: salaryMax ? Number(salaryMax) : undefined,
        applyType: 'external', applyUrl: applyUrl || undefined,
        tags: Array.from(selectedTags),
      });
      router.push(`/jobs/${job.slug}`);
    } catch (err) {
      setStatus('err');
      setMessage(err instanceof Error ? err.message : 'Could not create job.');
    }
  }

  if (loading) return <P>loading…</P>;
  if (!user)   return <P>redirecting…</P>;
  if (!canEmploy) {
    return (
      <div className="mx-auto max-w-2xl px-6 pt-20 pb-20">
        <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/post-a-job</div>
        <h1 className="text-3xl font-semibold tracking-tight">Employer account required</h1>
        <p className="mt-3 text-zinc-400">You are signed in as <span className="font-mono text-cyan-300">{user.email}</span> (role <span className="font-mono text-violet-300">{user.role}</span>). Posting requires an employer account.</p>
        <div className="mt-6 flex gap-3">
          <Link href="/register" className="btn-glow rounded-md px-5 py-2 text-sm">Create an employer account</Link>
          <Link href="/jobs" className="rounded-md px-5 py-2 text-sm border border-white/10 hover:border-cyan-400/40 hover:text-cyan-300 transition">Browse jobs instead</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 pt-14 pb-20">
      <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/post-a-job</div>
      <h1 className="text-4xl font-semibold tracking-tight">Post a <span className="holo-text">Web3</span> job</h1>
      <p className="mt-3 text-zinc-400">Goes live immediately. Showcased to 630k monthly readers.</p>

      <form onSubmit={onSubmit} className="mt-10 glass rounded-xl p-6 space-y-5">
        <Field label="Title">
          <input value={title} onChange={(e) => setTitle(e.target.value)} required minLength={3} maxLength={160}
            placeholder="Senior Solidity Engineer"
            className="w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm" />
        </Field>

        <Field label="Description (Markdown supported · min 30 chars)">
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} required minLength={30} rows={10}
            placeholder="What does the role look like? Who would thrive? What does success in 90 days look like?"
            className="w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm font-mono leading-relaxed" />
        </Field>

        <div className="grid sm:grid-cols-2 gap-4">
          <Field label="Location">
            <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Remote / New York, US"
              className="w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm" />
          </Field>
          <Field label="Remote-friendly">
            <label className="inline-flex items-center gap-2 text-sm text-zinc-300 mt-2.5">
              <input type="checkbox" checked={isRemote} onChange={(e) => setIsRemote(e.target.checked)} className="accent-cyan-400" />
              Remote OK
            </label>
          </Field>
          <Field label="Seniority">
            <select value={seniority} onChange={(e) => setSeniority(e.target.value as any)}
              className="w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm">
              {SENIORITIES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </Field>
          <Field label="Type">
            <select value={employmentType} onChange={(e) => setEmploymentType(e.target.value as any)}
              className="w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm">
              {EMPLOYMENT.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
            </select>
          </Field>
          <Field label="Salary min (USD)">
            <input type="number" min={0} max={1000000} value={salaryMin} onChange={(e) => setSalaryMin(e.target.value)}
              className="w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm font-mono" />
          </Field>
          <Field label="Salary max (USD)">
            <input type="number" min={0} max={1000000} value={salaryMax} onChange={(e) => setSalaryMax(e.target.value)}
              className="w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm font-mono" />
          </Field>
        </div>

        <Field label="Apply URL (external)">
          <input type="url" value={applyUrl} onChange={(e) => setApplyUrl(e.target.value)} placeholder="https://yourcompany.com/jobs/xyz"
            className="w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm font-mono" />
        </Field>

        <Field label={`Tags (${selectedTags.size} selected · at least 1)`}>
          <div className="space-y-3">
            {groupedTags.map(([cat, items]) => (
              <div key={cat}>
                <div className="text-[11px] uppercase tracking-widest text-zinc-500 mb-1.5 font-mono">{cat}</div>
                <div className="flex flex-wrap gap-1.5">
                  {items.map((t) => (
                    <button type="button" key={t.slug} onClick={() => toggleTag(t.slug)}
                      className={`rounded-full px-2.5 py-0.5 text-xs font-mono border transition ${
                        selectedTags.has(t.slug)
                          ? 'border-cyan-400/60 bg-cyan-400/10 text-cyan-200'
                          : 'border-white/10 text-zinc-400 hover:text-zinc-200'
                      }`}>
                      {t.name}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Field>

        <button type="submit" disabled={status === 'loading'} className="btn-glow rounded-md w-full py-2.5 text-sm font-medium disabled:opacity-50">
          {status === 'loading' ? 'Publishing…' : 'Publish job'}
        </button>
        {message && <p className="text-xs text-rose-400">{message}</p>}
      </form>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs uppercase tracking-widest text-zinc-500">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

function P({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto max-w-3xl px-6 pt-20 text-zinc-500 font-mono">{children}</div>;
}
