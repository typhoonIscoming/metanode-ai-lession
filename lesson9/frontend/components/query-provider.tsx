"use client";

import { QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MutationCache } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { toast } from "sonner";
import { ApiError } from "@/lib/api";

// 全局错误转 Toast：404 不弹（页面自己处理），其余 ApiError 弹右下角
function notifyApiError(error: unknown): void {
  if (!(error instanceof ApiError)) return;
  if (error.status === 404) return;
  toast.error(`[${error.code}] ${error.message}`);
}

export function QueryProvider({ children }: { children: ReactNode }) {
  // useState 保证 client 实例在每个浏览器 session 只创建一次
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 10_000,
            retry: (failureCount, error) => {
              // 404 / 422 不重试；网络层错误重试 1 次
              if (error instanceof ApiError) {
                if (error.status && error.status >= 400 && error.status < 500) return false;
              }
              return failureCount < 1;
            },
            refetchOnWindowFocus: false,
          },
          mutations: {
            retry: false,
          },
        },
        queryCache: new QueryCache({
          onError: (err) => notifyApiError(err),
        }),
        mutationCache: new MutationCache({
          onError: (err) => notifyApiError(err),
        }),
      }),
  );

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
