import { salariesApi } from '@/lib/api';
import { Tilt } from '@/components/tilt';
import { SalaryBars3D } from '@/components/salary-bars-3d-mount';

export const revalidate = 120;

function fmtUsd(n: number | null | undefined): string {
  if (!n) return '—';
  if (n >= 1000) return `$${Math.round(n / 1000)}k`;
  return `$${n}`;
}

export default async function SalariesPage() {
  const snap = await salariesApi.snapshot();
  return (
    <div className="mx-auto max-w-7xl px-6 pt-14 pb-20">
      <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/salaries</div>
      <h1 className="text-4xl md:text-5xl font-semibold tracking-tight">
        Web3 <span className="holo-text">salary</span> snapshot
      </h1>
      <p className="mt-3 text-zinc-400 max-w-2xl">
        Aggregated from live on-chain roles indexed in our database. Updated every hour.
      </p>

      {/* summary */}
      <div className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-4">
        <Kpi label="Roles indexed" value={snap.overall?.job_count ?? 0} suffix="" />
        <Kpi label="Avg min" value={snap.overall?.avg_min ?? 0} prefix="$" suffix="" />
        <Kpi label="Avg max" value={snap.overall?.avg_max ?? 0} prefix="$" suffix="" />
        <Kpi label="Top recorded" value={snap.overall?.max_max ?? 0} prefix="$" suffix="" />
      </div>

      {/* 3D bars */}
      <section className="mt-12">
        <h2 className="text-xl font-semibold tracking-tight mb-4">Top roles by ceiling salary</h2>
        <SalaryBars3D rows={snap.byRole.slice(0, 10)} />
      </section>

      {/* by role */}
      <section className="mt-12">
        <h2 className="text-xl font-semibold tracking-tight mb-4">By skill / role</h2>
        <div className="glass rounded-xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-widest text-zinc-500 border-b border-white/5">
                <th className="px-4 py-3">Tag</th>
                <th className="px-4 py-3 text-right">Roles</th>
                <th className="px-4 py-3 text-right">Avg min</th>
                <th className="px-4 py-3 text-right">Avg max</th>
                <th className="px-4 py-3 text-right">Floor</th>
                <th className="px-4 py-3 text-right">Ceiling</th>
              </tr>
            </thead>
            <tbody>
              {snap.byRole.map((r) => (
                <tr key={r.slug} className="border-b border-white/5 hover:bg-white/[0.02] transition">
                  <td className="px-4 py-3 font-medium text-zinc-100">{r.name}</td>
                  <td className="px-4 py-3 text-right font-mono text-zinc-400">{r.job_count}</td>
                  <td className="px-4 py-3 text-right font-mono text-zinc-200">{fmtUsd(r.avg_min)}</td>
                  <td className="px-4 py-3 text-right font-mono text-cyan-300">{fmtUsd(r.avg_max)}</td>
                  <td className="px-4 py-3 text-right font-mono text-zinc-500">{fmtUsd(r.min_min)}</td>
                  <td className="px-4 py-3 text-right font-mono text-zinc-500">{fmtUsd(r.max_max)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid md:grid-cols-2 gap-6 mt-12">
        {/* seniority */}
        <section>
          <h2 className="text-xl font-semibold tracking-tight mb-4">By seniority</h2>
          <div className="glass rounded-xl overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-widest text-zinc-500 border-b border-white/5">
                  <th className="px-4 py-3">Level</th>
                  <th className="px-4 py-3 text-right">Roles</th>
                  <th className="px-4 py-3 text-right">Avg min</th>
                  <th className="px-4 py-3 text-right">Avg max</th>
                </tr>
              </thead>
              <tbody>
                {snap.bySeniority.map((r) => (
                  <tr key={r.seniority} className="border-b border-white/5">
                    <td className="px-4 py-3 capitalize text-zinc-100">{r.seniority}</td>
                    <td className="px-4 py-3 text-right font-mono text-zinc-400">{r.job_count}</td>
                    <td className="px-4 py-3 text-right font-mono text-zinc-200">{fmtUsd(r.avg_min)}</td>
                    <td className="px-4 py-3 text-right font-mono text-cyan-300">{fmtUsd(r.avg_max)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* remote */}
        <section>
          <h2 className="text-xl font-semibold tracking-tight mb-4">Remote vs on-site</h2>
          <div className="glass rounded-xl overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-widest text-zinc-500 border-b border-white/5">
                  <th className="px-4 py-3">Mode</th>
                  <th className="px-4 py-3 text-right">Roles</th>
                  <th className="px-4 py-3 text-right">Avg min</th>
                  <th className="px-4 py-3 text-right">Avg max</th>
                </tr>
              </thead>
              <tbody>
                {snap.byRemote.map((r) => (
                  <tr key={r.kind} className="border-b border-white/5">
                    <td className="px-4 py-3 capitalize text-zinc-100">{r.kind}</td>
                    <td className="px-4 py-3 text-right font-mono text-zinc-400">{r.job_count}</td>
                    <td className="px-4 py-3 text-right font-mono text-zinc-200">{fmtUsd(r.avg_min)}</td>
                    <td className="px-4 py-3 text-right font-mono text-cyan-300">{fmtUsd(r.avg_max)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <p className="mt-12 text-xs text-zinc-600 font-mono">last updated · {new Date(snap.updatedAt).toUTCString()}</p>
    </div>
  );
}

function Kpi({ label, value, prefix = '', suffix = '' }: { label: string; value: number; prefix?: string; suffix?: string }) {
  return (
    <Tilt>
      <div className="glass rounded-xl p-5">
        <div className="text-xs uppercase tracking-widest text-zinc-500">{label}</div>
        <div className="mt-1 font-mono text-3xl text-zinc-50">
          {prefix}{value.toLocaleString()}{suffix}
        </div>
      </div>
    </Tilt>
  );
}
