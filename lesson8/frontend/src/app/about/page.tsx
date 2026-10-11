export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 pt-20 pb-20">
      <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/about</div>
      <h1 className="text-4xl font-semibold tracking-tight">About <span className="holo-text">web3.career</span></h1>
      <div className="mt-6 space-y-4 text-zinc-300 leading-relaxed">
        <p>web3.career is an on-chain job board built to help engineers, designers and operators find roles at the most-funded Web3 projects.</p>
        <p>We index roles from project ATSs, Twitter, and public RSS feeds. Hand-curated, lightly opinionated, fully open.</p>
        <p>This deployment is the open-source v0 reference implementation built from the PRDs in this repo.</p>
      </div>
    </div>
  );
}
