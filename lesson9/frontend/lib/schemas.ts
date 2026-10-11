// Zod schemas，与 backend Pydantic schema 人工对齐（backend-PRD §4 + §5）
// 后端用 numeric/Decimal 字段，JSON 序列化时输出为字符串（如 "0.7200"、"108000.00000000"），
// 前端保持字符串读入，渲染时按需调 lib/format.ts 的辅助函数转 number。
import { z } from "zod";

// ---------- 基础工具 ----------

// ISO8601 时间字符串（必须带 Z 或 +00:00 后缀，UTC）
export const IsoDateTimeSchema = z.string().refine(
  (s) => {
    const d = new Date(s);
    return !Number.isNaN(d.getTime());
  },
  { message: "需为合法 ISO8601 时间字符串" },
);

// 数值字符串（Decimal 序列化结果），统一在 UI 层解析
export const DecimalStringSchema = z.string();

// ---------- 枚举 ----------

export const MarketStateSchema = z.enum(["WATCHING", "ENTERED_LONG", "ENTERED_SHORT", "EXPIRED"]);
export type MarketState = z.infer<typeof MarketStateSchema>;

export const MarketSourceSchema = z.enum(["discovery", "manual"]);
export type MarketSource = z.infer<typeof MarketSourceSchema>;

export const MarketDirectionSchema = z.enum(["above", "below"]);
export type MarketDirection = z.infer<typeof MarketDirectionSchema>;

export const SignalKindSchema = z.enum([
  "ENTRY_LONG",
  "ENTRY_SHORT",
  "EXIT_LONG",
  "EXIT_SHORT",
  "EXPIRED",
]);
export type SignalKind = z.infer<typeof SignalKindSchema>;

export const LlmConfidenceSchema = z.enum(["low", "medium", "high"]);
export type LlmConfidence = z.infer<typeof LlmConfidenceSchema>;

export const WebSearchProviderSchema = z.enum(["tavily", "exa", "brave", "openai"]);
export type WebSearchProvider = z.infer<typeof WebSearchProviderSchema>;

export const JobStatusSchema = z.enum(["running", "success", "failed"]);
export type JobStatus = z.infer<typeof JobStatusSchema>;

export const JobNameSchema = z.enum([
  "daily_discovery",
  "price_poll",
  "ai_repredict_check",
  "feishu_retry",
  "price_tick_cleanup",
]);
export type JobName = z.infer<typeof JobNameSchema>;

// ---------- 子结构 ----------

export const NewsSourceSchema = z.object({
  title: z.string(),
  url: z.string().url(),
  snippet: z.string(),
  published_at: IsoDateTimeSchema.optional().nullable(),
});
export type NewsSource = z.infer<typeof NewsSourceSchema>;

// ---------- Prediction ----------

export const PredictionSchema = z.object({
  id: z.number().int(),
  p_ai: DecimalStringSchema,
  p_quant: DecimalStringSchema,
  llm_adjustment: DecimalStringSchema,
  llm_confidence: LlmConfidenceSchema.nullable(),
  llm_rationale: z.string().nullable(),
  news_sources: z.array(NewsSourceSchema),
  spot_price: DecimalStringSchema.nullable(),
  realized_vol: DecimalStringSchema.nullable(),
  model_version: z.string(),
  created_at: IsoDateTimeSchema,
});
export type Prediction = z.infer<typeof PredictionSchema>;

// list 接口里嵌套的精简 prediction
export const PredictionSummarySchema = z.object({
  p_ai: DecimalStringSchema,
  model_version: z.string(),
  created_at: IsoDateTimeSchema,
});
export type PredictionSummary = z.infer<typeof PredictionSummarySchema>;

// ---------- PriceTick ----------

export const PriceTickSchema = z.object({
  p_yes: DecimalStringSchema,
  p_no: DecimalStringSchema.nullable().optional(),
  fetched_at: IsoDateTimeSchema,
});
export type PriceTick = z.infer<typeof PriceTickSchema>;

export const PriceTickWithIdSchema = PriceTickSchema.extend({
  id: z.number().int().optional(),
  midpoint_source: z.string().optional(),
});
export type PriceTickWithId = z.infer<typeof PriceTickWithIdSchema>;

// ---------- Market ----------

// list 接口里 latest_price 的精简版本
export const LatestPriceSchema = z.object({
  p_yes: DecimalStringSchema,
  fetched_at: IsoDateTimeSchema,
});
export type LatestPrice = z.infer<typeof LatestPriceSchema>;

