// lib/schemas.ts Zod schema 测试
// PolymarketUrlSchema 至少 6 个 case：合法 + 非法各种形态
import { describe, expect, it } from "vitest";
import { PolymarketUrlSchema } from "@/lib/schemas";

describe("PolymarketUrlSchema", () => {
  it("接受 polymarket.com/event/ 标准 URL", () => {
    const result = PolymarketUrlSchema.safeParse(
      "https://polymarket.com/event/bitcoin-above-on-may-17",
    );
    expect(result.success).toBe(true);
  });

  it("接受 polymarket.com/zh/event/ 中文路径", () => {
    const result = PolymarketUrlSchema.safeParse(
      "https://polymarket.com/zh/event/bitcoin-above-on-may-17",
    );
    expect(result.success).toBe(true);
  });

  it("接受 polymarket.com/market/ 旧路径", () => {
    const result = PolymarketUrlSchema.safeParse(
      "https://polymarket.com/market/bitcoin-above-on-may-17",
    );
    expect(result.success).toBe(true);
  });

  it("接受 polymarket.com 子域名（PRD §3.1 兼容 www）", () => {
    const result = PolymarketUrlSchema.safeParse(
      "https://www.polymarket.com/event/bitcoin-above-on-may-17",
    );
    expect(result.success).toBe(true);
  });

  it("接受带 query 与 fragment（slug 解析由 backend 处理）", () => {
    const result = PolymarketUrlSchema.safeParse(
      "https://polymarket.com/event/bitcoin-above-on-may-17?utm_source=x#section",
    );
    expect(result.success).toBe(true);
  });

  it("拒绝非 polymarket.com 域名", () => {
    const result = PolymarketUrlSchema.safeParse(
      "https://example.com/event/bitcoin-above-on-may-17",
    );
    expect(result.success).toBe(false);
    if (!result.success) {
      const messages = result.error.issues.map((i) => i.message).join(";");
      expect(messages).toMatch(/polymarket\.com/);
    }
  });

  it("拒绝路径不含 /event/ 或 /market/", () => {
    const result = PolymarketUrlSchema.safeParse("https://polymarket.com/about");
    expect(result.success).toBe(false);
    if (!result.success) {
      const messages = result.error.issues.map((i) => i.message).join(";");
      expect(messages).toMatch(/\/event\/|\/market\//);
    }
  });

  it("拒绝非 URL 字符串", () => {
    const result = PolymarketUrlSchema.safeParse("not a url at all");
    expect(result.success).toBe(false);
  });

  it("拒绝空字符串", () => {
    const result = PolymarketUrlSchema.safeParse("");
    expect(result.success).toBe(false);
  });

  // ⚠ 安全相关：endsWith("polymarket.com") 会把 "evilpolymarket.com" 视为通过；
  // 安全实现应：host === 'polymarket.com' || host.endsWith('.polymarket.com')。
  // 这条 case 当前红 = lib/schemas.ts:322 endsWith 检查有子域名劫持风险，已通知 frontend。
  it("拒绝伪造域名劫持子串（subdomain takeover）", () => {
    const result = PolymarketUrlSchema.safeParse("https://evilpolymarket.com/event/fake");
    expect(result.success).toBe(false);
  });
});
