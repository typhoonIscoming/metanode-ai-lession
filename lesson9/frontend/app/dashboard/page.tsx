"use client";

import Link from "next/link";
import { Activity, Radio, TrendingUp, Zap } from "lucide-react";
import { useMarkets } from "@/hooks/use-markets";
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

function fmtTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
}

export default function DashboardPage() {
  const marketsQ = useMarkets({ limit: 50 });
  const signalsQ = useSignals({ limit: 20 });

  const markets = marketsQ.data?.items ?? [];
  const signals = signalsQ.data?.items ?? [];

  const activeMarkets = markets.filter((m) => m.state !== "EXPIRED");
  const enteredCount = markets.filter(
    (m) => m.state === "ENTERED_LONG" || m.state === "ENTERED_SHORT",
  ).length;
  const pushed24h = signals.filter(
    (s) => Date.now() - new Date(s.occurred_at).getTime() < 24 * 3600 * 1000,
  );

  return (
    <main className="mx-auto max-w-7xl space-y-8 px-6 py-8">
      {/* Hero */}
      <section className="animate-fade-up relative overflow-hidden rounded-2xl border border-orange-500/20 bg-gradient-to-br from-orange-500/10 via-slate-900/40 to-slate-950/60 p-8 backdrop-blur">
        <div className="absolute -top-12 -right-12 h-48 w-48 rounded-full bg-orange-500/20 blur-3xl" />
        <div className="relative flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold tracking-widest text-orange-400/80 uppercase">
              Live Arb Terminal
            </p>
            <h1 className="mt-2 text-4xl font-bold tracking-tight text-slate-50">
              Polymarket × BTC 套利信号
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              量化（对数正态）+ LLM 实时调整 → 与市场中价比对 → 飞书推送
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-300">
            <span className="relative flex h-2 w-2">
              <span className="absolute h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
              <span className="relative h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            实时 · 30 秒自动刷新
          </div>
        </div>
      </section>

      {/* KPI 4 卡 */}
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi
          icon={<Radio className="h-4 w-4" />}
          label="总监控市场"
          value={marketsQ.data?.total ?? 0}
          sub="含已过期"
          tone="primary"
          delay={0}
        />
        <Kpi
          icon={<Activity className="h-4 w-4" />}
          label="活跃市场"
          value={activeMarkets.length}
          sub="WATCHING / ENTERED_*"
          tone="green"
          delay={50}
        />
        <Kpi
          icon={<Zap className="h-4 w-4" />}
          label="入场中"
          value={enteredCount}
          sub="LONG / SHORT 持仓信号"
          tone="orange"
          delay={100}
        />
        <Kpi
          icon={<TrendingUp className="h-4 w-4" />}
          label="24h 推送"
          value={pushed24h.length}
          sub="过去 24 小时"
          tone="red"
          delay={150}
        />
      </section>

      {/* 信号列表 */}
      <section
        className="animate-fade-up glass-card rounded-2xl p-6"
        style={{ animationDelay: "200ms" }}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-100">最近信号</h2>
          <Link href="/history" className="text-xs text-orange-400 hover:text-orange-300">
            查看全部 →
          </Link>
        </div>
        {signals.length === 0 ? (
          <p className="py-8 text-center text-sm text-slate-500">
            暂无信号。等下一轮 signal_notify job（每 5 分钟），或点右侧「立即触发」。
          </p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-800/60">
            <table className="w-full text-sm">
              <thead className="bg-slate-900/50 text-xs tracking-wider text-slate-500 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">类型</th>
                  <th className="px-4 py-3 text-left font-semibold">市场</th>
                  <th className="px-4 py-3 text-right font-semibold">P(AI)</th>
                  <th className="px-4 py-3 text-right font-semibold">市场价</th>
                  <th className="px-4 py-3 text-right font-semibold">Gap</th>
                  <th className="px-4 py-3 text-left font-semibold">跃迁</th>
                  <th className="px-4 py-3 text-left font-semibold">飞书</th>
                  <th className="px-4 py-3 text-left font-semibold">时间</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {signals.map((s) => {
                  const gap = num(s.gap);
                  const meta = KIND_META[s.kind] ?? { label: s.kind, class: "state-watching" };
                  return (
                    <tr key={s.id} className="row-lift">
                      <td className="px-4 py-3">
                        <span
                          className={cn(
                            "inline-block rounded-md px-2.5 py-1 text-xs font-semibold",
                            meta.class,
                          )}
                        >
                          {meta.label}
                        </span>
                      </td>
                      <td className="max-w-xs px-4 py-3">
                        <Link
                          href={`/markets/${s.market.id}`}
                          className="block truncate text-sm text-slate-100 hover:text-orange-300"
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
                      <td className="px-4 py-3 text-xs text-slate-500">
                        {s.from_state.replace("ENTERED_", "")} →{" "}
                        {s.to_state.replace("ENTERED_", "")}
                      </td>
                      <td className="px-4 py-3">
                        {s.feishu_pushed ? (
                          <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                            已推
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 text-xs text-rose-400">
                            <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                            未推
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500" title={s.occurred_at}>
                        {fmtTime(s.occurred_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* 监控中的市场（单栏） */}
      <section
        className="animate-fade-up glass-card rounded-2xl p-6"
        style={{ animationDelay: "250ms" }}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-100">监控中的市场</h2>
          <Link href="/predict" className="text-xs text-orange-400 hover:text-orange-300">
            手动加入 →
          </Link>
        </div>
        {markets.length === 0 ? (
          <p className="py-8 text-center text-sm text-slate-500">
            尚无市场。每日 00:30 UTC 自动 discover，或去{" "}
            <Link href="/predict" className="text-orange-400">
              手动预测
            </Link>{" "}
            添加。
          </p>
        ) : (
          <ul className="space-y-2">
            {markets.slice(0, 12).map((m) => (
              <li key={m.id}>
                <Link
                  href={`/markets/${m.id}`}
                  className="row-lift flex items-center justify-between gap-3 rounded-lg border border-slate-800/40 bg-slate-900/30 px-4 py-3"
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm text-slate-100">{m.question}</div>
                    <div className="mt-1 flex items-center gap-3 text-xs text-slate-500">
                      <span>结算 {new Date(m.resolve_at).toLocaleDateString("zh-CN")}</span>
                      {m.latest_prediction && (
                        <span>
                          P(AI){" "}
                          <span className="text-emerald-400">
                            {(num(m.latest_prediction.p_ai) * 100).toFixed(1)}%
                          </span>
                        </span>
                      )}
                      {m.latest_price && (
                        <span>
                          P(市场){" "}
                          <span className="text-orange-400">
                            {(num(m.latest_price.p_yes) * 100).toFixed(1)}%
                          </span>
                        </span>
                      )}
                    </div>
                  </div>
                  <span
                    className={cn(
                      "shrink-0 rounded-md px-2.5 py-1 text-xs font-semibold",
                      STATE_CLASS[m.state] ?? "state-watching",
                    )}
                  >
                    {m.state.replace("ENTERED_", "")}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}

function Kpi({
  icon,
  label,
  value,
  sub,
  tone,
  delay,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  sub: string;
  tone: "primary" | "green" | "orange" | "red";
  delay: number;
}) {
  const toneClass = {
    primary: "text-slate-100",
    green: "text-emerald-400",
    orange: "text-orange-400",
    red: "text-rose-400",
  }[tone];
  const glowClass = {
    primary: "",
    green: "hover:shadow-[0_0_30px_hsl(160_80%_45%/0.15)]",
    orange: "hover:shadow-[0_0_30px_hsl(24_95%_53%/0.15)]",
    red: "hover:shadow-[0_0_30px_hsl(0_75%_60%/0.15)]",
  }[tone];
  return (
    <div
      className={cn(
        "animate-fade-up glass-card rounded-2xl p-5 transition-all duration-300 hover:-translate-y-0.5",
        glowClass,
      )}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center gap-2 text-xs font-medium tracking-wider text-slate-500 uppercase">
        <span className={toneClass}>{icon}</span>
        {label}
      </div>
      <div className={cn("mt-3 font-mono text-4xl font-bold tabular-nums", toneClass)}>{value}</div>
      <div className="mt-1 text-xs text-slate-600">{sub}</div>
    </div>
  );
}