export const MarketSchema = z.object({
  id: z.number().int(),
  condition_id: z.string(),
  slug: z.string(),
  question: z.string(),
  description: z.string().nullable().optional(),
  strike_price: DecimalStringSchema.nullable(),
  direction: MarketDirectionSchema.nullable(),
  resolve_at: IsoDateTimeSchema,
  state: MarketStateSchema,
  source: MarketSourceSchema,
  created_at: IsoDateTimeSchema,
  last_state_change_at: IsoDateTimeSchema,
  latest_prediction: PredictionSummarySchema.nullable().optional(),
  latest_price: LatestPriceSchema.nullable().optional(),
  // gap = p_ai - p_mkt；后端用 Decimal，前端字符串
  gap: DecimalStringSchema.nullable().optional(),
  // 详情页特有
  metadata: z.record(z.string(), z.unknown()).optional(),
  outcome_yes_token_id: z.string().optional(),
  outcome_no_token_id: z.string().optional(),
});
export type Market = z.infer<typeof MarketSchema>;

// ---------- SignalEvent ----------

// signal 列表里嵌套的精简 market / prediction
export const SignalMarketRefSchema = z.object({
  id: z.number().int(),
  question: z.string(),
  slug: z.string(),
});

export const SignalPredictionRefSchema = z.object({
  p_ai: DecimalStringSchema,
  model_version: z.string(),
});

export const SignalEventSchema = z.object({
  id: z.number().int(),
  market: SignalMarketRefSchema,
  prediction: SignalPredictionRefSchema,
  kind: SignalKindSchema,
  from_state: MarketStateSchema,
  to_state: MarketStateSchema,
  p_ai_at_event: DecimalStringSchema,
  p_mkt_at_event: DecimalStringSchema,
  gap: DecimalStringSchema,
  feishu_pushed: z.boolean(),
  feishu_push_at: IsoDateTimeSchema.nullable(),
  feishu_error: z.string().nullable(),
  feishu_retry_count: z.number().int().optional(),
  occurred_at: IsoDateTimeSchema,
});
export type SignalEvent = z.infer<typeof SignalEventSchema>;

// ---------- Setting ----------

export const SettingSchema = z.object({
  entry_threshold: DecimalStringSchema,
  debounce_minutes: z.number().int(),
  price_poll_minutes: z.number().int(),
  predict_ttl_hours: z.number().int(),
  discovery_keywords: z.array(z.string()),
  discovery_max_days_to_resolve: z.number().int(),
  feishu_webhook_url: z.string().nullable(),
  openai_api_key: z.string().nullable(),
  openai_model: z.string(),
  web_search_provider: WebSearchProviderSchema,
  web_search_api_key: z.string().nullable(),
  updated_at: IsoDateTimeSchema,
});
export type Setting = z.infer<typeof SettingSchema>;

// PATCH 请求体：所有字段可选，含越界校验
export const SettingPatchSchema = z.object({
  entry_threshold: z.number().min(0.01).max(0.5).optional(),
  debounce_minutes: z.number().int().min(1).optional(),
  price_poll_minutes: z.number().int().min(1).optional(),
  predict_ttl_hours: z.number().int().min(1).optional(),
  discovery_keywords: z.array(z.string().min(1)).min(1).optional(),
  discovery_max_days_to_resolve: z.number().int().min(1).max(365).optional(),
  feishu_webhook_url: z.string().url().optional(),
  openai_api_key: z.string().min(1).optional(),
  openai_model: z.string().min(1).optional(),
  web_search_provider: WebSearchProviderSchema.optional(),
  web_search_api_key: z.string().min(1).optional(),
});
export type SettingPatch = z.infer<typeof SettingPatchSchema>;

export const TestFeishuResponseSchema = z.union([
  z.object({
    ok: z.literal(true),
    status: z.number().int(),
    response: z.object({ code: z.number().int(), msg: z.string() }).passthrough(),
  }),
  z.object({
    ok: z.literal(false),
    status: z.number().int(),
    error: z.string(),
  }),
]);
export type TestFeishuResponse = z.infer<typeof TestFeishuResponseSchema>;

// ---------- JobRun / Scheduler ----------

export const JobRunSchema = z.object({
  id: z.number().int(),
  job_name: z.string(),
  status: JobStatusSchema,
  started_at: IsoDateTimeSchema,
  finished_at: IsoDateTimeSchema.nullable(),
  stats: z.record(z.string(), z.unknown()),
  error: z.string().nullable(),
});
export type JobRun = z.infer<typeof JobRunSchema>;

export const SchedulerJobSchema = z.object({
  name: z.string(),
  trigger: z.string(),
  interval_minutes: z.number().optional(),
  next_run_at: IsoDateTimeSchema.nullable(),
});
export type SchedulerJob = z.infer<typeof SchedulerJobSchema>;

