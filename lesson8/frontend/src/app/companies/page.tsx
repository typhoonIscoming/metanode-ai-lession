import Link from 'next/link';
import { api } from '@/lib/api';
import { Tilt } from '@/components/tilt';

export const revalidate = 60;

export default async function CompaniesPage() {
  const { data, meta } = await api.companies.list({ limit: 50 });
  return (
    <>
      <section className="mx-auto max-w-7xl px-6 pt-14 pb-6">
        <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/companies</div>
        <h1 className="text-4xl md:text-5xl font-semibold tracking-tight">
          Top <span className="holo-text">Web3</span> companies
        </h1>
        <p className="mt-3 text-zinc-400">
          {meta.pagination.total.toLocaleString()} verified protocols, L2s, auditors and on-chain games.
        </p>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-20 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.map((c) => (
          <Tilt key={c.id} className="fade-up">
            <Link href={`/jobs?company=${c.slug}`} className="glass group rounded-xl p-5 block">
              <div className="flex items-start gap-4">
                <div className="h-12 w-12 shrink-0 rounded-lg border border-white/10 bg-gradient-to-br from-violet-500/20 to-cyan-500/20 grid place-items-center">
                  <span className="font-mono text-sm text-cyan-200">{c.name.slice(0, 2).toUpperCase()}</span>
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-medium text-[15px] text-zinc-50 truncate group-hover:text-cyan-200 transition-colors">
                    {c.name}
                  </h3>
                  <p className="text-sm text-zinc-400 mt-1 line-clamp-2">{c.description ?? '—'}</p>
                  <div className="mt-3 flex items-center justify-between text-xs font-mono text-zinc-500">
                    <span>{c.hqCity ?? '—'}{c.hqCountry ? `, ${c.hqCountry}` : ''}</span>
                    <span className="text-cyan-300">{c.openRolesCount} open</span>
                  </div>
                </div>
              </div>
            </Link>
          </Tilt>
        ))}
      </section>
    </>
  );
}
