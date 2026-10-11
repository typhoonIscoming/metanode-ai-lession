# Web3 Career — 一次 Vibe-Coding 的全记录

> 课程视频回放（Lesson 8）：[点击观看](https://appibxs98ig9955.h5.xet.pomoho.com/p/course/video/v_6a2b06a9e4b0694c5bd52a59?product_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&course_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&sub_course_id=subcourse_3EUmreviThPpAUC2IJ1NTqoDbk5)

一个仿照 [web3.career](https://web3.career/) 的 Web3 招聘聚合平台 v0.2 原型。

从空目录开始，**全程用 AI Pair Programming（Claude Code + superpowers 工作流）走完调研、PRD、设计、实现、调优**——一共 49 个 commit，3 个版本迭代，最后落地一个**可登录、可发岗位、有 3D 沉浸感**的可运行 demo。

---

## 看起来是什么样

打开 http://localhost:3000，你会看到：

- 全屏流动的 **WebGL shader 渐变背景**（紫 → 青 → 绿，时间维度漂移）+ 上层动态网格
- Hero 区右半边一颗旋转的 **wireframe 二十面体** + 7 个浮动青色小立方体
- 卡片**鼠标跟随 3D 倾斜**（±8°）+ 高光扫过
- 配色霓虹深色 + glassmorphism 玻璃卡 + 全息渐变文字（"web3 builders" 三色彩虹）
- `/salaries` 上一段**真实数据驱动的 3D 立体柱状图**（取 Top-10 角色的薪资上限）

数据全部从 Postgres 实时取，不是死页面。

---

## 技术栈

| | |
| --- | --- |
| **前端** | Next.js 15 (App Router, RSC 默认) · React 19 · TypeScript strict · Tailwind v4 · three.js + @react-three/fiber + @react-three/drei |
| **后端** | NestJS 11 · Prisma 6 · Postgres 16 · class-validator · @nestjs/jwt · bcryptjs · zod (env 校验) |
| **基建** | Docker Compose · pnpm 10 · 模块化单体（后端按 PRD 微服务边界做内部模块，留好后续拆分接缝） |

---

## 快速开始

```bash
# 1. 启动 Postgres（容器内 5432 → 宿主 5434，避开本机已有 postgres）
docker compose up -d postgres

# 2. 装后端 + 跑迁移 + 灌种子数据 + 启动 API
cd backend
cp .env.example .env
# .env 已经把 DATABASE_URL 指到 localhost:5434
pnpm install
pnpm prisma migrate dev --name init
pnpm db:seed                # 灌入 22 个 tag / 5 家公司 / 20 个岗位 / 10 篇文章 / 2 个 demo 账号
pnpm test                   # 4 个 AuthService 单测应该全绿
pnpm start:dev              # API: http://localhost:4000/v1

# 3. 装前端 + 启动（新开终端）
cd ../frontend
cp .env.local.example .env.local
pnpm install
pnpm dev                    # Web: http://localhost:3000
```

> 如果你宿主机 5432 没占用，可以把 `docker-compose.yml` 的 `5434:5432` 改回 `5432:5432`，然后用 `.env.example` 里的默认 URL。

---

## 演示账号（seed 后自动创建）

| 邮箱 | 密码 | 角色 | 关联公司 |
| --- | --- | --- | --- |
| `demo-candidate@web3career.local` | `password1` | candidate（候选人） | — |
| `demo-employer@web3career.local`  | `password1` | employer（雇主） | helios-protocol |

登录后 header 右上角会出现头像菜单（Dashboard / Browse jobs / Sign out），雇主多一项 **Post a job**。

---

## 项目结构

```
.
├── backend/                            NestJS 模块化单体
│   ├── prisma/
│   │   ├── schema.prisma               10 张表：users, refresh_tokens, tags, companies,
│   │   │                               jobs, job_tags, applications, bookmarks,
│   │   │                               subscriptions, articles
│   │   └── seed.ts
│   └── src/
│       ├── main.ts, app.module.ts, config/, prisma/, common/
│       ├── auth/                       JWT + refresh rotation + 4 unit tests
│       ├── jobs/                       list / detail / create（employer 才能 create）
│       ├── companies/, tags/, users/
│       ├── articles/                   /learn 页面的内容源
│       ├── salaries/                   实时聚合（按角色 / 级别 / Remote）
│       └── subscribe/                  Newsletter 订阅
├── frontend/
│   └── src/
│       ├── app/                        17 个公开路由
│       │   ├── page.tsx (首页, 含 HeroScene)
│       │   ├── jobs/, jobs/[slug]/
│       │   ├── companies/
│       │   ├── salaries/ (含 SalaryBars3D)
│       │   ├── learn/, learn/[slug]/
│       │   ├── login/, register/, dashboard/
│       │   ├── post-a-job/
│       │   └── about/, faq/, terms/, privacy/, advertise/, api/  ← 静态信息页
│       ├── components/
│       │   ├── site-header.tsx (+ auth-menu.tsx 客户端菜单)
│       │   ├── site-footer.tsx, grid-background.tsx
│       │   ├── job-card.tsx, tag-chip.tsx
│       │   ├── newsletter-form.tsx, stat-counter.tsx
│       │   ├── shader-bg.tsx           ← WebGL fragment shader 背景
│       │   ├── tilt.tsx                ← 鼠标 3D 倾斜包装器
│       │   ├── hero-scene.tsx          ← 首页 3D 场景
│       │   └── salary-bars-3d.tsx      ← /salaries 3D 柱状图
│       └── lib/
│           ├── api.ts (typed fetch + auth bearer)
│           ├── auth.ts (localStorage session + useSession hook)
│           └── format.ts, cn.ts
├── docker-compose.yml
├── PRD.md, frontend-PRD.md, backend-PRD.md       ← 原始 PRD 文档
└── docs/superpowers/
    ├── specs/                          设计 spec（brainstorming 输出）
    └── plans/                          实现 plan（writing-plans 输出，bite-sized 任务）
```

---

## 核心 API（全部公开端点）

```
# Auth
POST /v1/auth/register      { role, email, password, displayName?, companyName? }
POST /v1/auth/login         { email, password }
POST /v1/auth/refresh       { refreshToken }
GET  /v1/users/me           (auth required)

# Jobs
GET  /v1/jobs?tag=&remote=&q=&company=&sort=&page=&limit=
GET  /v1/jobs/:slug
POST /v1/jobs               (auth, employer 才能发)

# Companies / Tags
GET  /v1/companies?page=&limit=&q=
GET  /v1/companies/:slug
GET  /v1/tags?popular=true&category=&limit=

# v0.1 新增
GET  /v1/articles?category=&limit=        # /learn 页面数据
GET  /v1/articles/categories              # 各类内容计数
GET  /v1/articles/:slug
GET  /v1/salaries                         # 实时聚合：overall / byRole / bySeniority / byRemote

# 其它
POST /v1/subscribe          { email, firstName?, lastName?, source? }
```

---

## Vibe-Coding 历程

整个项目分**三个版本**完成，每次迭代都先走 superpowers 工作流（brainstorm → spec → plan → subagent 执行 → verify）。

### v0 · 骨架搭建（commit 1 – 28）

**目标**：从空目录到一个能跑的最小可用版本。

走完的流程：
1. **调研** — 用 WebFetch 扒了 web3.career 的首页、岗位列表、套餐页、FAQ、薪资页等多个真实页面，归纳出功能矩阵
2. **PRD 撰写** — 输出 `PRD.md` / `frontend-PRD.md` / `backend-PRD.md` 三份完整产品 + 技术规格（共 ~2400 行）
3. **明确范围** — 用户明确说"不要 web3 钱包功能"，把 SIWE/wagmi/钱包登录都从 PRD 砍掉，改为邮箱密码 + Magic Link + OAuth + TOTP 2FA
4. **`/superpowers:writing-plans`** — 把 v0 拆成 25 个 bite-sized 任务，每个任务都带完整代码
5. **`/superpowers:subagent-driven-development`** — 按 Phase 派发子代理（implementer → spec reviewer → quality reviewer）顺序执行
6. **端到端验证** — `pnpm install` / `prisma migrate` / `db:seed` / `pnpm test`（4 个绿） / curl 全部公开路由

交付：
- 后端：Auth + Jobs + Companies + Tags + Users + Subscribe 6 个模块
- 前端：首页 / 岗位列表 / 岗位详情 / 公司列表 / 登录 / 注册 / 404 一共 8 个页面
- 数据：22 tag · 5 公司 · 20 岗位 · 2 demo 账号
- 整套深色 crypto 主题（aurora 渐变 + 动态网格 + glassmorphism 卡 + 全息渐变标题）

### v0.1 · 修 bug + 把所有 404 补齐（commit 29 – 35）

**问题**：用户实际打开发现：
- 浏览器扩展（有道词典）注入 `data-yd-content-ready` 属性导致 hydration warning
- Salaries / Learn / Post-a-job / About / FAQ ... 等链接全是 404
- 登录后没跳转、header 不显示登录态、只甩一行调试文字

走完的流程：
1. **`/superpowers:systematic-debugging`** — 4 阶段诊断 hydration → 根因是浏览器扩展 → 给 `<html>` `<body>` 加 `suppressHydrationWarning`，顺手把 `SiteFooter` 里的 `Math.random()` 替换成稳定元素
2. **`/superpowers:writing-plans`** v0.1 patch — 把缺失能力拆成 4 阶段：
   - **2A 后端扩展**：加 `Article` 模型 + 迁移；新建 `articles` / `salaries` 两个模块；seed 注入 10 篇文章
   - **2B 前端 Auth 状态**：`lib/auth.ts` localStorage + `useSession` hook；`AuthMenu` 客户端菜单挂在 header；登录/注册成功后 `router.push('/dashboard')`；API client 自动注入 Bearer token
   - **2C 核心新页面**：`/dashboard` · `/salaries` · `/learn` · `/learn/[slug]` · `/post-a-job`
   - **2D 静态页 + 验证**：`/about` `/faq` `/terms` `/privacy` `/advertise` `/api` 6 个静态页 + 端到端 17 条路由 curl

交付：
- 全部 17 条公开路由 HTTP 200
- 完整登录 → 跳转 → 持久化 → 头像菜单 → 登出闭环
- 雇主能从 `/post-a-job` 真的发岗位（POST /v1/jobs，带 Bearer token）→ 跳到新岗位详情页

### v0.2 · 沉浸式 3D 升级（commit 36 – 49）

**目标**：用户嫌"页面还不够美观"，希望引入 3D 风格。

走完的流程：
1. **`/superpowers:brainstorming`** — 用 `AskUserQuestion` 给用户 3 档可选（轻量 CSS / Hero WebGL / 重型沉浸），用户选**重型沉浸** + wireframe 多面体几何风格
2. **写 spec** → `docs/superpowers/specs/2026-05-17-web3career-v0.2-3d-immersive-design.md`：4 个组件、性能预算、可访问性约束、prefers-reduced-motion 兜底
3. **`/superpowers:writing-plans`** → `docs/superpowers/plans/2026-05-17-web3career-v0.2-3d-immersive.md`：11 个 bite-sized 任务，4 个 phase
4. **subagent 派发** — 按 Phase 派发 4 批
5. **碰到的真实坑**：
   - Next 15 RSC 不允许 `dynamic({ ssr: false })` → 子代理自己拐了个弯：加一个客户端 mount 包装器（`hero-scene-mount.tsx` / `salary-bars-3d-mount.tsx`）
   - `@react-three/drei@9` 跟 React 19 + fiber v9 peer 冲突 → 升级 drei 到 v10（fiber 保留 v9）
   - WSL2 文件 watch 不触发 HMR → 重启时加 `WATCHPACK_POLLING=true`

交付：
- **ShaderBg** (`shader-bg.tsx`)：纯 WebGL（无 three.js 依赖）的 fragment shader 全屏背景，紫/青/绿 fbm 噪声，~4KB
- **Tilt** (`tilt.tsx`)：客户端鼠标位置驱动 perspective 倾斜，附带"光斑"高光，应用于 5 类卡片共 ~50 个实例
- **HeroScene** (`hero-scene.tsx`)：r3f Float 包裹的紫色 wireframe 二十面体 + 7 个青色 wireframe 小立方体，缓速自转，仅桌面端
- **SalaryBars3D** (`salary-bars-3d.tsx`)：drei `<Billboard>` + `<Text>` 包装的 3D 柱阵，文字始终面对相机，数据从 `/v1/salaries` 实时来
- **v0.2 一处 polish 修复**：用户反映柱状图标签遮挡 → Billboard 化、间距 0.95 → 1.2、容器 360px → 480px、相机后撤、删冗余 wireframe 层、文字加 outline 描边

性能：r3f 只在 `/` 和 `/salaries` 加载（dynamic ssr:false），其它 15 条路由 0 包体；prefers-reduced-motion 全部组件自动静音。

---

## 用到的 Superpowers 工作流

整个项目严格按以下技能链推进：

| 阶段 | 技能 | 作用 |
| --- | --- | --- |
| 创意起点 | `superpowers:brainstorming` | 提多个方向 + AskUserQuestion 确认 → 落 spec |
| 出实现计划 | `superpowers:writing-plans` | spec 拆成 bite-sized 任务，每步带完整代码、无占位符 |
| 执行 | `superpowers:subagent-driven-development` | 每任务派子代理（implementer + spec reviewer + quality reviewer 两阶段评审） |
| 修 bug | `superpowers:systematic-debugging` | 四阶段（root cause → pattern → hypothesis → impl）系统排查，禁止瞎试 |

主会话只做**调度 + 审阅**，繁重的多文件实现工作全部派给子代理（用 haiku 模型节约成本，关键判断节点用 sonnet）。

---

## 后续可以做但 v0.2 没做

| 方向 | 备注 |
| --- | --- |
| 真实爬虫（Greenhouse / Lever / Ashby ATS） | backend-PRD §8 已设计 |
| Stripe 信用卡发岗位计费 | backend-PRD §11 已设计 |
| Elasticsearch 全文检索替代 Postgres `ILIKE` | backend-PRD §9 |
| Admin Console（订单 / 用户 / 内容审核） | backend-PRD §3 / §16 |
| 国际化（中/英/日/韩） | next-intl + 现有 i18n 字串集中提取 |
| 2FA TOTP UI 流程 | 后端已就绪，仅缺前端绑定/校验页 |
| 鼠标拖尾粒子 / 滚动驱动相机视差 | v0.3 视觉再升级候选 |

---

## 设计文档索引

| 文件 | 内容 |
| --- | --- |
| `PRD.md` | 总览 PRD（产品定位 / 角色 / 信息架构 / 商业化 / 里程碑） |
| `frontend-PRD.md` | 前端技术 PRD（设计系统 / 路由 / 状态 / 数据 / SEO / 测试） |
| `backend-PRD.md` | 后端技术 PRD（微服务划分 / 数据模型 / API / 安全 / 部署） |
| `docs/superpowers/specs/2026-05-17-web3career-v0.2-3d-immersive-design.md` | v0.2 3D 升级设计 spec |
| `docs/superpowers/plans/2026-05-17-web3career-v0.md` | v0 骨架 25 任务实现计划 |
| `docs/superpowers/plans/2026-05-17-web3career-v0.1-interactivity.md` | v0.1 互动补丁 4 阶段实现计划 |
| `docs/superpowers/plans/2026-05-17-web3career-v0.2-3d-immersive.md` | v0.2 3D 升级 11 任务实现计划 |

---

## 一句话总结

> 这是一份「**人提需求 / 改方向，AI 写代码 / 调试 / 评审**」的协同实践 —— 49 个 commit 跑出一个可登录、可发岗位、有 3D 沉浸感的全栈 Web3 招聘平台原型。
