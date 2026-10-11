'use client';
import { useState } from 'react';
import { subscribe } from '@/lib/api';

export function NewsletterForm({ source = 'home' }: { source?: string }) {
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'ok' | 'err'>('idle');
  const [message, setMessage] = useState('');

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('loading');
    try {
      const res = await subscribe({ email, firstName, source });
      setStatus('ok');
      setMessage(res.alreadySubscribed ? 'You were already on the list.' : 'Subscribed. Watch your inbox.');
    } catch (err) {
      setStatus('err');
      setMessage(err instanceof Error ? err.message : 'Something went wrong');
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-2 max-w-xl">
      <input
        type="text"
        value={firstName}
        onChange={(e) => setFirstName(e.target.value)}
        placeholder="First name"
        className="px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm placeholder:text-zinc-500 sm:w-32"
      />
      <input
        type="email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="your@email.com"
        className="px-3 py-2.5 rounded-md bg-white/5 border border-white/10 focus:border-cyan-400/60 outline-none text-sm placeholder:text-zinc-500 flex-1"
      />
      <button
        type="submit"
        disabled={status === 'loading'}
        className="btn-glow rounded-md px-5 py-2.5 text-sm font-medium disabled:opacity-50"
      >
        {status === 'loading' ? '…' : 'Subscribe'}
      </button>
      {message && (
        <p className={`text-xs mt-1 sm:basis-full ${status === 'ok' ? 'text-lime-400' : 'text-rose-400'}`}>
          {message}
        </p>
      )}
    </form>
  );
}
