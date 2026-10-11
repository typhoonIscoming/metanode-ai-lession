"use client";

import { useState } from "react";
import Link from "next/link";
import { Download } from "lucide-react";
import { useSignals } from "@/hooks/use-signals";
import { Button } from "@/components/ui/button";
import { type SignalKind } from "@/lib/schemas";
import { cn } from "@/lib/utils";

const KIND_OPTIONS: { value: SignalKind | "all"; label: string; class: string }[] = [
  { value: "all", label: "全部", class: "state-watching" },
  { value: "ENTRY_LONG", label: "🟢 做多入场", class: "state-long" },
  { value: "ENTRY_SHORT", label: "🔴 做空入场", class: "state-short" },
  { value: "EXIT_LONG", label: "退出多头", class: "state-expired" },
  { value: "EXIT_SHORT", label: "退出空头", class: "state-expired" },
  { value: "EXPIRED", label: "已结算", class: "state-expired" },
];

function num(s: string | null | undefined): number {
  if (!s) return 0;
  const v = Number(s);
  return Number.isFinite(v) ? v : 0;
}

function exportCsv(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return "";
  const headers = Object.keys(rows[0]);
  const escape = (v: unknown) => {
    if (v === null || v === undefined) return "";
    const s = String(v);
    return s.includes(",") || s.includes('"') || s.includes("\n")
      ? `"${s.replace(/"/g, '""')}"`
      : s;
  };
  return [headers.join(","), ...rows.map((r) => headers.map((h) => escape(r[h])).join(","))].join(
    "\n",
  );
}

export default function HistoryPage() {
  const [kindFilter, setKindFilter] = useState<SignalKind | "all">("all");
  const [limit, setLimit] = useState(50);

  const signalsQ = useSignals({
    kind: kindFilter === "all" ? undefined : kindFilter,
    limit,
  });
  const signals = signalsQ.data?.items ?? [];
  const total = signalsQ.data?.total ?? 0;

  const handleExport = () => {
    const rows = signals.map((s) => ({
      id: s.id,
      occurred_at: s.occurred_at,
      kind: s.kind,
      market_id: s.market.id,
      question: s.market.question,
      from_state: s.from_state,
      to_state: s.to_state,
      p_ai: s.p_ai_at_event,
      p_mkt: s.p_mkt_at_event,
      gap: s.gap,
      feishu_pushed: s.feishu_pushed,
      feishu_push_at: s.feishu_push_at,
    }));
    const csv = exportCsv(rows);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `signals_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="mx-auto max-w-7xl space-y-6 px-6 py-8">
      <header className="animate-fade-up">
        <h1 className="text-3xl font-bold tracking-tight text-slate-50">推送历史</h1>
        <p className="mt-1 text-sm text-slate-400">
          所有信号事件 + 飞书推送状态 · 共{" "}
          <span className="font-mono text-orange-400">{total}</span> 条
        </p>
      </header>

      <section
        className="animate-fade-up glass-card rounded-2xl p-4"
        style={{ animationDelay: "50ms" }}
      >
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex flex-wrap gap-1.5">
            {KIND_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setKindFilter(opt.value)}
                className={cn(
                  "rounded-md border px-3 py-1.5 text-xs font-medium transition-all",
                  kindFilter === opt.value
                    ? "border-orange-500/50 bg-orange-500/15 text-orange-300"
                    : "border-slate-700 bg-slate-900/40 text-slate-400 hover:border-slate-600 hover:text-slate-200",
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <div className="ml-auto flex items-center gap-2 text-xs">
            <label className="flex items-center gap-2 text-slate-500">
              显示
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-slate-200 focus:border-orange-500/50 focus:outline-none"
              >
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={200}>200</option>
              </select>
              条
            </label>
            <Button
              onClick={handleExport}
              disabled={signals.length === 0}
              className="h-8 border border-slate-700 bg-slate-900/40 px-3 text-xs text-slate-300 hover:bg-slate-800"
            >
              <Download className="mr-1.5 h-3 w-3" />
              导出 CSV
            </Button>
          </div>
        </div>
      </section>

      <section
        className="animate-fade-up glass-card rounded-2xl p-6"
        style={{ animationDelay: "100ms" }}
      >
        {signalsQ.isLoading ? (
          <p className="py-12 text-center text-sm text-slate-500">加载中…</p>
        ) : signals.length === 0 ? (
          <p className="py-12 text-center text-sm text-slate-500">无符合筛选条件的信号</p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-800/60">
            <table className="w-full text-sm">
              <thead className="bg-slate-900/50 text-xs tracking-wider text-slate-500 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">ID</th>
                  <th className="px-4 py-3 text-left font-semibold">类型</th>
                  <th className="px-4 py-3 text-left font-semibold">市场</th>
                  <th className="px-4 py-3 text-right font-semibold">P(AI)</th>
                  <th className="px-4 py-3 text-right font-semibold">市场价</th>
                  <th className="px-4 py-3 text-right font-semibold">Gap</th>
                  <th className="px-4 py-3 text-left font-semibold">飞书</th>
                  <th className="px-4 py-3 text-left font-semibold">时间</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {signals.map((s) => {
                  const gap = num(s.gap);
                  const meta = KIND_OPTIONS.find((o) => o.value === s.kind);
                  return (
                    <tr key={s.id} className="row-lift">
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">#{s.id}</td>
                      <td className="px-4 py-3">
                        <span
                          className={cn(
                            "inline-block rounded-md px-2.5 py-1 text-xs font-semibold",
                            meta?.class ?? "state-watching",
                          )}
                        >
                          {meta?.label ?? s.kind}
                        </span>
                      </td>
                      <td className="max-w-xs px-4 py-3">
                        <Link
                          href={`/markets/${s.market.id}`}
                          className="block truncate text-slate-100 hover:text-orange-300"
                          title={s.market.question}
                        >
                          {s.market.question}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-slate-300">
                        {(num(s.p_ai_at_event) * 100).toFixed(2)}%
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-slate-300">
                        {(num(s.p_mkt_at_event) * 100).toFixed(2)}%
                      </td>
                      <td
                        className={cn(
                          "px-4 py-3 text-right font-mono text-base font-bold",
                          gap > 0 ? "text-emerald-400" : "text-rose-400",
                        )}
                      >
                        {gap > 0 ? "+" : ""}
                        {(gap * 100).toFixed(2)}%
                      </td>
                      <td className="px-4 py-3">
                        {s.feishu_pushed ? (
                          <span className="text-xs text-emerald-400">已推</span>
                        ) : (
                          <span
                            className="text-xs text-rose-400"
                            title={s.feishu_error ?? undefined}
                          >
                            未推
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500">
                        {new Date(s.occurred_at).toLocaleString("zh-CN", {
                          timeZone: "Asia/Shanghai",
                        })}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
