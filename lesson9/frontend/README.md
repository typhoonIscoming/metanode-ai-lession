# Frontend — Polymarket BTC 套利信号工具

> Next.js 16 (App Router) + TypeScript strict + Tailwind 4 + shadcn/ui + TanStack Query

详细需求与设计见 `../frontend-PRD.md`。

## 本地开发

前置：Node 22+、pnpm 10+。

```bash
pnpm install
cp .env.example .env.local   # 已默认指向 http://localhost:8000/api/v1
pnpm dev                     # http://localhost:3000
```

`/` 自动 redirect 到 `/dashboard`。

## 脚本

```bash
pnpm dev            # 开发服务器（Turbopack）
pnpm build          # 生产构建
pnpm start          # 跑生产构建
pnpm lint           # eslint
pnpm typecheck      # tsc --noEmit
pnpm format         # prettier --write .
pnpm format:check   # prettier --check .
pnpm test           # vitest 一次性
pnpm test:watch     # vitest watch
pnpm test:coverage  # vitest + 覆盖率
```

## 目录结构

```
app/                Next.js App Router 路由
  layout.tsx        全站布局 + Toaster
  page.tsx          → redirect /dashboard
  dashboard/        仪表盘（F-04）
  markets/[id]/     市场详情（F-05）
  predict/          手动预测（F-06）
  history/          推送历史（F-07）
  settings/         设置（F-08）
components/
  ui/               shadcn/ui 原子组件（勿改源码）
  …                 业务组件（F-03 起补齐）
lib/
  api.ts            apiFetch 封装，注意 NEXT_PUBLIC_API_BASE 已含 /api/v1 前缀
  format.ts         数字 / 百分比格式化
  time.ts           UTC ↔ 本地化
  schemas.ts        Zod schema（对齐 backend Pydantic）
  utils.ts          shadcn cn() 工具
hooks/              TanStack Query hooks（F-02 起补齐）
tests/              Vitest + RTL
```

## 与后端契约

- 所有 API 走 `NEXT_PUBLIC_API_BASE`，默认 `http://localhost:8000/api/v1`
- **path 写相对路径**：`apiFetch("/markets")`，**不要**写 `/api/v1/markets`
- 后端 Phase 0：GET 列表返空 success / `/markets/{id}` 返 404 / POST 写路径返 422 / `/settings` 真实数据

## 注意

- v1 全 Client Components（`"use client"`）
- 时间一律 UTC 存、本地化展示，tooltip 显示 UTC 原值
- 代码注释与字符串文案中文；标识符英文
- 不做暗色模式（sonner Toaster 固定 light 主题）

## 容器化

```bash
docker build -t polymarket-arb-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_BASE=http://backend:8000/api/v1 polymarket-arb-frontend
```

接入 docker-compose 的 placeholder 留给 backend 的 B-03。
