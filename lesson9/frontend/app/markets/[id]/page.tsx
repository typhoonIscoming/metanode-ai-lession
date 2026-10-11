"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowLeft, ExternalLink } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useMarket, usePredictions, usePriceTicks } from "@/hooks/use-markets";
import { useSignals } from "@/hooks/use-signals";
import { cn } from "@/lib/utils";

const STATE_CLASS: Record<string, string> = {
  WATCHING: "state-watching",
  ENTERED_LONG: "state-long",
  ENTERED_SHORT: "state-short",
  EXPIRED: "state-expired",
};

const KIND_META: Record<string, { label: string; class: string }> = {
  ENTRY_LONG: { label: "做多入场", class: "state-long" },
  ENTRY_SHORT: { label: "做空入场", class: "state-short" },
  EXIT_LONG: { label: "退出多头", class: "state-expired" },
  EXIT_SHORT: { label: "退出空头", class: "state-expired" },
  EXPIRED: { label: "已结算", class: "state-expired" },
};

function num(s: string | null | undefined): number {
  if (!s) return 0;
  const v = Number(s);
  return Number.isFinite(v) ? v : 0;
}
function fmtUtc(iso: string): string {
  return new Date(iso).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" });
}

export default function MarketDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const marketId = Number(id);
  const marketQ = useMarket(marketId);
  const predictionsQ = usePredictions(marketId);
  const ticksQ = usePriceTicks(marketId);
  const signalsQ = useSignals({ market_id: marketId, limit: 50 });

  const m = marketQ.data;
  const predictions = predictionsQ.data?.items ?? [];
  const ticks = ticksQ.data?.items ?? [];
  const signals = signalsQ.data?.items ?? [];

  if (marketQ.isLoading) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-12">
        <p className="text-slate-500">加载中…</p>
      </main>
    );
  }
  if (marketQ.isError || !m) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-12">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-orange-400 hover:text-orange-300"
        >
          <ArrowLeft className="h-4 w-4" /> 返回仪表盘
        </Link>
        <h1 className="mt-4 text-2xl font-bold text-slate-100">市场未找到</h1>
        <p className="mt-2 text-sm text-rose-400">{String(marketQ.error)}</p>
      </main>
    );
  }

  // chart data: merge ticks + predictions on time axis
  const chartData = [...ticks].reverse().map((t) => ({
    time: new Date(t.fetched_at).getTime(),
    p_mkt: num(t.p_yes) * 100,
  }));
  const predPoints = [...predictions].reverse().map((p) => ({
    time: new Date(p.created_at).getTime(),
    p_ai: num(p.p_ai) * 100,
  }));
  const merged = new Map<number, { time: number; p_mkt?: number; p_ai?: number }>();
  for (const p of [...chartData, ...predPoints]) {
    const existing = merged.get(p.time) ?? { time: p.time };
    Object.assign(existing, p);
    merged.set(p.time, existing);
  }
  const chartSeries = Array.from(merged.values()).sort((a, b) => a.time - b.time);
  const latestPred = predictions[0];

  // 真实 Polymarket URL
  const eventSlug = (m.metadata as { event_slug?: string } | undefined)?.event_slug;
  const polymarketUrl = eventSlug
    ? `https://polymarket.com/event/${eventSlug}`
    : m.slug
      ? `https://polymarket.com/market/${m.slug}`
      : null;

  return (
    <main className="mx-auto max-w-7xl space-y-6 px-6 py-8">
      {/* Header */}
      <header className="animate-fade-up">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-orange-400 hover:text-orange-300"
        >
          <ArrowLeft className="h-4 w-4" /> 仪表盘
        </Link>
        <div className="mt-3 flex flex-wrap items-start justify-between gap-3">
          <div className="flex-1">
            <h1 className="text-3xl font-bold tracking-tight text-slate-50">{m.question}</h1>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-slate-400">
              <span
                className={cn(
                  "rounded-md px-2.5 py-1 text-xs font-semibold",
                  STATE_CLASS[m.state] ?? "state-watching",
                )}
              >
                {m.state}
              </span>
              <span className="text-xs text-slate-500">
                {m.source === "discovery" ? "🤖 自动发现" : "✋ 手动添加"}
              </span>
              <span className="text-xs text-slate-500">结算 {fmtUtc(m.resolve_at)}</span>
              {polymarketUrl && (
                <a
                  href={polymarketUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 rounded-md border border-orange-500/40 bg-orange-500/10 px-2.5 py-1 text-xs text-orange-300 hover:bg-orange-500/20"
                >
                  在 Polymarket 打开 <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
            {m.description && (
              <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-500">
                {m.description}
              </p>
            )}
          </div>
        </div>
      </header>

      {/* KPI */}
      <section
        className="animate-fade-up grid grid-cols-2 gap-4 md:grid-cols-4"
        style={{ animationDelay: "50ms" }}
      >
        <KpiBox
          label="Strike"
          value={m.strike_price ? `$${Number(m.strike_price).toLocaleString()}` : "—"}
          tone="slate"
        />
        <KpiBox label="方向" value={m.direction ?? "—"} tone="slate" />
        <KpiBox
          label="最新 P(AI)"
          value={m.latest_prediction ? `${(num(m.latest_prediction.p_ai) * 100).toFixed(2)}%` : "—"}
          tone="green"
        />
        <KpiBox
          label="最新 P(市场)"
          value={m.latest_price ? `${(num(m.latest_price.p_yes) * 100).toFixed(2)}%` : "—"}
          tone="orange"
        />
      </section>

      {/* Chart */}
      <section
        className="animate-fade-up glass-card rounded-2xl p-6"
        style={{ animationDelay: "100ms" }}
      >
        <h2 className="mb-4 text-lg font-semibold text-slate-100">价格走势 · AI 概率 vs 市场价</h2>
        {chartSeries.length === 0 ? (
          <p className="py-12 text-center text-sm text-slate-500">
            暂无数据。等下一次 price_poll job（5 分钟）。
          </p>
        ) : (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartSeries} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(222 25% 18%)" />
                <XAxis
                  dataKey="time"
                  stroke="hsl(215 15% 45%)"
                  fontSize={11}
                  tickFormatter={(t) =>
                    new Date(t).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
                  }
                />
                <YAxis
                  stroke="hsl(215 15% 45%)"
                  fontSize={11}
                  domain={[0, 100]}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(222 32% 10%)",
                    border: "1px solid hsl(222 25% 22%)",
                    borderRadius: "8px",
                    color: "hsl(210 40% 96%)",
                  }}
                  labelStyle={{ color: "hsl(215 15% 60%)" }}
                  labelFormatter={(t) => fmtUtc(new Date(t as number).toISOString())}
                  formatter={(v: number) => `${v.toFixed(2)}%`}
                />
                <ReferenceLine y={50} stroke="hsl(215 15% 35%)" strokeDasharray="3 3" />
                <Line
                  type="monotone"
                  dataKey="p_mkt"
                  name="市场价"
                  stroke="hsl(24 95% 53%)"
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="p_ai"
                  name="AI 概率"
                  stroke="hsl(160 80% 45%)"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      {/* Latest prediction */}
      {latestPred && (
        <section
          className="animate-fade-up glass-card rounded-2xl p-6"
          style={{ animationDelay: "150ms" }}
        >
          <h2 className="mb-4 text-lg font-semibold text-slate-100">最新预测</h2>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <KpiBox
              label="P(AI)"
              value={`${(num(latestPred.p_ai) * 100).toFixed(2)}%`}
              tone="green"
              big
            />
            <KpiBox
              label="P(量化)"
              value={`${(num(latestPred.p_quant) * 100).toFixed(2)}%`}
              tone="slate"
              big
            />
            <KpiBox
              label="LLM 调整"
              value={`${num(latestPred.llm_adjustment) >= 0 ? "+" : ""}${(num(latestPred.llm_adjustment) * 100).toFixed(2)}%`}
              tone="orange"
              big
            />
            <KpiBox label="LLM 置信度" value={latestPred.llm_confidence ?? "—"} tone="slate" big />
          </div>
          {latestPred.llm_rationale && (
            <div className="mt-4 rounded-xl border border-slate-800/60 bg-slate-950/40 p-4">
              <div className="mb-2 text-xs font-semibold tracking-wider text-orange-400/80 uppercase">
                LLM 解释
              </div>
              <pre className="font-sans text-sm whitespace-pre-wrap text-slate-300">
                {latestPred.llm_rationale}
              </pre>
            </div>
          )}
          <div className="mt-4 flex flex-wrap gap-x-3 gap-y-1 border-t border-slate-800/60 pt-3 text-xs text-slate-500">
            <span>
              model <span className="font-mono text-orange-400">{latestPred.model_version}</span>
            </span>
            <span>·</span>
            <span>
              spot{" "}
              <span className="font-mono text-slate-300">
                ${Number(latestPred.spot_price ?? "0").toLocaleString()}
              </span>
            </span>
            <span>·</span>
            <span>
              30d 波动{" "}
              <span className="font-mono text-slate-300">
                {(num(latestPred.realized_vol) * 100).toFixed(2)}%
              </span>
            </span>
            <span>·</span>
            <span>{fmtUtc(latestPred.created_at)}</span>
          </div>
        </section>
      )}

      {/* Signals */}
      <section
        className="animate-fade-up glass-card rounded-2xl p-6"
        style={{ animationDelay: "200ms" }}
      >
        <h2 className="mb-4 text-lg font-semibold text-slate-100">本市场的信号事件</h2>
        {signals.length === 0 ? (
          <p className="py-8 text-center text-sm text-slate-500">本市场尚未触发过信号</p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-800/60">
            <table className="w-full text-sm">
              <thead className="bg-slate-900/50 text-xs tracking-wider text-slate-500 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">类型</th>
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
                  const meta = KIND_META[s.kind];
                  return (
                    <tr key={s.id} className="row-lift">
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
                          <span className="text-xs text-rose-400">未推</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500">{fmtUtc(s.occurred_at)}</td>
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

function KpiBox({
  label,
  value,
  tone,
  big,
}: {
  label: string;
  value: string;
  tone: "green" | "orange" | "slate";
  big?: boolean;
}) {
  const cls = { green: "text-emerald-400", orange: "text-orange-400", slate: "text-slate-100" }[
    tone
  ];
  return (
    <div className="rounded-xl border border-slate-800/60 bg-slate-950/40 p-4">
      <div className="text-xs tracking-wider text-slate-500 uppercase">{label}</div>
      <div
        className={cn("mt-2 font-mono font-bold tabular-nums", cls, big ? "text-2xl" : "text-xl")}
      >
        {value}
      </div>
    </div>
  );
}
