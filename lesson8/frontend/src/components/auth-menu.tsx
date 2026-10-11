'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useSession, clearSession } from '@/lib/auth';

export function AuthMenu() {
  const { user, loading } = useSession();
  const [open, setOpen] = useState(false);

  if (loading) {
    return <span className="text-sm text-zinc-500 font-mono">…</span>;
  }
  if (!user) {
    return (
      <Link href="/login" className="text-sm text-zinc-300 hover:text-white">Sign in</Link>
    );
  }

  const initial = (user.displayName ?? user.email).slice(0, 1).toUpperCase();
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-md border border-white/10 px-2 py-1 text-sm hover:border-cyan-400/40 transition"
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <span className="h-6 w-6 rounded-full grid place-items-center bg-gradient-to-br from-cyan-500/40 to-violet-500/40 text-[11px] font-mono text-cyan-100">{initial}</span>
        <span className="hidden sm:inline text-zinc-200 max-w-[120px] truncate">{user.displayName ?? user.email}</span>
        <span className="text-zinc-500 text-xs">▾</span>
      </button>
      {open && (
        <div role="menu" className="absolute right-0 mt-2 w-56 rounded-md border border-white/10 bg-[#0a0e1a]/95 backdrop-blur-xl shadow-lg py-1.5 z-50">
          <div className="px-3 py-2 border-b border-white/5">
            <div className="text-xs text-zinc-500 uppercase tracking-widest">{user.role}</div>
            <div className="text-sm text-zinc-200 truncate">{user.email}</div>
          </div>
          <MenuLink href="/dashboard" onClick={() => setOpen(false)}>Dashboard</MenuLink>
          {user.role === 'employer' && (
            <MenuLink href="/post-a-job" onClick={() => setOpen(false)}>Post a job</MenuLink>
          )}
          <MenuLink href="/jobs" onClick={() => setOpen(false)}>Browse jobs</MenuLink>
          <button
            type="button"
            onClick={() => { clearSession(); setOpen(false); window.location.href = '/'; }}
            className="w-full text-left px-3 py-2 text-sm text-rose-300 hover:bg-white/5 transition"
          >
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}

function MenuLink({ href, onClick, children }: { href: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <Link href={href} onClick={onClick} className="block px-3 py-2 text-sm text-zinc-200 hover:bg-white/5 hover:text-cyan-200 transition">
      {children}
    </Link>
  );
}
