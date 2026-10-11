"use client";

import { useEffect, useState } from "react";
import { Bell, Brain, Search, Settings as SettingsIcon, Zap } from "lucide-react";
import { useSettings, useUpdateSettings, useTestFeishu } from "@/hooks/use-settings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const MODEL_OPTIONS = ["gpt-5.5", "gpt-5", "gpt-5-mini", "gpt-4o", "gpt-4o-mini"];

interface FormState {
  entry_threshold: string;
  debounce_minutes: string;
  price_poll_minutes: string;
  predict_ttl_hours: string;
  discovery_keywords: string;
  discovery_max_days_to_resolve: string;
  feishu_webhook_url: string;
  openai_api_key: string;
  openai_model: string;
}

const EMPTY: FormState = {
  entry_threshold: "",
  debounce_minutes: "",
  price_poll_minutes: "",
  predict_ttl_hours: "",
  discovery_keywords: "",
  discovery_max_days_to_resolve: "",
  feishu_webhook_url: "",
  openai_api_key: "",
  openai_model: "",
};

export default function SettingsPage() {
  const settingsQ = useSettings();
  const updateMut = useUpdateSettings();
  const testFeishuMut = useTestFeishu();
  const [form, setForm] = useState<FormState>(EMPTY);
  const [dirty, setDirty] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!settingsQ.data) return;
    const s = settingsQ.data;
    setForm({
      entry_threshold: String(s.entry_threshold),
      debounce_minutes: String(s.debounce_minutes),
      price_poll_minutes: String(s.price_poll_minutes),
      predict_ttl_hours: String(s.predict_ttl_hours),
      discovery_keywords: s.discovery_keywords.join(", "),
      discovery_max_days_to_resolve: String(s.discovery_max_days_to_resolve),
      feishu_webhook_url: s.feishu_webhook_url ?? "",
      openai_api_key: s.openai_api_key ?? "",
      openai_model: s.openai_model ?? "",
    });
    setDirty(new Set());
  }, [settingsQ.data]);

  const update = (k: keyof FormState, v: string) => {
    setForm((p) => ({ ...p, [k]: v }));
    setDirty((p) => new Set(p).add(k));
  };

  const handleSave = async () => {
    const patch: Record<string, unknown> = {};
    if (dirty.has("entry_threshold")) patch.entry_threshold = Number(form.entry_threshold);
    if (dirty.has("debounce_minutes")) patch.debounce_minutes = Number(form.debounce_minutes);
    if (dirty.has("price_poll_minutes")) patch.price_poll_minutes = Number(form.price_poll_minutes);
    if (dirty.has("predict_ttl_hours")) patch.predict_ttl_hours = Number(form.predict_ttl_hours);
    if (dirty.has("discovery_keywords")) {
      patch.discovery_keywords = form.discovery_keywords
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
    }
    if (dirty.has("discovery_max_days_to_resolve"))
      patch.discovery_max_days_to_resolve = Number(form.discovery_max_days_to_resolve);
    if (dirty.has("feishu_webhook_url") && !form.feishu_webhook_url.includes("***hidden***"))
      patch.feishu_webhook_url = form.feishu_webhook_url;
    if (dirty.has("openai_api_key") && !form.openai_api_key.includes("***hidden***"))
      patch.openai_api_key = form.openai_api_key;
    if (dirty.has("openai_model")) patch.openai_model = form.openai_model;

    if (Object.keys(patch).length === 0) {
      toast.info("无修改");
      return;
    }
    try {
      await updateMut.mutateAsync(patch as Parameters<typeof updateMut.mutateAsync>[0]);
      toast.success(`已保存 ${Object.keys(patch).length} 项`);
    } catch (e) {
      toast.error(`保存失败：${e instanceof Error ? e.message : String(e)}`);
    }
  };

  const handleTestFeishu = async () => {
    try {
      const r = await testFeishuMut.mutateAsync();
      if (r.ok) toast.success("飞书测试卡片已发送，去群里查看");
      else toast.error(`飞书测试失败：${r.error}`);
    } catch (e) {
      toast.error(`飞书测试失败：${e instanceof Error ? e.message : String(e)}`);
    }
  };

  if (settingsQ.isLoading) {
    return (
      <main className="mx-auto max-w-4xl px-6 py-12">
        <p className="text-slate-500">加载中…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-6 py-8">
      <header className="animate-fade-up flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-50">设置</h1>
          <p className="mt-1 text-sm text-slate-400">
            所有变更立即写库，最迟 5 分钟内被下一轮调度生效。敏感字段已 mask（含
            ***hidden***），保留即不变。
          </p>
        </div>
        <Button
          onClick={handleSave}
          disabled={dirty.size === 0 || updateMut.isPending}
          className="h-10 bg-gradient-to-r from-orange-500 to-amber-500 px-6 font-semibold text-white shadow-lg shadow-orange-500/30 hover:from-orange-400 hover:to-amber-400 disabled:opacity-40"
        >
          {updateMut.isPending ? "保存中…" : `保存 (${dirty.size})`}
        </Button>
      </header>

      <Section icon={<Zap className="h-4 w-4" />} title="信号引擎" delay={50}>
        <Field
          label="入场阈值 entry_threshold"
          hint="gap 绝对值超过此值才触发入场（默认 0.15 = 15pp）"
          value={form.entry_threshold}
          onChange={(v) => update("entry_threshold", v)}
          type="number"
          step="0.01"
        />
        <Field
          label="去抖窗口 debounce_minutes"
          hint="状态变更后多久内禁止再次跃迁（默认 10 分钟）"
          value={form.debounce_minutes}
          onChange={(v) => update("debounce_minutes", v)}
          type="number"
        />
        <Field
          label="价格轮询 price_poll_minutes"
          hint="多久从 CLOB 拉一次中价（默认 5 分钟）"
          value={form.price_poll_minutes}
          onChange={(v) => update("price_poll_minutes", v)}
          type="number"
        />
        <Field
          label="AI 重预测 TTL predict_ttl_hours"
          hint="预测在多久内被视为新鲜不重算（默认 24 小时）"
          value={form.predict_ttl_hours}
          onChange={(v) => update("predict_ttl_hours", v)}
          type="number"
        />
      </Section>

      <Section icon={<Search className="h-4 w-4" />} title="市场发现" delay={100}>
        <Field
          label="关键词 discovery_keywords"
          hint="逗号分隔；question/slug/tags 任一含关键词即匹配"
          value={form.discovery_keywords}
          onChange={(v) => update("discovery_keywords", v)}
          placeholder="bitcoin, btc"
        />
        <Field
          label="最大剩余天数 discovery_max_days_to_resolve"
          hint="只关注未来 N 天内结算的市场"
          value={form.discovery_max_days_to_resolve}
          onChange={(v) => update("discovery_max_days_to_resolve", v)}
          type="number"
        />
      </Section>

      <Section icon={<Bell className="h-4 w-4" />} title="飞书推送" delay={150}>
        <Field
          label="webhook URL"
          hint="飞书自定义机器人 webhook；未配置时进入 dry-run 模式"
          value={form.feishu_webhook_url}
          onChange={(v) => update("feishu_webhook_url", v)}
          placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..."
        />
        <Button
          onClick={handleTestFeishu}
          disabled={
            testFeishuMut.isPending ||
            !form.feishu_webhook_url ||
            form.feishu_webhook_url.includes("***hidden***")
          }
          className="h-9 border border-orange-500/40 bg-orange-500/10 px-4 text-sm text-orange-300 hover:bg-orange-500/20"
        >
          {testFeishuMut.isPending ? "发送中…" : "🚀 发一条测试卡片"}
        </Button>
      </Section>

      <Section icon={<Brain className="h-4 w-4" />} title="LLM 调整器" delay={200}>
        <Field
          label="OpenAI / AIHubMix API Key"
          hint="OpenAI 兼容端点的 key；未配置时降级到纯量化"
          value={form.openai_api_key}
          onChange={(v) => update("openai_api_key", v)}
          type="password"
          placeholder="sk-..."
        />
        <div>
          <Label className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
            模型
          </Label>
          <select
            value={form.openai_model}
            onChange={(e) => update("openai_model", e.target.value)}
            className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 focus:border-orange-500/50 focus:outline-none"
          >
            {MODEL_OPTIONS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <p className="mt-1.5 text-xs text-slate-500">
            用 AIHubMix 时建议 gpt-5.5 / gpt-5-mini / gpt-4o-mini
          </p>
        </div>
      </Section>
    </main>
  );
}

function Section({
  icon,
  title,
  children,
  delay,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
  delay: number;
}) {
  return (
    <section
      className="animate-fade-up glass-card rounded-2xl p-6"
      style={{ animationDelay: `${delay}ms` }}
    >
      <h2 className="mb-5 flex items-center gap-2 text-base font-semibold text-slate-100">
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-orange-500/15 text-orange-400">
          {icon}
        </span>
        {title}
      </h2>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">{children}</div>
    </section>
  );
}

function Field({
  label,
  hint,
  value,
  onChange,
  type = "text",
  step,
  placeholder,
}: {
  label: string;
  hint?: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  step?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <Label className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
        {label}
      </Label>
      <Input
        className={cn(
          "mt-2 h-10 border-slate-700 bg-slate-950/60 text-sm text-slate-100 placeholder:text-slate-600",
          "focus-visible:ring-orange-500/30",
        )}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        step={step}
        placeholder={placeholder}
      />
      {hint && <p className="mt-1.5 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
