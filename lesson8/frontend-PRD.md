# Web3 Career 复刻项目 — 前端 PRD

> 版本：v1.0
> 编写日期：2026-05-17
> 关联文档：`PRD.md`、`backend-PRD.md`
> 目标读者：前端工程师、设计师、QA

---

## 0. 范围声明

本文档定义**所有面向浏览器/移动 Web** 的实现细节，包括：

- 公开站点（访客 + 求职者 + 雇主访问的页面）
- 求职者控制台
- 雇主控制台
- 管理后台（Admin Console）
- 共享组件、状态管理、数据请求层、SEO、性能、A11y、测试

**不包含**：移动原生 App（v1 内 PWA 即可）、Storybook 内部细节文档（独立维护）。

---

## 1. 技术栈

| 层 | 选型 | 理由 |
| --- | --- | --- |
| 框架 | **Next.js 15（App Router）+ React 19** | 内置 SSR/ISR，App Router 支持流式渲染、Server Components |
| 语言 | **TypeScript 5.x（strict）** | 大型项目类型安全必须 |
| 样式 | **Tailwind CSS 4 + CSS Variables** | 原子化 + 通过 CSS 变量实现主题切换 |
| UI 组件 | **shadcn/ui + Radix Primitives** | 无样式可访问的底座 + 自定义视觉 |
| 图标 | **Lucide Icons + Phosphor**（互补）| Web3 行业标识 |
| 表单 | **React Hook Form + Zod** | 高性能 + Schema 与后端共享 |
| 富文本 | **TipTap 2.x**（输出 HTML + Markdown） | 现代化扩展生态 |
| 图表 | **Recharts + Visx** | 薪资趋势、漏斗 |
| 国际化 | **next-intl** | App Router 原生支持 |
| 状态 | **React Server Components（默认）+ Zustand（轻量客户端态）** | 避免 Redux 复杂度 |
| 客户端缓存 | **TanStack Query v5** | 适合 dashboard 区域 |
| 鉴权（前端） | **NextAuth.js v5 + JWT Refresh** | 支持邮箱密码、Magic Link、Google/GitHub OAuth |
| 支付 | **Stripe.js Checkout（v1）**；v1.1 预留加密托管网关 | |
| 测试 | **Vitest（单元）+ Testing Library（组件）+ Playwright（E2E）+ Storybook（视觉回归）** | |
| Lint/格式化 | **Biome + ESLint Edge Rules** | 性能优于 ESLint + Prettier |
| 包管理 | **pnpm 9 + Turborepo** | 多包工作流 |
| 部署 | **Vercel（主）/ 自托管 K8s（备）** | |

---

## 2. 仓库与代码组织

### 2.1 Monorepo 结构（Turborepo）
```
web3career/
├── apps/
│   ├── web/                # 主前端站点（Next.js）
│   ├── admin/              # 管理后台（独立部署，子域名）
│   └── docs/               # API 文档站（Nextra / Mintlify）
├── packages/
│   ├── ui/                 # 通用 UI 组件（shadcn 扩展）
│   ├── eslint-config/
│   ├── tsconfig/
│   ├── icons/              # 自定义 SVG 图标
│   ├── api-client/         # 后端 API SDK（含 zod schema 共享）
│   ├── schemas/            # 与后端共享的 Zod 模型
│   ├── tracking/           # 埋点 SDK 包装（PostHog）
│   ├── auth/               # NextAuth 共享配置
│   └── i18n/               # 翻译文件
├── e2e/                    # Playwright 用例
├── .github/workflows/      # CI
├── turbo.json
└── pnpm-workspace.yaml
```

### 2.2 apps/web 内部结构
```
app/
├── (marketing)/            # 营销与公开页面分组
│   ├── layout.tsx          # 顶导+底导
│   ├── page.tsx            # 首页 /
│   ├── jobs/
│   │   ├── page.tsx        # /jobs 列表
│   │   └── [slug]/page.tsx # 详情
│   ├── (tags)/[tag]-jobs/page.tsx     # 动态 tag 聚合 /solidity-jobs
│   ├── companies/
│   ├── salaries/
│   ├── learn/
│   ├── api/                # /api 营销页
│   └── advertise/
├── (auth)/
│   ├── login/
│   ├── register/
│   └── forgot-password/
├── (candidate)/
│   ├── layout.tsx          # 求职者侧栏
│   ├── dashboard/
│   ├── saved/
│   ├── applied/
│   ├── alerts/
│   └── profile/
├── (employer)/
│   ├── layout.tsx          # 雇主侧栏
│   ├── dashboard/
│   ├── jobs/
│   │   ├── new/            # 发布岗位向导
│   │   └── [id]/edit/
│   ├── bundle/
│   ├── talent-pool/
│   ├── billing/
│   └── team/
├── api/                    # Route Handlers（仅 BFF：文件上传、OAuth 回调、Magic Link、webhook 转发）
├── sitemap.ts
├── robots.ts
├── opensearch.xml
└── global-error.tsx
```

