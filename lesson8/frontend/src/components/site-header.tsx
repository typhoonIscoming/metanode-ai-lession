import Link from 'next/link';
import { AuthMenu } from './auth-menu';

const NAV: Array<{ label: string; href: string }> = [
  { label: 'Jobs',       href: '/jobs' },
  { label: 'Companies',  href: '/companies' },
  { label: 'Salaries',   href: '/salaries' },
  { label: 'Learn',      href: '/learn' },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/5 backdrop-blur-xl bg-[rgba(5,7,13,0.7)]">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="relative h-7 w-7 grid place-items-center rounded-md border border-white/10 bg-gradient-to-br from-cyan-500/30 to-violet-500/30">
            <span className="font-mono text-[12px] text-cyan-300 group-hover:text-cyan-200 transition-colors">W3</span>
            <span className="absolute inset-0 rounded-md ring-1 ring-cyan-400/0 group-hover:ring-cyan-400/40 transition" />
          </div>
          <span className="font-semibold tracking-tight text-[15px]">
            web3<span className="text-cyan-300">.</span>career
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-6 text-sm text-zinc-300">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className="relative hover:text-white transition-colors after:absolute after:-bottom-1.5 after:left-0 after:h-px after:w-0 after:bg-cyan-400 hover:after:w-full after:transition-all"
            >
              {n.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <AuthMenu />
          <Link
            href="/post-a-job"
            className="btn-glow rounded-md px-4 py-1.5 text-sm font-medium"
          >
            Post a Job
          </Link>
        </div>
      </div>
    </header>
  );
}
