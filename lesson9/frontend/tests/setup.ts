// Vitest setup：扩展 jest-dom 匹配器，并为 jsdom 缺失的浏览器 API 做 mock
import "@testing-library/jest-dom/vitest";

// Recharts / Radix 组件依赖 ResizeObserver；jsdom 默认不带
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
Object.defineProperty(globalThis, "ResizeObserver", {
  writable: true,
  value: ResizeObserverMock,
});

// matchMedia 用于响应式 hook 与 Sonner Toaster
Object.defineProperty(globalThis, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});
