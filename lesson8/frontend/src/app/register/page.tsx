'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { authRegister } from '@/lib/api';
import { writeSession } from '@/lib/auth';

export default function RegisterPage() {
  const router = useRouter();
  const [role, setRole] = useState<'candidate' | 'employer'>('candidate');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'err' | 'ok'>('idle');
  const [message, setMessage] = useState('');

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('loading');
    try {
      const res = await authRegister({ role, email, password, displayName: displayName || undefined, companyName: role === 'employer' ? companyName : undefined });
      writeSession({ user: res.user, accessToken: res.accessToken, refreshToken: res.refreshToken });
      router.push('/dashboard');
      router.refresh();
    } catch (err) {
      setStatus('err');
      setMessage(err instanceof Error ? err.message : 'Registration failed');
    }
  }

  return (
    <div className="mx-auto max-w-md px-6 pt-20 pb-20">
      <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/register</div>
      <h1 className="text-3xl font-semibold tracking-tight mb-2">Create account</h1>
      <p className="text-sm text-zinc-500 mb-8">Pick a role — you can always link a company profile later.</p>

      <div className="mb-4 grid grid-cols-2 gap-2">
        {(['candidate', 'employer'] as const).map((r) => (
          <button
            key={r}
            type="button"
            onClick={() => setRole(r)}
            className={`rounded-md px-4 py-2.5 text-sm border transition ${
              role === r ? 'border-cyan-400/60 text-cyan-200 bg-cyan-400/10' : 'border-white/10 text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {r === 'candidate' ? 'Find a job' : 'Hire talent'}
          </button>
        ))}
      </div>

      <form onSubmit={onSubmit} className="glass rounded-xl p-6 space-y-4">
        <label className="block">
          <span className="text-xs uppercase tracking-widest text-zinc-500">Email</span>
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm" />
        </label>
        <label className="block">
          <span className="text-xs uppercase tracking-widest text-zinc-500">Password (≥ 8)</span>
          <input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm" />
        </label>
        <label className="block">
          <span className="text-xs uppercase tracking-widest text-zinc-500">Display name (optional)</span>
          <input type="text" value={displayName} onChange={(e) => setDisplayName(e.target.value)}
            className="mt-1 w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm" />
        </label>
        {role === 'employer' && (
          <label className="block">
            <span className="text-xs uppercase tracking-widest text-zinc-500">Company name</span>
            <input type="text" required value={companyName} onChange={(e) => setCompanyName(e.target.value)}
              className="mt-1 w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm" />
          </label>
        )}
        <button disabled={status === 'loading'} className="btn-glow w-full rounded-md py-2.5 text-sm font-medium disabled:opacity-50">
          {status === 'loading' ? 'Creating…' : 'Create account'}
        </button>
        {message && (
          <p className={`text-xs ${status === 'ok' ? 'text-lime-400' : 'text-rose-400'}`}>{message}</p>
        )}
      </form>

      <p className="mt-6 text-sm text-zinc-500 text-center">
        Already have an account? <Link href="/login" className="text-cyan-300 hover:underline">Sign in</Link>
      </p>
    </div>
  );
}
