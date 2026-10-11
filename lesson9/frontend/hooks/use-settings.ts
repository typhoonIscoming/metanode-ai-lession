"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import {
  SettingPatchSchema,
  SettingSchema,
  TestFeishuResponseSchema,
  type Setting,
  type SettingPatch,
  type TestFeishuResponse,
} from "@/lib/schemas";

const SETTINGS_KEY = ["settings"] as const;

/**
 * GET /settings — 全局配置（敏感字段 mask 后给前端）
 */
export function useSettings() {
  return useQuery({
    queryKey: SETTINGS_KEY,
    queryFn: async (): Promise<Setting> => {
      const raw = await apiFetch<unknown>("/settings");
      return SettingSchema.parse(raw);
    },
  });
}

/**
 * PATCH /settings — 部分字段更新；变更立即生效（后端 60s 内对调度生效）
 */
export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (patch: SettingPatch): Promise<Setting> => {
      const parsed = SettingPatchSchema.parse(patch);
      const raw = await apiFetch<unknown>("/settings", {
        method: "PATCH",
        body: JSON.stringify(parsed),
      });
      return SettingSchema.parse(raw);
    },
    onSuccess: (data) => {
      qc.setQueryData(SETTINGS_KEY, data);
      qc.invalidateQueries({ queryKey: SETTINGS_KEY });
    },
  });
}

/**
 * POST /settings/test_feishu — 发测试卡片
 */
export function useTestFeishu() {
  return useMutation({
    mutationFn: async (): Promise<TestFeishuResponse> => {
      const raw = await apiFetch<unknown>("/settings/test_feishu", { method: "POST" });
      return TestFeishuResponseSchema.parse(raw);
    },
  });
}
