"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Sparkles, Target } from "lucide-react";
import { usePredictDryRun } from "@/hooks/use-predict";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

function num(s: string | null | undefined): number {
  if (!s) return 0;
  const v = Number(s);
  return Number.isFinite(v) ? v : 0;
}

function fmtUtc(iso: string): string {
  return new Date(iso).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" });
}

// 示例：Polymarket 的「Bitcoin above ___ on {date}」event 一般会预先创建
// 未来 2-3 天，更远的日期可能 404。下面是当前已知可用的几个 event。
const EXAMPLES = [
  {
    label: "Bitcoin above ___ on May 21?",
    url: "https://polymarket.com/event/bitcoin-above-on-may-21",
  },
  {
    label: "Bitcoin above ___ on May 20?",
    url: "https://polymarket.com/event/bitcoin-above-on-may-20",
  },
  {
    label: "When will BTC hit 150k?",
    url: "https://polymarket.com/event/when-will-bitcoin-hit-150k",
  },
];

interface PersistInfo {
  market_id: number;
  market_created: boolean;
  prediction_id: number;
  tick_created: boolean;
  signal_stats?: Record<string, unknown>;
  push_stats?: Record<string, unknown>;
}

export default function PredictPage() {
  const [url, setUrl] = useState("");
  const mut = usePredictDryRun();
  const qc = useQueryClient();

  // 「加入监控」：persist=true，绕过 Zod 严格校验（response 多了 persist 字段）
  const persistMut = useMutation({
    mutationFn: async (polymarket_url: string) => {
      return await apiFetch<{
        market_preview: { question: string; chosen_from_event?: string | null };
        prediction: { p_ai: string; p_quant: string };
        persist: PersistInfo | null;
      }>("/predict", {
        method: "POST",
        body: JSON.stringify({ polymarket_url, persist: true }),
      });
    },
    onSuccess: (data) => {
      const p = data.persist;
      if (p) {
        const action = p.market_created ? "已新建并加入监控" : "已更新已有市场";
        const push = (p.push_stats?.pushed as number | undefined) ?? 0;
        const dry = (p.push_stats?.dry_run as number | undefined) ?? 0;
        toast.success(`${action}：${data.market_preview.question.slice(0, 40)}`, {
          description: `市场 #${p.market_id} · 飞书推送 pushed=${push}, dry_run=${dry}`,
          duration: 6000,
        });
      } else {
        toast.success("预测完成（未入库）");
      }
      qc.invalidateQueries({ queryKey: ["markets"] });
      qc.invalidateQueries({ queryKey: ["signals"] });
    },
    onError: (e) => toast.error(`加入监控失败：${e instanceof Error ? e.message : String(e)}`),
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      toast.error("请输入 Polymarket URL");
      return;
    }
    try {
      await mut.mutateAsync({ polymarket_url: url.trim() });
    } catch (e) {
      toast.error(`预测失败：${e instanceof Error ? e.message : String(e)}`);
    }
  };

  const handlePersist = async () => {
    if (!url.trim()) {
      toast.error("请输入 Polymarket URL");
      return;
    }
    persistMut.mutate(url.trim());
  };

  const data = mut.data;
  const isLLMOk = data?.prediction.llm_confidence != null;

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-6 py-8">
      <header className="animate-fade-up">
        <div className="inline-flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-3 py-1 text-xs font-semibold text-orange-300">
          <Sparkles className="h-3 w-3" />
          两种模式：试一次（dry-run）/ 加入监控（入库 + 推飞书）
        </div>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-50">手动预测</h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-400">
          贴一个 Polymarket BTC 二元市场或 event 集合 URL → 量化 + LLM 预测。Event 集合自动选市场价
          最接近 50% 的子市场。「加入监控」会把市场写入 dashboard 并立即跑信号引擎 + 飞书推送。
        </p>
      </header>

      <section
        className="animate-fade-up glass-card rounded-2xl p-6"
        style={{ animationDelay: "50ms" }}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label
              htmlFor="url"
              className="text-xs font-semibold tracking-wider text-slate-400 uppercase"
            >
              Polymarket URL
            </Label>
            <Input
              id="url"
              type="url"
              className="mt-2 h-11 border-slate-700 bg-slate-950/60 font-mono text-sm text-slate-100 placeholder:text-slate-600 focus-visible:ring-orange-500/30"
              placeholder="https://polymarket.com/event/..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <p className="mt-1.5 text-xs text-slate-500">
              支持{" "}
              <code className="rounded bg-slate-800 px-1.5 py-0.5 text-orange-300">
                /event/&lt;slug&gt;
              </code>{" "}
              或{" "}
              <code className="rounded bg-slate-800 px-1.5 py-0.5 text-orange-300">
                /market/&lt;slug&gt;
              </code>
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button
              type="submit"
              disabled={mut.isPending || persistMut.isPending}
              className="h-11 bg-gradient-to-r from-orange-500 to-amber-500 px-6 font-semibold text-white shadow-lg shadow-orange-500/30 hover:from-orange-400 hover:to-amber-400 disabled:opacity-50"
            >
              {mut.isPending ? "预测中（拉市场 + 量化 + LLM）…" : "🚀 试一次（dry-run）"}
            </Button>
            <Button
              type="button"
              onClick={handlePersist}
              disabled={mut.isPending || persistMut.isPending}
              className="h-11 border border-emerald-500/40 bg-emerald-500/15 px-5 font-semibold text-emerald-300 hover:border-emerald-500/60 hover:bg-emerald-500/25 hover:text-emerald-200 disabled:opacity-50"
            >
              {persistMut.isPending ? "入库 + 推送中…" : "📥 加入监控并推送"}
            </Button>
            {!url.trim() && (
              <span className="text-xs text-amber-400/80">↑ 先填 Polymarket URL（或点示例）</span>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-500">示例：</span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex.url}
                type="button"
                className="rounded-md border border-slate-700 bg-slate-800/40 px-2.5 py-1 text-slate-400 hover:border-orange-500/50 hover:bg-orange-500/10 hover:text-orange-300"
                onClick={() => setUrl(ex.url)}
              >
                {ex.label}
              </button>
            ))}
          </div>
        </form>
      </section>

      {mut.isError && (
        <section className="animate-fade-up rounded-2xl border border-rose-500/40 bg-rose-500/10 p-4">
          <div className="text-sm font-semibold text-rose-300">预测失败</div>
          <div className="mt-1 text-sm text-rose-400/80">
            {mut.error instanceof Error ? mut.error.message : String(mut.error)}
          </div>
        </section>
      )}

      {persistMut.isSuccess && persistMut.data?.persist && (
        <section className="animate-fade-up rounded-2xl border border-emerald-500/40 bg-emerald-500/10 p-4">
          <div className="text-sm font-semibold text-emerald-300">
            ✅ 已加入监控 · 市场 #{persistMut.data.persist.market_id}
          </div>
          <div className="mt-1 text-sm text-emerald-200/80">
            {persistMut.data.persist.market_created ? "新建市场" : "已有市场（更新预测）"}
            {persistMut.data.persist.signal_stats &&
              `, 信号引擎跃迁 ${persistMut.data.persist.signal_stats.transitioned ?? 0} 次`}
            {persistMut.data.persist.push_stats &&
              `, 飞书推送 ${persistMut.data.persist.push_stats.pushed ?? 0}, dry-run ${persistMut.data.persist.push_stats.dry_run ?? 0}`}
            。
          </div>
          <Link
            href={`/markets/${persistMut.data.persist.market_id}`}
            className="mt-2 inline-flex text-xs text-emerald-300 hover:text-emerald-100"
          >
            打开市场详情 →
          </Link>
        </section>
      )}

      {data && (
        <>
          <section className="animate-fade-up glass-card rounded-2xl p-6">
            {data.market_preview.chosen_from_event && (
              <div className="mb-4 flex items-start gap-3 rounded-xl border border-blue-500/30 bg-blue-500/10 p-4 text-sm">
                <Target className="h-5 w-5 shrink-0 text-blue-400" />
                <div>
                  <div className="font-semibold text-blue-300">
                    Event 集合：{data.market_preview.chosen_from_event}
                  </div>
                  <div className="mt-1 text-blue-200/80">
                    共 {data.market_preview.event_sub_count} 个子市场， 自动选了{" "}
                    <strong className="text-blue-100">市场价最接近 50%</strong> 的那一个
                    {data.market_preview.chosen_midpoint && (
                      <span className="ml-1 rounded bg-blue-500/20 px-1.5 py-0.5 font-mono text-xs">
                        YES {(num(data.market_preview.chosen_midpoint) * 100).toFixed(2)}%
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}
            <h2 className="text-xl font-semibold text-slate-100">{data.market_preview.question}</h2>
            <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-3">
              <Stat
                label="Strike"
                value={
                  data.market_preview.strike_price
                    ? `$${Number(data.market_preview.strike_price).toLocaleString()}`
                    : "—"
                }
              />
              <Stat label="方向" value={data.market_preview.direction ?? "—"} />
              <Stat label="结算时间" value={fmtUtc(data.market_preview.resolve_at)} small />
            </div>
          </section>

          <section className="animate-fade-up glass-card rounded-2xl p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-100">预测结果</h2>
              {isLLMOk ? (
                <span className="rounded-full border border-orange-500/40 bg-orange-500/15 px-3 py-1 text-xs font-semibold text-orange-300">
                  ✨ 含 LLM 调整
                </span>
              ) : (
                <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-500">
                  纯量化
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <BigNum
                label="P(AI) 综合"
                value={(num(data.prediction.p_ai) * 100).toFixed(2) + "%"}
                tone="green"
                big
              />
              <BigNum
                label="P(量化)"
                value={(num(data.prediction.p_quant) * 100).toFixed(2) + "%"}
                tone="slate"
              />
              <BigNum
                label="LLM 调整"
                value={
                  (num(data.prediction.llm_adjustment) >= 0 ? "+" : "") +
                  (num(data.prediction.llm_adjustment) * 100).toFixed(2) +
                  "%"
                }
                tone="orange"
              />
              <BigNum
                label="LLM 置信度"
                value={data.prediction.llm_confidence ?? "—"}
                tone="slate"
              />
            </div>

            {data.prediction.llm_rationale && (
              <div className="mt-5 rounded-xl border border-slate-800/60 bg-slate-950/40 p-4">
                <div className="mb-2 text-xs font-semibold tracking-wider text-orange-400/80 uppercase">
                  LLM 解释
                </div>
                <pre className="font-sans text-sm whitespace-pre-wrap text-slate-300">
                  {data.prediction.llm_rationale}
                </pre>
              </div>
            )}

            <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-slate-800/60 pt-3 text-xs text-slate-500">
              <span>
                model{" "}
                <span className="font-mono text-orange-400">{data.prediction.model_version}</span>
              </span>
              <span>·</span>
              <span>
                BTC spot{" "}
                <span className="font-mono text-slate-300">
                  ${Number(data.prediction.spot_price ?? "0").toLocaleString()}
                </span>
              </span>
              <span>·</span>
              <span>
                30d 波动{" "}
                <span className="font-mono text-slate-300">
                  {(num(data.prediction.realized_vol) * 100).toFixed(2)}%
                </span>
              </span>
              <span>·</span>
              <span>{fmtUtc(data.prediction.created_at)}</span>
            </div>
          </section>
        </>
      )}
    </main>
  );
}

function Stat({ label, value, small }: { label: string; value: string; small?: boolean }) {
  return (
    <div>
      <div className="text-xs tracking-wider text-slate-500 uppercase">{label}</div>
      <div className={cn("mt-1 font-mono text-slate-100", small ? "text-sm" : "text-lg")}>
        {value}
      </div>
    </div>
  );
}

function BigNum({
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
        className={cn("mt-2 font-mono font-bold tabular-nums", cls, big ? "text-3xl" : "text-2xl")}
      >
        {value}
      </div>
    </div>
  );
}
