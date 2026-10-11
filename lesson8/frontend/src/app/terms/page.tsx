export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 pt-20 pb-20">
      <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/terms</div>
      <h1 className="text-4xl font-semibold tracking-tight">Terms of service</h1>
      <p className="mt-6 text-zinc-500 text-sm">This v0 reference deployment has no production terms. By using it you agree it is provided as-is for educational and demonstration purposes, with no warranty.</p>
      <div className="mt-10 prose prose-invert text-zinc-300 leading-relaxed space-y-3">
        <p><strong>Acceptable use.</strong> Do not scrape at scale, do not impersonate companies, do not post illegal or discriminatory roles.</p>
        <p><strong>Content.</strong> You retain rights to anything you post. You grant us a license to display it on the site.</p>
        <p><strong>Liability.</strong> No warranties, express or implied, for this educational build.</p>
      </div>
    </div>
  );
}
