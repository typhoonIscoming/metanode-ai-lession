// 最小冒烟测试：验证 Vitest + RTL + jsdom + jest-dom matcher 链路打通
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

describe("vitest infra sanity", () => {
  it("jsdom renders + jest-dom matcher 可用", () => {
    render(<div data-testid="probe">hello</div>);
    const el = screen.getByTestId("probe");
    expect(el).toBeInTheDocument();
    expect(el).toHaveTextContent("hello");
  });

  it("ResizeObserver mock 已注入（Recharts 依赖）", () => {
    expect(typeof globalThis.ResizeObserver).toBe("function");
    const ro = new (
      globalThis as unknown as { ResizeObserver: new () => unknown }
    ).ResizeObserver();
    expect(ro).toBeDefined();
  });

  it("matchMedia mock 已注入（响应式 hook + Sonner 依赖）", () => {
    expect(typeof globalThis.matchMedia).toBe("function");
    const mq = (
      globalThis as unknown as {
        matchMedia: (q: string) => { matches: boolean };
      }
    ).matchMedia("(min-width: 768px)");
    expect(mq.matches).toBe(false);
  });
});
