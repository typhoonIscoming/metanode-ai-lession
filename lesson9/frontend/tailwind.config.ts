import type { Config } from "tailwindcss";

// Tailwind 4 主要通过 CSS 中的 @theme 配置；此文件保留是为了符合 PRD §2 目录约定与 shadcn/ui CLI 兼容
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
  ],
};

export default config;
