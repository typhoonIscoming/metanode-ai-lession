import Link from 'next/link';

const ENDPOINTS: Array<{ method: string; path: string; note: string }> = [
  { method: 'GET',  path: '/v1/jobs',                note: 'Paginated job list. Filter: tag, remote, salary_min, company, q, sort, page, limit.' },
  { method: 'GET',  path: '/v1/jobs/:slug',          note: 'Single job with company and tags.' },
  { method: 'GET',  path: '/v1/companies',           note: 'Companies list with open-roles count.' },
  { method: 'GET',  path: '/v1/companies/:slug',     note: 'Company detail + recent live jobs.' },
  { method: 'GET',  path: '/v1/tags?popular=true',   note: 'Tags sorted by live-job count.' },
  { method: 'GET',  path: '/v1/salaries',            note: 'Aggregated salary snapshot.' },
  { method: 'GET',  path: '/v1/articles',            note: 'Learn-center articles, books, courses, etc.' },
  { method: 'POST', path: '/v1/auth/login',          note: 'Email + password → tokens.' },
  { method: 'POST', path: '/v1/auth/register',       note: 'Create candidate or employer account.' },
];

export default function ApiPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 pt-20 pb-20">
      <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/api</div>
      <h1 className="text-4xl md:text-5xl font-semibold tracking-tight">The <span className="holo-text">web3.career</span> API</h1>
      <p className="mt-3 text-zinc-400 max-w-2xl">All public endpoints. Authenticated endpoints require an <code className="font-mono text-cyan-300">Authorization: Bearer &lt;token&gt;</code> header from <code className="font-mono">/v1/auth/login</code>.</p>

      <div className="mt-8 glass rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-widest text-zinc-500 border-b border-white/5">
              <th className="px-4 py-3 w-20">Method</th>
              <th className="px-4 py-3">Path</th>
              <th className="px-4 py-3">Notes</th>
            </tr>
          </thead>
          <tbody>
            {ENDPOINTS.map((e) => (
              <tr key={e.path + e.method} className="border-b border-white/5">
                <td className="px-4 py-3 font-mono text-xs">
                  <span className={e.method === 'GET' ? 'text-cyan-300' : 'text-lime-400'}>{e.method}</span>
                </td>
                <td className="px-4 py-3 font-mono text-zinc-200">{e.path}</td>
                <td className="px-4 py-3 text-zinc-400">{e.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-10">
        <h2 className="text-xl font-semibold tracking-tight mb-3">Quick start</h2>
        <pre className="glass rounded-xl p-5 font-mono text-xs text-cyan-100 overflow-x-auto">
{`# list 5 latest jobs
curl http://localhost:4000/v1/jobs?limit=5

# login
curl -X POST http://localhost:4000/v1/auth/login \\
  -H 'content-type: application/json' \\
  -d '{"email":"demo-candidate@web3career.local","password":"password1"}'

# (employer) post a job — replace TOKEN
curl -X POST http://localhost:4000/v1/jobs \\
  -H 'content-type: application/json' \\
  -H 'authorization: Bearer TOKEN' \\
  -d '{"title":"...","description":"...","isRemote":true,"applyType":"external","tags":["solidity"]}'`}
        </pre>
      </div>

      <p className="mt-10 text-xs text-zinc-600">
        See full docs at <Link href="/" className="underline">PRDs</Link> in the repo (backend-PRD.md §5).
      </p>
    </div>
  );
}