### 2.3 模块边界约定
- **Server Component 默认**：列表、详情、SEO 文案、聚合页全部 RSC。
- **Client Component 仅用于交互**：表单、Tab、Modal、Drawer、Slider。
- **数据访问层**：`packages/api-client` 暴露 typed fetcher；RSC 中直接 `await getJobs(...)`；客户端组件用 `useJobs()` 包装的 TanStack Query Hook。
- **禁止**直接在组件里 `fetch(...)`。

---

## 3. 设计系统

### 3.1 Design Tokens

```ts
// packages/ui/tokens.ts
export const colors = {
  primary: {
    50: '#EFF6FF', 100: '#DBEAFE', 200: '#BFDBFE', 300: '#93C5FD',
    400: '#60A5FA', 500: '#3B82F6', 600: '#1F6FEB', 700: '#1D4ED8',
    800: '#1E40AF', 900: '#1E3A8A',
  },
  accent: { 500: '#FF7A00', 600: '#EA580C' },        // 主 CTA / 强调
  success: '#16A34A',
  warning: '#F59E0B',
  danger: '#DC2626',
  gray: { 50: '#FAFAFA', 100: '#F3F4F6', 200: '#E5E7EB',
          300: '#D1D5DB', 400: '#9CA3AF', 500: '#6B7280',
          600: '#4B5563', 700: '#374151', 800: '#1F2937',
          900: '#111827', 950: '#030712' },
};

export const radii   = { sm: 4, md: 8, lg: 12, xl: 16, full: 9999 };
export const shadows = { sm:'0 1px 2px rgb(0 0 0 / .05)',
                         md:'0 4px 6px -1px rgb(0 0 0 / .1)',
                         lg:'0 10px 15px -3px rgb(0 0 0 / .1)' };
export const fontFamily = {
  sans: 'Inter, "Helvetica Neue", Arial, sans-serif',
  mono: 'JetBrains Mono, ui-monospace',
};
export const fontSize = { xs:12, sm:14, base:16, lg:18, xl:20,
                          '2xl':24, '3xl':30, '4xl':36, '5xl':48 };
export const spacing = { 1:4, 2:8, 3:12, 4:16, 5:20, 6:24, 8:32, 10:40, 12:48, 16:64, 20:80 };
```

### 3.2 主题
- **Light（默认）** + **Dark**（通过 `class="dark"`）。
- 系统跟随：`prefers-color-scheme`；用户可在 Header 切换并写入 `localStorage`。

### 3.3 组件库分层（Atomic Design）

#### Atoms
`Button / Input / Textarea / Select / Switch / Checkbox / Radio / Slider / Badge / Tag / Avatar / Logo / Spinner / Skeleton / Divider / Icon / Link`

#### Molecules
`SearchBar / Pagination / Breadcrumb / Tabs / Accordion / Dropdown / Modal / Drawer / Toast / Tooltip / EmptyState / RangeSlider(Salary) / FormField / FileUploader / TagChip / FilterPill / CopyButton / SocialLoginButton`

#### Organisms
`JobCard / CompanyCard / SalaryTable / FilterPanel / JobDetailHeader / ApplyDialog / NewsletterSignup / TestimonialCard / FeaturedJobsCarousel / CityGrid / LogoWall / PricingTable / BundleSelector / AddOnSelector / DashboardSidebar / ApplicationTable / ResumeBuilder / JobPostingStepper`

#### Templates
`MarketingLayout / DashboardLayout / AuthLayout / AdminLayout / ListingTemplate / DetailTemplate`

#### Pages
具体路由组件，仅做数据组合，不写样式。

### 3.4 Storybook 约定
- 每个组件强制 3 类 Story：`Default / All States / In Page Context`。
- 通过 `chromatic` 做视觉回归；PR 阶段对比。

---

## 4. 路由与页面规格

> 完整路由参考 `PRD.md §3.1`。本节定义每个页面的**数据需求 / 组件构成 / 状态 / 交互细节 / SEO**。

