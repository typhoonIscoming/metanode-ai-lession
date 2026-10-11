'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSession, clearSession } from '@/lib/auth';
import { Tilt } from '@/components/tilt';

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading } = useSession();
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  useEffect(() => {
    if (mounted && !loading && !user) {
      router.replace('/login');
    }
  }, [mounted, loading, user, router]);

  if (!mounted || loading) {
    return <div className="mx-auto max-w-3xl px-6 pt-20 text-zinc-500 font-mono">loading…</div>;
  }
  if (!user) {
    return <div className="mx-auto max-w-3xl px-6 pt-20 text-zinc-500 font-mono">redirecting…</div>;
  }

  const initial = (user.displayName ?? user.email).slice(0, 1).toUpperCase();
  return (
    <div className="mx-auto max-w-5xl px-6 pt-14 pb-20">
      <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/dashboard</div>
      <div className="flex items-center gap-5 mb-10">
        <div className="h-16 w-16 rounded-xl border border-white/10 bg-gradient-to-br from-cyan-500/40 to-violet-500/40 grid place-items-center text-xl font-mono text-cyan-100">{initial}</div>
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Welcome, {user.displayName ?? user.email.split('@')[0]}</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Signed in as <span className="font-mono text-cyan-300">{user.email}</span> · role <span className="font-mono text-violet-300">{user.role}</span>
          </p>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card title="Browse jobs" body="Latest 75k+ on-chain roles." href="/jobs" />
        <Card title="Companies" body="Top protocols hiring right now." href="/companies" />
        <Card title="Salaries" body="Aggregated comp by skill, level, region." href="/salaries" />
        {user.role === 'employer' ? (
          <Card title="Post a job" body="Publish a new role to 75k candidates." href="/post-a-job" cta="Compose →" />
        ) : (
          <Card title="Saved jobs" body="(Coming in v0.2 — wire bookmarks API.)" href="/jobs" cta="Browse →" />
        )}
        <Card title="Learn" body="Articles, books, bootcamps and tutorials." href="/learn" />
        <Card title="Settings" body="Profile, security, notifications." href="#" cta="Soon" />
      </div>

      <div className="mt-12 pt-6 border-t border-white/5">
        <button
          onClick={() => { clearSession(); router.push('/'); }}
          className="rounded-md px-4 py-2 text-sm border border-rose-500/40 text-rose-300 hover:bg-rose-500/10 transition"
        >
          Sign out
        </button>
      </div>
    </div>
  );
}

function Card({ title, body, href, cta = 'Open →' }: { title: string; body: string; href: string; cta?: string }) {
  return (
    <Tilt className="fade-up">
      <Link href={href} className="glass rounded-xl p-5 group block">
        <div className="text-[15px] text-zinc-100 font-medium group-hover:text-cyan-200 transition">{title}</div>
        <p className="text-sm text-zinc-400 mt-1 leading-relaxed">{body}</p>
        <div className="mt-4 text-xs font-mono text-cyan-300">{cta}</div>
      </Link>
    </Tilt>
  );
}
