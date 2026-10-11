const ITEMS: Array<{ q: string; a: string }> = [
  { q: 'How is Web3 different from Web2 hiring?',
    a: 'Web3 roles often pay in part with tokens/equity, are global-remote by default, and ask for more public proof-of-work (GitHub, audits, EIPs).' },
  { q: 'Are these jobs legitimate?',
    a: 'Every employer on our platform is verified by domain age, public funding records, or hand-review by our team.' },
  { q: 'Do I need to know Solidity to get a Web3 job?',
    a: 'No. Roles span design, marketing, sales, ops, BD, community, security, devrel and more. About 35% of postings are non-engineering.' },
  { q: 'Where do most companies hire from?',
    a: 'Top 5 cities by job count: New York, San Francisco, London, Singapore, Lisbon. Remote dominates overall.' },
  { q: 'Is web3.career open-source?',
    a: 'This v0 reference build is. See the repo for the PRD-driven implementation.' },
];

export default function FaqPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 pt-20 pb-20">
      <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/faq</div>
      <h1 className="text-4xl font-semibold tracking-tight">Frequently asked</h1>
      <div className="mt-10 space-y-6">
        {ITEMS.map((i) => (
          <details key={i.q} className="glass rounded-xl p-5 group">
            <summary className="cursor-pointer list-none flex items-center justify-between gap-4">
              <span className="font-medium text-zinc-100">{i.q}</span>
              <span className="font-mono text-cyan-300 group-open:rotate-45 transition">+</span>
            </summary>
            <p className="mt-3 text-zinc-400 leading-relaxed">{i.a}</p>
          </details>
        ))}
      </div>
    </div>
  );
}