### 4.1 首页 `/`
- **数据**：`GET /v1/stats`、`GET /v1/jobs?sort=featured&limit=12`、`GET /v1/jobs?sort=recent&limit=20`、`GET /v1/tags?popular=true&limit=60`、`GET /v1/companies?top=true&limit=20`、`GET /v1/salaries/snapshot`。
- **渲染**：RSC + ISR 60s。
- **组件**：`HeroBanner`（含 `NewsletterSignup`）、`StatsRow`、`TagCloud`、`FeaturedJobsCarousel`、`AdBanner（可空）`、`LatestJobsList`、`BootcampPromo`、`CategoryGrid`、`SalarySnapshot`、`CityGrid`、`RegionGrid`、`LearnHub`、`FAQAccordion`、`TestimonialList`、`Footer`。
- **交互**：
  - 邮件订阅：客户端 `react-hook-form` + Zod；提交后 `POST /v1/subscribe`，成功显示 Toast，失败显示行内错误。
  - "Show all tags" 切换：点击展开/收起，状态保存在 `useState`。
  - Latest Jobs 区每 30s `revalidatePath('/')` 触发（v1 用 ISR；v1.1 改 WebSocket）。
- **SEO**：H1 = "Web3 Jobs - {dynamic count} blockchain & crypto jobs"；`og:image` 自动生成（`/api/og`）。

### 4.2 岗位列表 `/jobs` 及 `/{tag}-jobs`
- **路由动态生成**：tag 列表由 `generateStaticParams()` 预生成 Top 200 tag；剩余 ISR 600s。
- **URL 状态**：所有筛选写入 query（`?tag=rust&remote=1&salary_min=80000&sort=salary`）；使用 `useSearchParams` + `nuqs` 同步。
- **组件**：
  - `ListingHeader`（H1、副标题"{Month Year} ({N} new)"、可折叠 SEO 文案）。
  - `FilterPanel`（顶部 sticky；移动端 Drawer）。
  - `JobList`（无限滚动 + 分页双模式，默认页码以便 SEO）。
  - `Sidebar`（PC ≥ 1280px）：`RelatedTags`、`TopCompaniesByTag`、`PostJobCTA`。
  - `Footer`：`RelatedTagsCloud`（SEO 互链）。
- **筛选项**：
  - Search input（debounce 300ms，提交 `q=`）。
  - Remote 开关。
  - Location 多选（Combobox + 国家分组）。
  - Salary slider $0–$500k step $5k。
  - Seniority、Employment Type、Posted within (7/30/90)、Benefits、Chain。
- **排序**：`recent / salary / popularity`。
- **交互细节**：
  - 卡片悬停 0.2s 后展开摘要（前 240 字）。
  - 心形收藏：未登录 → 弹注册引导（保留 referrer，登录后回到此页并自动收藏）。
- **SEO**：每 tag 页独立 H1 / canonical / `JobPosting` JSON-LD 集合标签。

### 4.3 岗位详情 `/jobs/{slug}-{id}`
- **数据**：`GET /v1/jobs/{id}`、`GET /v1/jobs/{id}/related?type=same_company&limit=5`、`GET /v1/jobs/{id}/related?type=same_tag&limit=10`。
- **布局**：12 栅格，左 8（主内容）+ 右 4（吸顶 Apply 卡）；< 1024px 切换为单列，Apply 卡固定底部。
- **主内容**：`JobDetailHeader`（Logo + 标题 + 元信息 + Apply CTA） → `JobDescription`（Markdown 渲染） → `BenefitsBlock` → `CompanyBlock`（同公司其它岗） → `RelatedJobs`。
- **Apply 行为**：
  - `apply_type=external_url`：点击调 `POST /v1/applications/click` 埋点 → `window.open(apply_url, '_blank')`。
  - `apply_type=internal`：打开 `ApplyDialog`（候选人未登录则切到登录注册标签）。
- **辅助交互**：
  - Share 按钮：Web Share API 优先；不支持则下拉菜单（Twitter / LinkedIn / Discord webhook / Copy link）。
  - Report：弹 `ReportDialog`（原因下拉 + 描述 textarea）。
  - 阅读进度条（滚动百分比）。
- **SEO**：JSON-LD `JobPosting` 字段完整（title, description, datePosted, validThrough, employmentType, hiringOrganization, jobLocation, baseSalary, applicantLocationRequirements）；OpenGraph 自动生成。

### 4.4 公司列表 `/companies`
- 类似岗位列表，但顶部展示 Top 100 计数 + 排序（在招岗位数 / 融资 / 平均薪资）。
- `CompanyCard` 字段：Logo、Name、Tagline、Industry、HQ、Team Size、Funding、Open Roles 计数、Avg Salary、`View Jobs →`。

