import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Vitest 配置：jsdom 环境跑组件测试；setup 注入 testing-library 的扩展 matcher
// 覆盖率阈值与 docs/test-strategy.md §3.1 对齐：整体 ≥ 60%、关键组件单独 ≥ 80%
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    globals: true,
    css: false,
    include: ["tests/**/*.test.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      reportsDirectory: "./coverage",
      // 覆盖率收集范围：业务源码；排除测试本身、配置文件、shadcn 原子组件（不改源码）
      include: [
        "app/**/*.{ts,tsx}",
        "components/**/*.{ts,tsx}",
        "lib/**/*.{ts,tsx}",
        "hooks/**/*.{ts,tsx}",
      ],
      exclude: [
        "tests/**",
        "node_modules/**",
        "**/*.d.ts",
        "**/*.config.{ts,js,mjs,cjs}",
        "components/ui/**", // shadcn 生成原子组件，不计入业务覆盖率
        "app/**/layout.tsx",
        "app/**/loading.tsx",
        "app/**/error.tsx",
        "app/**/not-found.tsx",
        ".next/**",
      ],
      // 整体阈值；关键组件单独阈值由 pre-merge 的 test:cov-strict 脚本断言
      thresholds: {
        lines: 60,
        functions: 60,
        branches: 60,
        statements: 60,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./"),
    },
  },
});
