export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 pt-20 pb-20">
      <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/privacy</div>
      <h1 className="text-4xl font-semibold tracking-tight">Privacy</h1>
      <p className="mt-6 text-zinc-500 text-sm">Educational build. Treat data accordingly.</p>
      <div className="mt-10 prose prose-invert text-zinc-300 leading-relaxed space-y-3">
        <p><strong>What we store.</strong> Email, hashed password, role, optional display name. Cookies for session (when enabled), localStorage for v0.</p>
        <p><strong>What we never store.</strong> Plaintext passwords. We do not sell data.</p>
        <p><strong>Your rights.</strong> Email <span className="font-mono">privacy@example.com</span> to request deletion.</p>
      </div>
    </div>
  );
}
