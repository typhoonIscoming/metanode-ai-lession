# Frontend — 市值热力图前端

基于 Next.js 15+ App Router + TypeScript + Tailwind CSS 的前端应用。

## 启动

```bash
# 安装依赖（首次）
npm install

# 复制环境变量配置
cp .env.local.example .env.local

# 启动开发服务器（默认 3000 端口）
npm run dev
```

浏览器访问 http://localhost:3000

## 环境变量

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE` | 后端 API 基础地址（REST + SSE 共用） | `http://localhost:8000` |

## 目录约定

- `app/`：App Router 页面与路由
- `types/`：与后端契约对齐的 TypeScript 类型定义
