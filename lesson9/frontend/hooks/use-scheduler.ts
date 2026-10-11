"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, qs } from "@/lib/api";
import {
  JobRunListResponseSchema,
  SchedulerJobListResponseSchema,
  SchedulerTriggerRequestSchema,
  SchedulerTriggerResponseSchema,
  type JobRunListResponse,
  type JobStatus,
  type SchedulerJobListResponse,
  type SchedulerTriggerRequest,
  type SchedulerTriggerResponse,
} from "@/lib/schemas";

/**
 * GET /scheduler/jobs — 5 个 job 当前状态 + next_run_at
 */
export function useSchedulerJobs() {
  return useQuery({
    queryKey: ["scheduler", "jobs"] as const,
    queryFn: async (): Promise<SchedulerJobListResponse> => {
      const raw = await apiFetch<unknown>("/scheduler/jobs");
      return SchedulerJobListResponseSchema.parse(raw);
    },
    placeholderData: keepPreviousData,
  });
}

export interface JobRunFilter {
  job_name?: string;
  status?: JobStatus;
  limit?: number;
}

/**
 * GET /scheduler/runs — job 执行历史
 */
export function useSchedulerRuns(filter: JobRunFilter = {}) {
  return useQuery({
    queryKey: ["scheduler", "runs", filter] as const,
    queryFn: async (): Promise<JobRunListResponse> => {
      const raw = await apiFetch<unknown>(`/scheduler/runs${qs(filter)}`);
      return JobRunListResponseSchema.parse(raw);
    },
    placeholderData: keepPreviousData,
  });
}

/**
 * POST /scheduler/trigger — 手动触发某个 job
 */
export function useTriggerJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: SchedulerTriggerRequest): Promise<SchedulerTriggerResponse> => {
      const parsed = SchedulerTriggerRequestSchema.parse(body);
      const raw = await apiFetch<unknown>("/scheduler/trigger", {
        method: "POST",
        body: JSON.stringify(parsed),
      });
      return SchedulerTriggerResponseSchema.parse(raw);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["scheduler"] });
    },
  });
}
