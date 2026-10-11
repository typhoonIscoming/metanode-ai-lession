// 全站底部免责声明（PRD §3.3）
export function FooterDisclaimer() {
  return (
    <footer className="border-t border-slate-800/60 bg-slate-950/40 px-6 py-4 text-center text-xs text-slate-500 backdrop-blur">
      <span className="inline-flex items-center gap-2">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-orange-400/60" />
        本工具仅作个人研究信号提醒 · 不构成投资建议 · v0.1
      </span>
    </footer>
  );
}
