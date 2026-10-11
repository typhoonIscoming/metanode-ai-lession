import Link from 'next/link';

const SKUS: Array<{ name: string; price: string; size: string; note: string }> = [
  { name: 'Hero banner',      price: '$3,000 / week', size: '1320 × 220',  note: 'Above-the-fold on homepage. 1 advertiser per week.' },
  { name: 'Sidebar banner',   price: '$1,500 / week', size: '300 × 600',   note: 'Job-listing sidebar across all category pages.' },
  { name: 'Newsletter header', price: '$2,500 / send', size: '1200 × 200', note: 'Weekly newsletter to ~100k subscribers.' },
  { name: 'Sponsored job',    price: '$499 / 14 days', size: 'card',       note: 'Pinned to top of /jobs and tag pages.' },
  { name: 'Twitter promo',    price: '$199 / post',    size: 'tweet',      note: '41k follower account, scheduled in slot of your choice.' },
];

export default function AdvertisePage() {
  return (
    <div className="mx-auto max-w-4xl px-6 pt-20 pb-20">
      <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/advertise</div>
      <h1 className="text-4xl md:text-5xl font-semibold tracking-tight">Reach <span className="holo-text">web3 builders</span></h1>
      <p className="mt-3 text-zinc-400 max-w-2xl">630k monthly readers · 41k Twitter · 9k Discord · 100k newsletter. Pick a placement.</p>
      <div className="mt-10 grid gap-3">
        {SKUS.map((s) => (
          <div key={s.name} className="glass rounded-xl p-5 flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="font-medium text-zinc-100">{s.name}</div>
              <div className="text-sm text-zinc-500 mt-1">{s.note}</div>
              <div className="text-xs font-mono text-zinc-600 mt-1">{s.size}</div>
            </div>
            <div className="font-mono text-cyan-300">{s.price}</div>
          </div>
        ))}
      </div>
      <div className="mt-10 flex gap-3">
        <Link href="mailto:sales@example.com" className="btn-glow rounded-md px-5 py-2 text-sm">Email sales</Link>
        <Link href="/post-a-job" className="rounded-md px-5 py-2 text-sm border border-white/10 hover:border-cyan-400/40 hover:text-cyan-300 transition">Post a job instead</Link>
      </div>
    </div>
  );
}
