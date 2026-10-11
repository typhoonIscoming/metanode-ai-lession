// lib/api.ts 测试：覆盖 apiFetch 全部分支 + qs helper
// 关键场景：2xx 解析、204 返 undefined、4xx/5xx 抛 ApiError、错误响应体非法 JSON 走 fallback
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch, qs } from "@/lib/api";

// 用 vi.stubGlobal 注入 fetch mock；每个 case 单独 stub Response
function mockJsonResponse(body: unknown, init: { status?: number; ok?: boolean } = {}) {
  const status = init.status ?? 200;
  return {
    ok: init.ok ?? (status >= 200 && status < 300),
    status,
    statusText: status === 200 ? "OK" : `HTTP ${status}`,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response;
}

function mockNoContentResponse() {
  return {
    ok: true,
    status: 204,
    statusText: "No Content",
    json: vi.fn().mockRejectedValue(new Error("204 should not parse body")),
  } as unknown as Response;
}

function mockBadJsonResponse(status: number) {
  return {
    ok: false,
    status,
    statusText: `HTTP ${status}`,
    json: vi.fn().mockRejectedValue(new SyntaxError("Unexpected token")),
  } as unknown as Response;
}

describe("apiFetch", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("2xx 解析 JSON 并返回 body", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      mockJsonResponse({ id: 1, name: "市场 X" }),
    );
    const data = await apiFetch<{ id: number; name: string }>("/markets/1");
    expect(data).toEqual({ id: 1, name: "市场 X" });
  });

  it("204 No Content 返 undefined（不调 .json）", async () => {
    const resp = mockNoContentResponse();
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(resp);
    const data = await apiFetch<void>("/markets/1", { method: "DELETE" });
    expect(data).toBeUndefined();
    expect(resp.json).not.toHaveBeenCalled();
  });

  it("4xx 抛 ApiError，code/message/status 字段正确", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      mockJsonResponse(
        { error: { code: "MARKET_NOT_FOUND", message: "市场不存在", details: { id: 999 } } },
        { status: 404, ok: false },
      ),
    );
    await expect(apiFetch("/markets/999")).rejects.toMatchObject({
      code: "MARKET_NOT_FOUND",
      message: "市场不存在",
      status: 404,
      details: { id: 999 },
    });
  });

  it("5xx 抛 ApiError", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      mockJsonResponse(
        { error: { code: "INTERNAL_ERROR", message: "服务器异常" } },
        { status: 500, ok: false },
      ),
    );
    const err = (await apiFetch("/markets").catch((e: unknown) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("INTERNAL_ERROR");
    expect(err.status).toBe(500);
  });

  it("422 错误码 + URL_INVALID 等业务错误", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      mockJsonResponse(
        { error: { code: "URL_INVALID", message: "URL 解析失败" } },
        { status: 422, ok: false },
      ),
    );
    await expect(apiFetch("/markets", { method: "POST" })).rejects.toMatchObject({
      code: "URL_INVALID",
      status: 422,
    });
  });

  it("错误响应体非法 JSON 时降级用 statusText 作为 message", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockBadJsonResponse(502));
    const err = (await apiFetch("/markets").catch((e: unknown) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("UNKNOWN");
    // 当 .json() reject 时，api.ts 的 catch 用 { error: { code:"UNKNOWN", message:res.statusText } }
    // 兜底；所以 message 是 mock 的 statusText 而不是 "未知错误"
    expect(err.message).toBe("HTTP 502");
    expect(err.status).toBe(502);
  });

  it("path 以 /api/v1 开头时开发期 console.warn", async () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockJsonResponse({}));
    await apiFetch("/api/v1/markets");
    expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining("/api/v1"));
  });

  it("注入自定义 headers 与默认 Content-Type 合并", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockJsonResponse({}));
    await apiFetch("/markets", { method: "POST", headers: { "X-Foo": "bar" } });
    const callArgs = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(callArgs[1].headers).toMatchObject({
      "Content-Type": "application/json",
      "X-Foo": "bar",
    });
  });
});

describe("qs helper", () => {
  it("空对象返回空串（无前导 ?）", () => {
    expect(qs({})).toBe("");
  });

  it("跳过 undefined / null", () => {
    expect(qs({ a: undefined, b: null, c: "x" })).toBe("?c=x");
  });

  it("数组转重复 key", () => {
    expect(qs({ kind: ["ENTRY_LONG", "EXIT_LONG"] })).toBe("?kind=ENTRY_LONG&kind=EXIT_LONG");
  });

  it("数字 / boolean 都 String()", () => {
    expect(qs({ limit: 50, active: true })).toBe("?limit=50&active=true");
  });

  it("中文与特殊字符 URL encode", () => {
    expect(qs({ q: "市场 X" })).toBe("?q=%E5%B8%82%E5%9C%BA+X");
  });
});
