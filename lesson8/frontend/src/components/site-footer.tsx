import Link from 'next/link';

const COLS: Array<{ title: string; items: Array<{ label: string; href: string }> }> = [
  {
    title: 'Product',
    items: [
      { label: 'Jobs',          href: '/jobs' },
      { label: 'Companies',     href: '/companies' },
      { label: 'Salaries',      href: '/salaries' },
      { label: 'Top Companies', href: '/companies' },
    ],
  },
  {
    title: 'Employers',
    items: [
      { label: 'Post a Job',    href: '/post-a-job' },
      { label: 'Bundle',        href: '/post-a-job/bundle' },
      { label: 'Advertise',     href: '/advertise' },
      { label: 'API',           href: '/api' },
    ],
  },
  {
    title: 'Learn',
    items: [
      { label: 'Articles',      href: '/learn' },
      { label: 'Books',         href: '/learn' },
      { label: 'Bootcamps',     href: '/learn' },
      { label: 'Glossary',      href: '/learn' },
    ],
  },
  {
    title: 'Company',
    items: [
      { label: 'About',         href: '/about' },
      { label: 'FAQ',           href: '/faq' },
      { label: 'Terms',         href: '/terms' },
      { label: 'Privacy',       href: '/privacy' },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="relative mt-32 border-t border-white/5 bg-black/50">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-500/40 to-transparent" />
      <div className="mx-auto max-w-7xl px-6 py-14 grid grid-cols-2 md:grid-cols-5 gap-10 text-sm">
        <div className="col-span-2">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-7 w-7 grid place-items-center rounded-md border border-white/10 bg-gradient-to-br from-cyan-500/30 to-violet-500/30">
              <span className="font-mono text-[12px] text-cyan-300">W3</span>
            </div>
            <span className="font-semibold">web3<span className="text-cyan-300">.</span>career</span>
          </div>
          <p className="text-zinc-400 max-w-sm">
            The on-chain job board. Discover roles at the most-funded Web3 protocols, audits, L2s, and on-chain games.
          </p>
        </div>
        {COLS.map((col) => (
          <div key={col.title}>
            <h4 className="text-zinc-300 font-medium mb-3">{col.title}</h4>
            <ul className="space-y-2">
              {col.items.map((it) => (
                <li key={it.label}>
                  <Link href={it.href} className="text-zinc-500 hover:text-cyan-300 transition-colors">
                    {it.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-white/5">
        <div className="mx-auto max-w-7xl px-6 py-5 flex flex-col md:flex-row items-center justify-between gap-3 text-xs text-zinc-500">
          <span>© 2026 web3.career — open-source v0 clone (educational).</span>
          <span className="font-mono inline-flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-lime-400 animate-pulse" />
            block · online
          </span>
        </div>
      </div>
    </footer>
  );
}
