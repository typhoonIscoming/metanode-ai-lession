"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { apiFetch, qs } from "@/lib/api";
import {
  SignalEventSchema,
  SignalListResponseSchema,
  type SignalEvent,
  type SignalKind,
  type SignalListResponse,
} from "@/lib/schemas";

export interface SignalFilter {
  kind?: SignalKind;
  market_id?: number;
  from?: string;
  to?: string;
  limit?: number;
  offset?: number;
}

/**
 * GET /signals 列表（推送历史 + 仪表盘「今日推送」KPI 共用）
 */
export function useSignals(filter: SignalFilter = {}) {
  return useQuery({
    queryKey: ["signals", filter] as const,
    queryFn: async (): Promise<SignalListResponse> => {
      const raw = await apiFetch<unknown>(`/signals${qs(filter)}`);
      return SignalListResponseSchema.parse(raw);
    },
    placeholderData: keepPreviousData,
  });
}

/**
 * GET /signals/{id} 单条详情（含完整 prediction.rationale 与 news_sources）
 */
export function useSignal(id: number | null | undefined) {
  return useQuery({
    queryKey: ["signal", id] as const,
    queryFn: async (): Promise<SignalEvent> => {
      const raw = await apiFetch<unknown>(`/signals/${id}`);
      return SignalEventSchema.parse(raw);
    },
    enabled: id !== null && id !== undefined,
  });
}
