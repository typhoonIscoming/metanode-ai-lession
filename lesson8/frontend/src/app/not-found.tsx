import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="mx-auto max-w-2xl px-6 pt-32 pb-32 text-center">
      <div className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-4">err::not_found</div>
      <h1 className="text-6xl md:text-8xl font-semibold tracking-tight">
        <span className="holo-text">404</span>
      </h1>
      <p className="mt-4 text-zinc-400">This block was reverted. Try the home page or browse jobs.</p>
      <div className="mt-8 flex justify-center gap-3">
        <Link href="/" className="btn-glow rounded-md px-5 py-2 text-sm">Home</Link>
        <Link href="/jobs" className="rounded-md px-5 py-2 text-sm border border-white/10 hover:border-cyan-400/40 hover:text-cyan-300">Browse jobs</Link>
      </div>
    </div>
  );
}