export const SchedulerTriggerRequestSchema = z.object({
  job: JobNameSchema,
  market_id: z.number().int().optional(),
});
export type SchedulerTriggerRequest = z.infer<typeof SchedulerTriggerRequestSchema>;

export const SchedulerTriggerResponseSchema = z.object({
  job_run_id: z.number().int(),
});
export type SchedulerTriggerResponse = z.infer<typeof SchedulerTriggerResponseSchema>;

// ---------- Health / Readyz ----------

export const HealthzSchema = z.object({
  status: z.literal("ok"),
});

export const ReadyzSchema = z.object({
  status: z.enum(["ok", "degraded", "fail"]),
  components: z.record(z.string(), z.string()),
});
export type Readyz = z.infer<typeof ReadyzSchema>;

// ---------- List 响应通用 wrapper ----------

export function listResponse<T extends z.ZodTypeAny>(itemSchema: T) {
  return z.object({
    items: z.array(itemSchema),
    total: z.number().int().optional(),
    page: z.number().int().optional(),
    page_size: z.number().int().optional(),
  });
}

export const MarketListResponseSchema = listResponse(MarketSchema);
export type MarketListResponse = z.infer<typeof MarketListResponseSchema>;

export const PredictionListResponseSchema = listResponse(PredictionSchema);
export type PredictionListResponse = z.infer<typeof PredictionListResponseSchema>;

export const PriceTickListResponseSchema = listResponse(PriceTickSchema);
export type PriceTickListResponse = z.infer<typeof PriceTickListResponseSchema>;

export const SignalListResponseSchema = listResponse(SignalEventSchema);
export type SignalListResponse = z.infer<typeof SignalListResponseSchema>;

export const JobRunListResponseSchema = listResponse(JobRunSchema);
export type JobRunListResponse = z.infer<typeof JobRunListResponseSchema>;

export const SchedulerJobListResponseSchema = listResponse(SchedulerJobSchema);
export type SchedulerJobListResponse = z.infer<typeof SchedulerJobListResponseSchema>;

// ---------- POST /markets / POST /predict 响应 ----------

export const MarketWithPredictionSchema = z.object({
  market: MarketSchema,
  prediction: PredictionSchema,
});
export type MarketWithPrediction = z.infer<typeof MarketWithPredictionSchema>;

export const MarketPreviewSchema = z.object({
  question: z.string(),
  strike_price: DecimalStringSchema.nullable(),
  direction: MarketDirectionSchema.nullable(),
  resolve_at: IsoDateTimeSchema,
  // 从 event 集合自动选 sub-market 时附加（用户贴 event URL 而非具体 market URL）
  chosen_from_event: z.string().nullable().optional(),
  event_sub_count: z.number().int().nullable().optional(),
  chosen_midpoint: DecimalStringSchema.nullable().optional(),
});
export type MarketPreview = z.infer<typeof MarketPreviewSchema>;

export const PredictDryRunResponseSchema = z.object({
  market_preview: MarketPreviewSchema,
  prediction: PredictionSchema,
});
export type PredictDryRunResponse = z.infer<typeof PredictDryRunResponseSchema>;

// ---------- 表单 Schema ----------

// 安全地拿 URL host/pathname；非法 URL → 返回 null（后续 refine 拒绝）
function tryParseUrl(s: string): URL | null {
  try {
    return new URL(s);
  } catch {
    return null;
  }
}

// 精确域名匹配：严格等于 polymarket.com 或以 .polymarket.com 结尾
// 防止 evilpolymarket.com 这种子串劫持
function isPolymarketHost(host: string): boolean {
  return host === "polymarket.com" || host.endsWith(".polymarket.com");
}

export const PolymarketUrlSchema = z
  .string()
  .min(1, { message: "URL 不能为空" })
  .refine((s) => tryParseUrl(s) !== null, { message: "URL 格式不合法" })
  .refine(
    (s) => {
      const url = tryParseUrl(s);
      return url !== null && isPolymarketHost(url.host);
    },
    { message: "URL 必须是 polymarket.com 域名" },
  )
  .refine(
    (s) => {
      const url = tryParseUrl(s);
      return url !== null && /\/(event|market)\//.test(url.pathname);
    },
    { message: "URL 必须包含 /event/ 或 /market/" },
  );
export type PolymarketUrl = z.infer<typeof PolymarketUrlSchema>;

export const AddMarketRequestSchema = z.object({
  polymarket_url: PolymarketUrlSchema,
});
export type AddMarketRequest = z.infer<typeof AddMarketRequestSchema>;
