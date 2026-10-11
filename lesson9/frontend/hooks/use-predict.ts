"use client";

import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import {
  AddMarketRequestSchema,
  PredictDryRunResponseSchema,
  type AddMarketRequest,
  type PredictDryRunResponse,
} from "@/lib/schemas";

/**
 * POST /predict — 「试一次不入库」，返回市场预览 + 预测结果
 * 区别于 useAddMarket（POST /markets，入库 + 加监控）
 */
export function usePredictDryRun() {
  return useMutation({
    mutationFn: async (body: AddMarketRequest): Promise<PredictDryRunResponse> => {
      const parsed = AddMarketRequestSchema.parse(body);
      const raw = await apiFetch<unknown>("/predict", {
        method: "POST",
        body: JSON.stringify(parsed),
      });
      return PredictDryRunResponseSchema.parse(raw);
    },
  });
}