### 4.5 公司详情 `/companies/{slug}`
- 顶部 `CompanyHero`（封面 + Logo + Tagline + 关注/Claim）。
- `Tabs`：Overview / Jobs (N) / Salaries / News / Reviews(v1.1)。
- `Overview`：左 8 列描述（Markdown）+ 右 4 列侧栏（社交、官网、融资轮、Founders、Tech Stack）。
- `Jobs` tab 复用 `JobList`。
- `Salaries` tab：`SalaryTable` + `SalaryDistributionChart`。
- `News`：聚合 RSS / Twitter 卡片流。

### 4.6 薪资页面 `/salaries` 及子页
- **顶部摘要**：4 块统计（avg、median、top 25%, sample size）。
- **三大表格**：
  - `SalaryByRoleTable`（可点击行进入子页）。
  - `SalaryByRegionTable`。
  - `SalaryBySeniorityTable`。
- **趋势图**：`SalaryTrendChart`（X=月，Y=USD，多 series 切换）。
- **底部相关**：Top jobs in this role / 链接到岗位列表。

### 4.7 求职者控制台 `/dashboard`
- **Sidebar**：5 个 Tab。
- **主区**：
  - Saved：表格视图 + 删除/添加备注（modal）。
  - Applied：申请记录 + 状态徽章 + 雇主消息 timeline。
  - Alerts：列表 + "New Alert" 按钮（弹 `AlertWizard`：Tag/Location/Salary/Frequency）。
  - Profile：分块表单（自动保存 throttle 1s）。
  - Resume：上传 PDF（拖拽 + 进度）或 Resume Builder（v1.1）。
  - Talent Pool Visibility：开关 + 解释 + 状态历史。

### 4.8 雇主控制台 `/employer/dashboard`
- 顶部 KPI Cards：今日浏览、Apply 点击、有效岗位数、Bundle 余额。
- **Jobs Table**：状态过滤 + 操作菜单（Edit / Pause / Repost / Boost / Delete）。
- **Job Form Wizard**（`/employer/jobs/new`）4 步：
  1. **Company**：公司信息（首次发布带引导填写；后续可复用）。
  2. **Job Details**：title、location、remote、main_skill、extra_tags、benefits、salary slider、description（TipTap 编辑器）。
  3. **Add-ons & Pricing**：可勾选项 `AddOnSelector`、Sticky 时长选择、合计实时计算。
  4. **Payment**：选择卡 / Crypto；Review；提交 → 跳支付。
- **进度条** + **Auto save**（每 30s 写草稿，刷新可恢复）。
- **Validations**：参考 `PRD.md §4.5.2`，所有错误内联显示。
- **Talent Pool Search**（付费功能）：高级筛选 + 候选人匿名卡（"View profile" 按钮触发计费记录）。
- **Billing**：发票列表、订阅/Bundle 余额、卡管理。
- **Team**：邀请同事（邮件邀请链接，24h 失效）。

### 4.9 Admin Console（独立子应用）
- 跑在 `admin.web3career.example`；走 SSO（Google Workspace）。
- 模块：Users / Companies / Jobs / Applications / Orders / Refunds / Crawlers / Newsletter / Tags / Content / Reports / Audit Log。
- 全部使用 `DataTable` 组件（TanStack Table + 服务器分页 + 列筛选 + 批量操作）。

### 4.10 鉴权页面
- `/login`：邮箱+密码主区；下方分隔线 + "Continue with Google / GitHub" 社交按钮；右下角 "Email me a login link" 触发 Magic Link 流程。
- `/register`：身份选择（求职者 / 雇主）后展开对应表单；雇主额外收集公司名 + 公司 URL。
- `/forgot-password`：邮箱 → 收到重置链接 → 设置新密码。
- Magic Link 流程：用户输入邮箱 → 后端发送一次性 token 链接（15min 有效）→ 用户点击 → 自动登录并跳回原页面。
- 2FA：雇主与管理员首次登录强制扫码绑定 TOTP（Authy / Google Authenticator）；后续每次登录额外输入 6 位动态码。

### 4.11 错误页 & 边界态
- `not-found.tsx` 通用 404，含"返回首页 / 搜索岗位"两个 CTA。
- `error.tsx` 5xx；展示 trace_id 便于用户复制反馈。
- 离线：Service Worker 缓存最近浏览的岗位详情（PWA）。

---

## 5. 状态管理

