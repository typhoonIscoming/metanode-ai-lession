// 后端 API 基础 URL，注意 NEXT_PUBLIC_API_BASE 已包含 `/api/v1` 前缀
// 调用方写 `apiFetch("/markets")` 而不是 `apiFetch("/api/v1/markets")`
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";

// 后端错误响应结构。兼容两种格式：
// 1. 自定义：`{error: {code, message, details?}}`
// 2. FastAPI 默认 HTTPException：`{detail: "..."}` 或 `{detail: [{loc, msg, type}]}`（422 validation）
export interface ApiErrorBody {
  error?: { code?: string; message?: string; details?: unknown };
  detail?: string | Array<{ loc?: unknown; msg?: string; type?: string }>;
}

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public details?: unknown,
    public status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// 开发期防呆：禁止调用方把 `/api/v1` 写进 path
function assertNoVersionPrefix(path: string): void {
  if (process.env.NODE_ENV !== "production" && path.startsWith("/api/v1")) {
    console.warn(`[api] path "${path}" 不应以 "/api/v1" 开头：NEXT_PUBLIC_API_BASE 已含前缀`);
  }
}

/**
 * 把查询参数对象序列化为 URLSearchParams 字符串。
 * 跳过 undefined / null；数组转重复 key；其它值 String() 化。
 * 用泛型 + object 约束以兼容具名 interface（不需要 index signature）。
 */
export function qs<T extends object>(params: T): string {
  const usp = new URLSearchParams();
  for (const [key, value] of Object.entries(params as Record<string, unknown>)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      for (const v of value) usp.append(key, String(v));
    } else {
      usp.append(key, String(value));
    }
  }
  const s = usp.toString();
  return s ? `?${s}` : "";
}

// 统一 fetch 封装：non-2xx 抛 ApiError；204 No Content 返回 undefined
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  assertNoVersionPrefix(path);
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const body = (await res
      .json()
      .catch(() => ({ error: { code: "UNKNOWN", message: res.statusText } }))) as ApiErrorBody;
    // 兼容 FastAPI HTTPException 的 {detail: "..."} 和 validation 的 {detail: [...]}
    let detailMsg: string | undefined;
    if (typeof body.detail === "string") {
      detailMsg = body.detail;
    } else if (Array.isArray(body.detail) && body.detail.length > 0) {
      detailMsg = body.detail.map((d) => d.msg ?? JSON.stringify(d)).join("; ");
    }
    throw new ApiError(
      body.error?.code ?? "UNKNOWN",
      body.error?.message ?? detailMsg ?? `HTTP ${res.status} ${res.statusText}`,
      body.error?.details,
      res.status,
    );
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}
