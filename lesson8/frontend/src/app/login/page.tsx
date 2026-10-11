'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { authLogin } from '@/lib/api';
import { writeSession } from '@/lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('demo-candidate@web3career.local');
  const [password, setPassword] = useState('password1');
  const [status, setStatus] = useState<'idle' | 'loading' | 'err'>('idle');
  const [message, setMessage] = useState('');

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('loading');
    setMessage('');
    try {
      const res = await authLogin({ email, password });
      writeSession({ user: res.user, accessToken: res.accessToken, refreshToken: res.refreshToken });
      router.push('/dashboard');
      router.refresh();
    } catch (err) {
      setStatus('err');
      setMessage(err instanceof Error ? err.message : 'Login failed');
    }
  }

  return (
    <div className="mx-auto max-w-md px-6 pt-20 pb-20">
      <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/login</div>
      <h1 className="text-3xl font-semibold tracking-tight mb-2">Sign in</h1>
      <p className="text-sm text-zinc-500 mb-8">Default demo account is pre-filled.</p>

      <form onSubmit={onSubmit} className="glass rounded-xl p-6 space-y-4">
        <label className="block">
          <span className="text-xs uppercase tracking-widest text-zinc-500">Email</span>
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm" />
        </label>
        <label className="block">
          <span className="text-xs uppercase tracking-widest text-zinc-500">Password</span>
          <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm" />
        </label>
        <button disabled={status === 'loading'} className="btn-glow w-full rounded-md py-2.5 text-sm font-medium disabled:opacity-50">
          {status === 'loading' ? 'Signing in…' : 'Sign in'}
        </button>
        {message && <p className="text-xs text-rose-400">{message}</p>}
      </form>

      <p className="mt-6 text-sm text-zinc-500 text-center">
        New here? <Link href="/register" className="text-cyan-300 hover:underline">Create an account</Link>
      </p>
    </div>
  );
}