### 5.1 服务端态（Server State）
- **首选 RSC**：列表 / 详情等数据均通过 Server Component 拉取，不放入客户端。
- **客户端需要时**：使用 **TanStack Query v5**；统一 QueryClient 配置：
  - `staleTime: 60s`（列表）/ `staleTime: 5min`（详情）。
  - 401 自动尝试 `refresh token` 一次；失败跳 `/login?next=`。

### 5.2 客户端 UI 态（UI State）
- **小范围**：`useState` / `useReducer`。
- **跨组件**：`Zustand` slice（`useFiltersStore`、`useAuthStore`、`useThemeStore`）。
- **持久化**：`zustand/middleware/persist` + `localStorage`（仅 UI 偏好）。

### 5.3 表单态
- **React Hook Form + Zod**；所有 schema 放 `packages/schemas`，前后端共用。
- 错误显示策略：onBlur 校验 + onSubmit 全量校验；服务器返回的字段错误通过 `setError(name, ...)` 注入。

### 5.4 URL 同步
- 列表 / 搜索 / 筛选页统一使用 `nuqs`，约束所有可分享状态都在 URL；避免 React state 与 URL 失同步。

---

## 6. 数据请求层

### 6.1 SDK 设计
```ts
// packages/api-client/src/jobs.ts
export const jobsApi = {
  list: async (params: JobsListParams): Promise<JobsListResponse> =>
    request('/v1/jobs', { params }),
  detail: async (id: string) =>
    request(`/v1/jobs/${id}`),
  create: async (payload: CreateJobInput) =>
    request('/v1/jobs', { method: 'POST', body: payload }),
};
```
- 底层 `request()` 基于 `ofetch`；自动注入 `Authorization`、`X-Request-Id`、`Accept-Language`。
- 错误统一封装 `ApiError(code, message, fields)`，前端可直接 `instanceof` 判断。

### 6.2 渲染策略对照
| 路径 | 渲染 | 缓存 |
| --- | --- | --- |
| `/` | RSC + ISR 60s | CDN |
| `/jobs`、`/{tag}-jobs` | RSC + ISR 600s | CDN + 私有 query 不缓存 |
| `/jobs/{slug}-{id}` | RSC + ISR 5min + on-demand revalidate | CDN |
| `/companies`, `/salaries` | RSC + ISR 600s | CDN |
| `/learn/**` | RSC + ISR 3600s | CDN |
| `/dashboard/**`, `/employer/**` | RSC + 强制 dynamic（no-store） | 无 |
| `/api/**`（BFF） | Node runtime | 无 |

### 6.3 实时更新
- 雇主 dashboard 申请通知：Server-Sent Events `/v1/events?topic=employer.{id}`。
- 候选人 alert 通知：Push API + Web Notifications（v1.1）。

---

## 7. 鉴权与权限

### 7.1 会话
- **HTTP-only Cookie + JWT**：`access_token`（15min）、`refresh_token`（30d，旋转）。
- NextAuth.js 适配后端 `/v1/auth/...` 端点；不在本地存任何密码。
- 客户端不持久化敏感凭据；登录态仅通过 cookie 携带。

### 7.2 角色权限（前端守卫）
- `middleware.ts` 拦截 `/employer/**`、`/dashboard/**`、`/admin/**`；缺少角色 → 重定向。
- 组件级：`<Authorize roles={["employer.owner"]}>...</Authorize>` 包裹敏感按钮。

### 7.3 2FA 二次校验
- 雇主与管理员登录后若未启用 2FA，引导扫码绑定；管理操作（删除岗位、申请退款、修改账单）触发 step-up 验证（重新输入 TOTP）。

---

## 8. 国际化与本地化

- 文案 key 集中在 `packages/i18n/locales/{en,zh,es,fr,ja,ko}/*.json`，模块化拆分（`common.json`、`jobs.json`、`employer.json` ...）。
- `next-intl` 中间件根据 `Accept-Language` 自动选择；用户切换写入 cookie `NEXT_LOCALE`。
- 数字 / 货币：`Intl.NumberFormat`；日期：`date-fns` + 用户时区。
- URL 策略：v1 不带语言前缀（提升 SEO，单 hreflang），v1.1 引入 `/{lang}/...` 子路径。
- 富文本内容（岗位描述、学习文章）保持原语言，不机器翻译；前端展示原文 + 可选翻译按钮（v1.1）。

---

## 9. SEO

### 9.1 页面级
- 每页 RSC 内导出 `generateMetadata()`：动态 title、description、canonical、`alternates.canonical`、`openGraph`、`twitter`。
- Hero 区 H1 严格唯一。
- 重要数字写入 H1（如 `74,396 Web3 Jobs`），后端提供 stats。

