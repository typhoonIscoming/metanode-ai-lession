"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, qs } from "@/lib/api";
import {
  AddMarketRequestSchema,
  MarketListResponseSchema,
  MarketSchema,
  MarketWithPredictionSchema,
  PredictionListResponseSchema,
  PriceTickListResponseSchema,
  type AddMarketRequest,
  type Market,
  type MarketListResponse,
  type MarketSource,
  type MarketState,
  type MarketWithPrediction,
  type PredictionListResponse,
  type PriceTickListResponse,
} from "@/lib/schemas";

// 仪表盘与详情页保持 30s 自动 refetch（PRD §7.2）
const LIVE_REFETCH_MS = 30_000;

export interface MarketFilter {
  state?: MarketState | MarketState[];
  source?: MarketSource;
  limit?: number;
  offset?: number;
}

/**
 * GET /markets 列表，30s 自动 refetch
 */
export function useMarkets(filter: MarketFilter = {}) {
  return useQuery({
    queryKey: ["markets", filter] as const,
    queryFn: async (): Promise<MarketListResponse> => {
      const raw = await apiFetch<unknown>(
        `/markets${qs({
          state: Array.isArray(filter.state) ? filter.state : filter.state,
          source: filter.source,
          limit: filter.limit,
          offset: filter.offset,
        })}`,
      );
      return MarketListResponseSchema.parse(raw);
    },
    refetchInterval: LIVE_REFETCH_MS,
    placeholderData: keepPreviousData,
  });
}

/**
 * GET /markets/{id} 单条；404 不重试、不弹 Toast
 */
export function useMarket(id: number | null | undefined) {
  return useQuery({
    queryKey: ["market", id] as const,
    queryFn: async (): Promise<Market> => {
      const raw = await apiFetch<unknown>(`/markets/${id}`);
      return MarketSchema.parse(raw);
    },
    enabled: id !== null && id !== undefined,
    refetchInterval: LIVE_REFETCH_MS,
    placeholderData: keepPreviousData,
  });
}

/**
 * GET /markets/{id}/predictions
 */
export function usePredictions(marketId: number | null | undefined) {
  return useQuery({
    queryKey: ["predictions", marketId] as const,
    queryFn: async (): Promise<PredictionListResponse> => {
      const raw = await apiFetch<unknown>(`/markets/${marketId}/predictions`);
      return PredictionListResponseSchema.parse(raw);
    },
    enabled: marketId !== null && marketId !== undefined,
    refetchInterval: LIVE_REFETCH_MS,
    placeholderData: keepPreviousData,
  });
}

export interface PriceTickFilter {
  from?: string;
  to?: string;
  granularity?: "raw" | "hourly";
}

/**
 * GET /markets/{id}/price_ticks
 */
export function usePriceTicks(marketId: number | null | undefined, filter: PriceTickFilter = {}) {
  return useQuery({
    queryKey: ["price_ticks", marketId, filter] as const,
    queryFn: async (): Promise<PriceTickListResponse> => {
      const raw = await apiFetch<unknown>(`/markets/${marketId}/price_ticks${qs(filter)}`);
      return PriceTickListResponseSchema.parse(raw);
    },
    enabled: marketId !== null && marketId !== undefined,
    refetchInterval: LIVE_REFETCH_MS,
    placeholderData: keepPreviousData,
  });
}

/**
 * POST /markets — 加入监控
 */
export function useAddMarket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: AddMarketRequest): Promise<MarketWithPrediction> => {
      const parsed = AddMarketRequestSchema.parse(body);
      const raw = await apiFetch<unknown>("/markets", {
        method: "POST",
        body: JSON.stringify(parsed),
      });
      return MarketWithPredictionSchema.parse(raw);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["markets"] });
    },
  });
}

/**
 * DELETE /markets/{id} — 软删（state → EXPIRED）
 */
export function useDeleteMarket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number): Promise<void> => {
      await apiFetch<void>(`/markets/${id}`, { method: "DELETE" });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["markets"] });
    },
  });
}

/**
 * POST /markets/{id}/repredict — 立即重跑
 */
export function useRepredict() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const raw = await apiFetch<unknown>(`/markets/${id}/repredict`, { method: "POST" });
      return raw;
    },
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: ["predictions", id] });
      qc.invalidateQueries({ queryKey: ["market", id] });
    },
  });
}