### 9.2 结构化数据
- 岗位详情：`JobPosting` JSON-LD。
- 公司详情：`Organization` + `BreadcrumbList`。
- FAQ 页：`FAQPage`。
- 学习文章：`Article` + `Author`。

### 9.3 站点级
- `app/sitemap.ts` 动态生成 sitemap，按 50k 上限分片；每页带 `lastmod`、`changefreq`、`priority`。
- `robots.ts`：允许公开页，禁 `/dashboard`、`/employer`、`/admin`、`/api`。
- `OpenSearch` 接入浏览器搜索栏。

### 9.4 内部链接
- 列表底部 "Related Tags / Cities / Companies" 互链。
- 详情页右栏 "Similar Jobs / Same Company"。
- 学习文章插入相关岗位卡。

### 9.5 速度
- `next/image` 全站强制；Logo 用 `<Image priority={false} />`；Hero 图 priority。
- 字体：`next/font` self-host Inter；JetBrains Mono 仅在代码块按需加载。
- 关键 CSS inline，其余 lazy。

---

## 10. 性能预算

| 指标 | 目标 | 监控 |
| --- | --- | --- |
| LCP（首页） | ≤ 2.0s @ 4G Slow | RUM + Lighthouse CI |
| INP | ≤ 200ms | RUM |
| CLS | ≤ 0.05 | RUM |
| JS bundle（首页 First Load） | ≤ 180 KB gzip | bundle-analyzer CI 阻断 |
| 图片总大小 | ≤ 500 KB | CI 校验 |
| Number of requests | ≤ 50 | RUM |

### 10.1 优化手段
- React Server Components 默认 0 JS。
- 第三方脚本通过 `next/script` 的 `lazyOnload`；支付 SDK（Stripe.js）仅在结算页路由动态 `import()`。
- 富文本编辑器仅在雇主控制台动态加载。
- 图标：仅 `tree-shake` 当前页用到的 lucide icon。
- 缓存：`cache-control: public, max-age=0, s-maxage=60, stale-while-revalidate=600`。

---

## 11. 可访问性（WCAG 2.2 AA）

- 所有交互组件基于 Radix（焦点管理 + ARIA）。
- 颜色对比：亮色 / 暗色主题分别通过 `axe` CI 校验 ≥ 4.5。
- 键盘可达：Tab 顺序遵循文档流；模态打开后 focus trap，关闭后恢复 trigger 焦点。
- 表单 label：所有 `<label htmlFor>` 与 `<input id>` 一一对应；错误信息 `aria-describedby`。
- 跳过链接：`Skip to content`。
- 图片 alt：Logo 写公司名；装饰性 `alt=""`。
- 媒体：视频提供字幕；音频提供转录。

---

## 12. 错误处理与边界态

- **网络错误**：Toast + retry 按钮；保留用户输入。
- **服务降级**：搜索失败时 fallback 到普通列表；薪资数据失败显示"Data temporarily unavailable"。
- **空状态**：每个列表组件强制实现 `EmptyState`（图 + 文 + CTA）。
- **加载态**：Skeleton 优先于 Spinner；至少 200ms 闪现保护。
- **离线**：PWA Service Worker 缓存上次浏览的 5 个详情页 + 静态资源；离线访问显示"Showing cached version (offline)"标签。

---

## 13. 埋点与分析

### 13.1 工具
- **PostHog（自托管）** 处理事件、Funnel、Session Recording（仅雇主控制台开启录屏）。
- **Plausible（公开页）** 轻量 PV 统计，无 cookie，GDPR 友好。

### 13.2 关键事件
| 事件 | 触发时机 | 关键属性 |
| --- | --- | --- |
| page_view | 路由变化 | path, referrer, locale |
| job_card_view | 卡片进入视口 ≥ 500ms | job_id, tag, position_in_list |
| job_apply_click | Apply 点击 | job_id, source(list/detail), apply_type |
| job_save | 收藏 | job_id |
| filter_change | 筛选 | filter_name, value |
| signup_started | 注册首步 | role |
| signup_completed | 注册完成 | role, method(email_password / magic_link / oauth_google / oauth_github) |
| job_post_started | 雇主进入向导 | |
| job_post_step | 每完成一步 | step, errors_count |
| checkout_initiated | 进入支付 | amount, items |
| payment_succeeded | 支付成功 | order_id, method |
| api_key_generated | API key 创建 | plan |

### 13.3 隐私
- 不采集 IP 全段、不采集 email；user_id 用 hashed id。
- Session Recording 自动遮罩输入 / Resume 区域。
- 提供 Cookie Banner（必要 / 分析 / 营销 分级），默认 Opt-in 营销。

---

## 14. 测试策略

### 14.1 单元测试（Vitest）
- 工具函数、Zod schema、Hook、Reducer。覆盖率 ≥ 80% lines。

### 14.2 组件测试（Testing Library）
- 每个 Molecule / Organism 至少 3 个测试：渲染 / 交互 / a11y（`toHaveNoViolations`）。

### 14.3 E2E（Playwright）
- 关键用户旅程（每条都跑 Chromium + Webkit + Mobile Chrome）：
  1. 访客浏览岗位 + 申请外链
  2. 访客订阅 newsletter
  3. 求职者邮箱密码注册 + 收藏 + 申请 internal form
  4. 求职者 Magic Link 登录
  5. 雇主 Google OAuth 注册 + 启用 2FA
  6. 雇主发布岗位 + Stripe 支付（test mode）+ 增值项叠加
  7. 雇主购买 Bundle + 后续发布消耗额度
  8. Admin 审核岗位 + 退款流程
- 失败截图 + trace 自动上传 Vercel artifact。

### 14.4 视觉回归（Chromatic）
- Storybook 中每个组件，PR 阶段比对像素差 > 0.1% 阻断。

### 14.5 性能与 SEO
- Lighthouse CI（github action）：首页、列表、详情 3 个页面，每项指标分数 < 阈值则 PR 阻断。
- `next build` 自带的 `Web Vitals` 报告留档。

---

## 15. 构建与部署

### 15.1 环境
- `development`：本地，Mock 数据可选。
- `preview`：每个 PR 自动部署到 Vercel Preview，连预发 API。
- `staging`：长期分支 `develop` 自动部署。
- `production`：`main` 分支手动 promote。

### 15.2 CI/CD（GitHub Actions）
流程：
1. `pnpm install` (cache)
2. `pnpm lint && pnpm typecheck`
3. `pnpm test` (Vitest + Testing Library)
4. `pnpm build` (turbo cache)
5. Lighthouse CI / Playwright（仅 main / preview）
6. Bundle size 检查（`next-bundle-analyzer` + diff）
7. 部署 Vercel

### 15.3 Feature Flags
- `unleash` 或 `GrowthBook`；前后端共用。每个新功能用 flag 包裹，灰度 5% → 25% → 100%。

---

## 16. 响应式与移动端

### 16.1 断点（Tailwind 默认 + 自定义）
- `xs: 0`、`sm: 640`、`md: 768`、`lg: 1024`、`xl: 1280`、`2xl: 1536`。
- 列表卡片：< md 单列；md-lg 双列；≥ xl 单列（与侧栏并排）。

### 16.2 移动端专属优化
- 顶部导航折叠为汉堡 + Always-visible `Post a Job` 按钮。
- 详情页 Apply 按钮固定底部（80px 高，避免 iOS safe-area 遮挡）。
- 触摸目标 ≥ 44×44。
- 筛选改为 Drawer 弹出。
- 表单字段一行一项；键盘类型对应（email、tel、number）。

### 16.3 PWA
- `manifest.webmanifest` + Service Worker（next-pwa）。
- 离线缓存策略：详情页 stale-while-revalidate；静态资源 cache-first。
- "Add to Home Screen" prompt 在首次访问 ≥ 3 分钟后弹出。

---

## 17. 文件上传与媒体

- **Logo**：≤ 2MB，自动 webp 转码；存 S3，CDN 分发。
- **简历**：≤ 5MB PDF；客户端先 PDF Magic Number 校验；服务器再扫病毒（ClamAV）。
- **文章封面**：≤ 5MB，强制 16:9。
- **上传组件**：`Uppy`，支持拖拽 + 暂停续传。

---

## 18. 法律 / 合规组件

- Cookie Banner：`@klaro/web` 或自研；分类（必要 / 分析 / 营销）。
- GDPR 数据下载 / 删除按钮在 Profile → Privacy。
- Terms / Privacy / Cookie Policy 静态页（MDX，方便律师审核）。

---

## 19. 开发者体验

### 19.1 本地启动
```
pnpm install
cp .env.example .env.local
pnpm dev          # turbo 启动所有 apps
```

### 19.2 环境变量约定
- `NEXT_PUBLIC_API_URL`、`NEXT_PUBLIC_POSTHOG_KEY`、`NEXT_PUBLIC_STRIPE_PK`...
- 仅前缀 `NEXT_PUBLIC_` 的变量可暴露至客户端。
- `zod` 校验 `process.env`，启动即失败。

### 19.3 Mock API
- 开发模式可设 `USE_MSW=1` 启用 Mock Service Worker，加速 UI 迭代。

### 19.4 代码规范
- Conventional Commits + commitlint。
- Husky pre-commit：`lint-staged` 跑 biome + 测试相关文件。
- 文件命名：组件 `PascalCase`，工具 `camelCase`，目录 `kebab-case`。

---

## 20. 关键页面线框（文字版）

### 20.1 首页（PC 1440px）
```
┌──────────────────────────────────────────────────────────────┐
│ Logo  Home Salaries Internships Learn Top Hire API Adv [Post]│
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   H1: Browse 74,396 Web3 Jobs                                │
│   sub: Blockchain, Smart Contracts, Crypto                   │
│   [First name][Last name][Email]  [Subscribe]                │
│   Logo wall: Uniswap  Polygon  ConsenSys ...                 │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│   [ai] [solidity] [rust] [backend] [marketing] ... +Show all │
├──────────────────────────────────────────────────────────────┤
│   Featured Jobs                                              │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│   │JobCard 1│ │JobCard 2│ │JobCard 3│ │JobCard 4│ → carousel │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
├──────────────────────────────────────────────────────────────┤
│   Latest Jobs (20)                                           │
│   ──────────────────────────────────────────────────────     │
│   [Logo] Rust Engineer  Hibachi  Remote  $150k-200k  9h →    │
│   [Logo] Threat Analyst TRMLabs  DC,US   $83k-93k    15h →   │
│   ...                                                        │
├──────────────────────────────────────────────────────────────┤
│   Browse by Category | Top Cities | Top Regions              │
├──────────────────────────────────────────────────────────────┤
│   FAQ accordion                                              │
│   Testimonials                                               │
├──────────────────────────────────────────────────────────────┤
│   Footer (5 cols)                                            │
└──────────────────────────────────────────────────────────────┘
```

### 20.2 岗位详情（PC）
```
┌──────────── Header / Breadcrumb ────────────┐
│ Companies > Hibachi > Rust Engineer         │
├──────────────────────┬──────────────────────┤
│ [Company Logo big]   │   ┌──────────────┐   │
│ Rust Engineer        │   │  Apply Now   │   │
│ Hibachi · Remote     │   │  Save        │   │
│ $150k-200k · Rust    │   │  Share       │   │
│ Posted 9h ago        │   │              │   │
│                      │   │ Posted: 9h   │   │
│ ## About the company │   │ Location: RE │   │
│ ## The Role          │   │ Type: Full   │   │
│ ## Responsibilities  │   │ Salary: ...  │   │
│ ## Requirements      │   │ Tags: rust...│   │
│ ## Benefits          │   └──────────────┘   │
│ ## How to apply      │                      │
│                      │                      │
│ ### Similar Jobs     │                      │
│ Card · Card · Card   │                      │
└──────────────────────┴──────────────────────┘
```

---

## 21. 风险与权衡

| 风险 | 缓解 |
| --- | --- |
| RSC + ISR 调试体验差 | 完善日志 + Vercel preview + 本地 `next dev` 与生产一致 |
| 多语言增加包体 | 按 locale split + 动态加载 |
| 富文本编辑器（TipTap）体积较大 | 仅在雇主控制台路由动态 import |
| TipTap 升级破坏文章渲染 | 文章存 JSON 而非 HTML，渲染层独立适配版本 |
| 第三方支付脚本拖慢首屏 | 仅在结算页加载 |

---

## 22. 验收清单（前端 Done 标准）

- [ ] 所有页面通过 Lighthouse Performance ≥ 90、A11y ≥ 95、Best Practices ≥ 95、SEO ≥ 95。
- [ ] Storybook 覆盖 100% 自研组件，每组件至少 3 个 Story。
- [ ] E2E 关键 8 条用户旅程全部绿色。
- [ ] Bundle First Load JS ≤ 180 KB（首页）/ ≤ 220 KB（详情）。
- [ ] 所有表单具备 client + server 双层校验，错误信息 i18n。
- [ ] 主题切换、语言切换、登录态在所有路由保持一致。
- [ ] PWA 可安装，断网可访问最近 5 个详情页。
- [ ] 埋点全部接入 PostHog 且自测可见。
- [ ] 法律页（Terms / Privacy / Cookie）上线。
