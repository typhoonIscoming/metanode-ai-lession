# Web3 Career 复刻项目 — 后端 PRD

> 版本：v1.0
> 编写日期：2026-05-17
> 关联文档：`PRD.md`、`frontend-PRD.md`
> 目标读者：后端工程师、SRE、数据工程师、QA

---

## 0. 范围声明

本文档定义所有**服务器端**实现，包括微服务边界、数据模型、API 协议、爬虫、搜索、支付、通知、缓存、消息队列、可观测性、安全合规、部署与 CI/CD。

不在本文档：移动端、前端组件、营销文案。

---

## 1. 技术栈

| 层 | 选型 | 理由 |
| --- | --- | --- |
| 主语言 | **TypeScript（Node 22）** | 与前端共享 schema，团队熟悉 |
| 辅助语言 | **Python 3.12**（爬虫 / 数据聚合 / ML）、**Go**（高吞吐边缘服务，可选） | |
| 框架 | **NestJS 11**（HTTP + GraphQL + Microservices） | 模块化、装饰器、DI 丰富 |
| ORM | **Prisma 6** | 类型生成 + 多数据源 |
| 数据库 | **PostgreSQL 16**（主）、**Redis 7**（缓存/队列）、**Elasticsearch 8 / Meilisearch 1.x**（搜索）、**ClickHouse 24**（埋点 + 薪资聚合）、**S3 / Cloudflare R2**（对象存储） | |
| 消息队列 | **Kafka 3.7**（核心事件）、**BullMQ on Redis**（轻量异步任务） | |
| 任务调度 | **Temporal**（长流程 / 重试 / 工作流） + **node-cron / Prefect**（轻量定时） | |
| API 协议 | **REST + OpenAPI 3.1** 公开 + **gRPC** 服务间 + **GraphQL Yoga** 用于 BFF（可选） | |
| 认证 | **JWT（HS256→RS256 v1.1）+ Refresh Token Rotation**、**OAuth (Google/GitHub)**、**Magic Link**、**TOTP 2FA** | |
| 支付 | **Stripe**（信用卡 + Invoicing，v1）；v1.1 预留加密托管网关（NOWPayments / Coinbase Commerce） | |
| 邮件 | **Resend** + 自建 Newsletter | |
| 监控 | **Sentry**、**Grafana + Prometheus + Loki + Tempo**、**OpenTelemetry SDK** | |
| 部署 | **Kubernetes (EKS / GKE)** + **Helm** + **ArgoCD**（GitOps） | |

---

## 2. 系统拓扑

```
                   ┌──────────────────────────────┐
                   │   Cloudflare (CDN / WAF / DDoS) │
                   └──────────────┬───────────────┘
                                  │
                ┌─────────────────┴──────────────────┐
                │     Edge Load Balancer (ALB/NLB)   │
                └───────────┬───────────┬────────────┘
                            │           │
            ┌───────────────┴┐    ┌─────┴────────────┐
            │  Next.js SSR   │    │   API Gateway     │
            │  (Vercel/K8s)  │    │ (Kong / Envoy)    │
            └────────┬───────┘    └─┬───────┬─────────┘
                     │              │       │
                     └─────────┐    │       └────── public REST /v1
                               ▼    ▼
                          ┌───────────────────────────────┐
                          │  Internal Service Mesh (mTLS) │
                          └──┬───┬───┬───┬───┬───┬───┬────┘
                             │   │   │   │   │   │   │
       auth-svc  jobs-svc companies-svc  salaries-svc
       billing-svc  notifications-svc  admin-svc  search-svc
       crawler-svc (Python)  analytics-svc  files-svc
                             │
            ┌────────────────┴─────────────────┐
            ▼                                  ▼
    Postgres (Primary + Replica)         Kafka / Redis
    ClickHouse                           Elastic / Meilisearch
    S3                                   Temporal
```

- 服务通信：内部 **gRPC**（性能 + 类型）；事件驱动用 **Kafka**。
- 公开 API：**REST**（OpenAPI 3.1，文档自动生成）。

---

## 3. 微服务清单

| 服务 | 责任 | 主要数据 | 同步依赖 | 异步事件 |
| --- | --- | --- | --- | --- |
| **auth-svc** | 注册/登录、Token、OAuth、Magic Link、2FA、密码 | users, sessions, oauth_identities, magic_links, totp_secrets | - | `user.created`, `user.email_verified`, `user.deleted` |
| **jobs-svc** | 岗位 CRUD、状态机、聚合页缓存、岗位关系 | jobs, job_tags, job_metrics_cache | search-svc | `job.created/updated/expired/sticky_started/sticky_ended` |
| **companies-svc** | 公司 CRUD、认领、聚合 | companies, company_tags, claims | - | `company.created/claimed/updated` |
| **applications-svc** | 内部申请、状态机、雇主回复 | applications, application_events | jobs-svc, notifications-svc | `application.submitted/viewed/replied` |
| **billing-svc** | 订单、套餐、Add-on、Stripe / Crypto webhook、发票 | orders, order_items, bundles, balances, invoices | jobs-svc | `order.paid/refunded`, `bundle.balance_changed` |
| **notifications-svc** | 邮件、站内信、Discord / Twitter Webhook、Newsletter 调度 | subscriptions, alerts, templates, send_logs | - | 消费 `*.*` 触发邮件 |
| **search-svc** | 索引同步、查询、相关性、Faceting | ES/Meilisearch indices | - | `index.updated` |
| **crawler-svc** (Python) | 抓取 / 解析 / 去重 / 字段映射 | crawl_sources, crawl_runs, raw_jobs | jobs-svc | `crawl.found_job` |
| **salaries-svc** | 月度聚合、趋势、API | salaries_aggregated (ClickHouse) | jobs-svc | `salary.snapshot_ready` |
| **analytics-svc** | 埋点接入、看板查询、Funnel | ClickHouse | - | 消费 `track.*` |
| **admin-svc** | 后台聚合 API、批量操作、审计 | audit_log | 所有 svc | `admin.action_executed` |
| **files-svc** | 上传、转码、扫毒 | files, virus_scans | S3 | `file.uploaded/scanned/cleaned` |
| **api-gateway** | 路由、鉴权、限流、配额、API Key、计费 | api_keys, usage_log | auth-svc | - |
| **content-svc** | Learn 文章、作者管理、Markdown 渲染 | articles, authors | - | `article.published` |

### 3.1 服务通用约定
- **每个服务**：拥有独立数据库 schema；其他服务**只通过事件 / gRPC 调用**访问。
- 部署单元：独立 Docker image + Helm chart；可独立扩缩容。
- 接口契约：proto 文件统一存 `proto/`；事件 schema 存 `schemas/events/*.json`（Avro 兼容）。

---

## 4. 数据模型

### 4.1 设计原则
- UUID v7 主键（含时序，索引友好）。
- 软删 `deleted_at` 仅对 user / company 等核心表生效；其它表硬删。
- 货币统一存 USD cent (`bigint`)，转换在边界。
- 时间统一 `timestamptz`，存 UTC。
- JSONB 仅放半结构化字段（tags, benefits, metadata），关键字段独立列以利索引。

### 4.2 主要表（Postgres）

#### `users`（auth-svc）
```sql
id              uuid PK default uuid_generate_v7()
email           varchar(255) UNIQUE NOT NULL
email_lower     varchar(255) GENERATED ALWAYS AS (lower(email)) STORED UNIQUE
password_hash   varchar(255)            -- bcrypt 12
role            user_role NOT NULL      -- candidate/employer/admin/api
status          user_status NOT NULL DEFAULT 'active' -- active/banned/deleted
display_name    varchar(120)
locale          char(5) DEFAULT 'en'
timezone        varchar(64) DEFAULT 'UTC'
email_verified_at timestamptz
two_fa_secret   text                    -- TOTP, encrypted at rest（KMS 包裹）
two_fa_enabled  bool DEFAULT false
last_login_at   timestamptz
last_login_ip   inet
created_at      timestamptz DEFAULT now()
updated_at      timestamptz DEFAULT now()
deleted_at      timestamptz
```
索引：`(role, status)`, `(email_lower)`, `(last_login_at DESC)`。

#### `oauth_identities`
`id, user_id fk, provider (google|github|...), provider_user_id, profile_json, created_at`；UNIQUE `(provider, provider_user_id)`。

#### `magic_links`
`id, email, token_hash UNIQUE, purpose (login|verify_email|password_reset), expires_at, consumed_at, ip, user_agent, created_at`；过期 15 分钟；一次性消费。

#### `sessions`
`id, user_id, refresh_token_hash, ip, user_agent, expires_at, revoked_at, created_at`。

#### `companies`（companies-svc）
```sql
id              uuid PK
slug            varchar(160) UNIQUE
name            varchar(160) NOT NULL
website         varchar(255)
logo_url        varchar(500)
description_md  text
size_bucket     company_size            -- 1-10, 11-50, 51-200, 201-500, 501-1k, 1k+
founded_year    int
hq_country      char(2)
hq_city         varchar(160)
funding_total_usd_cent bigint
twitter         varchar(80)
discord         varchar(160)
linkedin        varchar(160)
github          varchar(80)
industry_tags   uuid[] REFERENCES tags(id)
owner_user_id   uuid REFERENCES users(id)
is_claimed      bool DEFAULT false
is_verified     bool DEFAULT false
status          company_status DEFAULT 'active'
created_at, updated_at, deleted_at
```

#### `tags`
```sql
id              uuid PK
slug            varchar(80) UNIQUE        -- "solidity", "remote", "defi"
name            varchar(120)
category        tag_category              -- skill/chain/role/benefit/region/seniority
parent_id       uuid REFERENCES tags(id)
description_md  text
seo_h1, seo_description text
created_at
```

#### `jobs`（jobs-svc）
```sql
id              uuid PK
slug            varchar(200) UNIQUE
company_id      uuid NOT NULL REFERENCES companies(id)
title           varchar(160) NOT NULL
description_md  text NOT NULL
location        varchar(160)
country_code    char(2)
region          varchar(40)
is_remote       bool NOT NULL DEFAULT false
seniority       seniority_enum            -- intern/junior/mid/senior/lead/exec
employment_type employment_type_enum      -- full/part/contract/internship
salary_min_cent bigint
salary_max_cent bigint
salary_currency char(3) DEFAULT 'USD'
benefits_json   jsonb
main_skill_id   uuid REFERENCES tags(id)
apply_type      apply_type_enum           -- external/internal
apply_url       varchar(500)
application_email varchar(255)
posted_by_user_id uuid REFERENCES users(id)
source          varchar(60) DEFAULT 'manual'  -- manual / crawler-greenhouse / ...
external_id     varchar(160)              -- crawler 原 id 去重
status          job_status DEFAULT 'pending' -- draft/pending/live/paused/expired/rejected
is_sticky_until timestamptz
sticky_tier     int                       -- 0/24h/3d/7d/14d/30d
has_logo_upgrade bool DEFAULT false
has_color_upgrade bool DEFAULT false
color_hex       char(7)
has_premium_support bool DEFAULT false
posted_at       timestamptz DEFAULT now()
expires_at      timestamptz NOT NULL
views_count     int DEFAULT 0             -- 由 ClickHouse 同步
apply_clicks_count int DEFAULT 0
created_at, updated_at, deleted_at
UNIQUE (source, external_id) WHERE external_id IS NOT NULL
```
索引：
- `(status, posted_at DESC)` 部分索引 `WHERE status='live'`
- `(country_code, is_remote)`
- `(company_id, status)`
- GIN `to_tsvector('english', title || ' ' || description_md)`

#### `job_tags`
`job_id fk, tag_id fk, position int`；PK `(job_id, tag_id)`。

#### `applications`
```sql
id              uuid PK
job_id          uuid NOT NULL
candidate_user_id uuid NOT NULL
status          application_status        -- submitted/viewed/replied/rejected/withdrawn
cover_letter    text
answers_json    jsonb
resume_file_id  uuid REFERENCES files(id)
submitted_at, viewed_at, replied_at, decision_at
```

#### `orders`、`order_items`、`bundles`、`bundle_balances`、`invoices`
- `orders`：`id, user_id, total_cent, currency, payment_method, provider, provider_ref, status (pending/paid/refunded/failed), created_at, paid_at`
- `order_items`：`id, order_id, sku, quantity, unit_price_cent, metadata jsonb (linked_job_id, addon_type)`
- `bundles`：`id, name, sku, price_cent, job_credits, addons jsonb, validity_months int`
- `bundle_balances`：`id, employer_company_id, bundle_id, job_credits_remaining, expires_at`
- `invoices`：`id, order_id, number unique, pdf_url, issued_at, tax_amount_cent, ...`

#### `subscriptions`（notifications-svc）
`id, email UNIQUE, first_name, last_name, source, preferences jsonb, status (active/unsubscribed/bounced), verified_at, created_at`

#### `job_alerts`
`id, user_id, name, filters jsonb, frequency (daily/weekly), last_sent_at, status`

#### `api_keys`（api-gateway）
`id, user_id, key_hash, name, plan, rate_limit_rpm int, monthly_quota int, used_this_month int, last_used_at, status, expires_at`

#### `audit_log`（admin-svc）
`id, actor_user_id, action, entity_type, entity_id, before jsonb, after jsonb, ip, user_agent, created_at`

### 4.3 ClickHouse 表（analytics）
- `events`：`event_name LowCardinality, user_id, session_id, ts DateTime64, props Map(String,String), country, ua, ...`
- `job_views`：`job_id UUID, ts DateTime, user_id, ip_hash, referer`
- `job_apply_clicks`：同上 + `apply_type`
- `api_usage`：`api_key_id, endpoint, status_code, ts, latency_ms`

### 4.4 数据迁移
- 工具：`prisma migrate`。
- 命名规则：`YYYYMMDDHHMM_short_description.sql`。
- 每次 PR 必含 `up` + `down` SQL；预演阶段在 staging Postgres 自动 dry-run。
- 大表加列：`ALTER ... ADD COLUMN ... NOT NULL DEFAULT` 用 `IF NOT EXISTS` 拆分两步（先 nullable，回填，再加约束），避免长锁。

---

## 5. API 规范

### 5.1 通用规则
- BaseURL（公开）：`https://api.web3career.example/v1`
- BaseURL（内部 BFF）：`https://internal-api.web3career.example/v1`
- 内容协商：`application/json; charset=utf-8`。
- 字段命名：snake_case。
- 时间：ISO 8601 UTC。
- 货币：金额单位 cent（整数），单位字段 `*_currency`。
- 分页：游标式 `cursor` + `limit`；返回 `meta.pagination.next_cursor`。
- 错误：
  ```json
  {
    "error": {
      "code": "VALIDATION_FAILED",
      "message": "Salary min cannot exceed max.",
      "request_id": "req_01HX...",
      "fields": { "salary_min_cent": "less_than_max" }
    }
  }
  ```
- 错误码：`AUTH_REQUIRED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_FAILED`, `RATE_LIMITED`, `CONFLICT`, `PAYMENT_REQUIRED`, `SERVER_ERROR`, `DEPENDENCY_FAILED`。
- HTTP 状态：`401`（鉴权），`403`（权限），`404`（缺失），`409`（冲突），`422`（业务校验），`429`（限流），`5xx`（服务端）。
- 幂等：所有 POST 改写资源支持 `Idempotency-Key` header（24h 内复用）。
- 版本：URL `/v1`；破坏性变更引入 `/v2`，原版本保留 ≥ 12 个月。

### 5.2 端点目录（节选）

#### Auth
- `POST /v1/auth/register` `{ role, email, password, first_name, last_name, company_name? }`
- `POST /v1/auth/login` `{ email, password, totp? }`
- `POST /v1/auth/magic-link` `{ email }` → 邮件发送一次性登录链接
- `GET  /v1/auth/magic-link/verify?token=` → 颁发 session
- `POST /v1/auth/oauth/{provider}/start` → 返回 redirect URL + state + PKCE
- `POST /v1/auth/oauth/{provider}/callback` `{ code, state }`
- `POST /v1/auth/refresh`
- `POST /v1/auth/logout`
- `POST /v1/auth/password/forgot`、`POST /v1/auth/password/reset`
- `POST /v1/auth/verify-email/resend`、`GET /v1/auth/verify-email?token=`
- `POST /v1/auth/2fa/setup` → 返回 QR 字符串与 backup codes
- `POST /v1/auth/2fa/enable` `{ code }` / `POST /v1/auth/2fa/disable` `{ code }`
- `POST /v1/auth/2fa/verify` `{ code }`（step-up）

#### Users
- `GET /v1/users/me`
- `PATCH /v1/users/me`
- `DELETE /v1/users/me`（GDPR 删除请求，30 天软删 + 标记）
- `GET /v1/users/me/export`（GDPR 数据导出，触发后台任务，邮件下载链接）

#### Jobs
- `GET /v1/jobs?...`（公开，无需鉴权；筛选见 PRD §9）
- `GET /v1/jobs/{id}`
- `GET /v1/jobs/{id}/related?type=same_company|same_tag&limit=`
- `POST /v1/jobs`（雇主，需付费）
- `PATCH /v1/jobs/{id}`
- `POST /v1/jobs/{id}/pause` / `resume` / `repost` / `boost`
- `DELETE /v1/jobs/{id}`
- `POST /v1/jobs/{id}/report`

#### Companies
- `GET /v1/companies?sort=open_roles|funding|salary&industry=...`
- `GET /v1/companies/{slug}`
- `POST /v1/companies/{slug}/claim`
- `PATCH /v1/companies/{slug}`（已认领）

#### Applications
- `POST /v1/jobs/{id}/apply` `{ resume_file_id, cover_letter, answers[] }`
- `GET /v1/applications/me`（候选人）
- `GET /v1/employer/applications?job_id=&status=`（雇主）
- `PATCH /v1/employer/applications/{id}` `{ status, message }`

#### Talent Pool
- `POST /v1/candidates/visibility` `{ enabled: true, sectors:[...] }`
- `GET /v1/employer/talent?...filters`（付费，需 Bundle Scale+）

#### Bookmarks / Alerts
- `POST /v1/bookmarks/{job_id}`、`DELETE /v1/bookmarks/{job_id}`、`GET /v1/bookmarks`
- `POST /v1/alerts`、`GET /v1/alerts`、`PATCH /v1/alerts/{id}`、`DELETE /v1/alerts/{id}`

#### Salaries
- `GET /v1/salaries`、`GET /v1/salaries/by-role/{role}`、`GET /v1/salaries/by-region/{region}`、`GET /v1/salaries/by-chain/{chain}`
- `GET /v1/salaries/trend?role=&period=12m`

#### Tags
- `GET /v1/tags?popular=true&limit=`
- `GET /v1/tags/{slug}`

#### Billing
- `POST /v1/billing/orders` `{ items:[{ sku, qty, metadata }] }`
- `GET /v1/billing/orders/me`
- `POST /v1/billing/checkout/stripe`
- `POST /v1/billing/checkout/crypto`
- `POST /v1/billing/webhooks/stripe`（签名校验）
- `POST /v1/billing/webhooks/nowpayments`
- `POST /v1/billing/refunds/{order_id}`（admin）
- `GET /v1/billing/invoices/{id}.pdf`

#### Subscription
- `POST /v1/subscribe`、`POST /v1/unsubscribe?token=`

#### API（公开数据 API for 第三方）
所有 `/v1/...` 端点；额外鉴权头 `Authorization: Bearer <api_key>`；含 `X-RateLimit-*`、`X-Request-Id`。

#### Admin
- `/v1/admin/...` 全集，需 `role=admin` + Google Workspace SSO。

### 5.3 OpenAPI
- `services/api-gateway` 自动生成 `openapi.json`；CI 校验向后兼容（`oasdiff`）。
- 文档站 `docs.web3career.example`，自动同步。

---

## 6. 认证与权限

### 6.1 JWT
- 算法 HS256（v1）→ 准备好切 RS256（v1.1，用 KMS 管私钥）。
- Access token TTL 15 分钟；Refresh 30 天，旋转 + 重放检测（一旦旧 refresh 被再次使用，撤销整族 session）。
- Token payload：`{ sub, role, plan, eml_verified, exp, iat, jti }`。

### 6.2 OAuth
- 实现 Google / GitHub OIDC；state + PKCE 防 CSRF。
- 邮箱冲突策略：若 OAuth 邮箱已存在普通账号，引导手动绑定（输入密码确认）。

### 6.3 Magic Link
- 邮箱无密码登录：用户提交邮箱 → 后端生成 32-byte 随机 token → 哈希入库 + 明文邮件发送 → 用户点击 → 后端校验 token、未过期、未消费 → 标记 `consumed_at` 并颁发 session。
- 速率限制：同邮箱 1min 1 次、1h 5 次。
- 用途扩展：邮箱验证、密码重置共用同一表 + 不同 `purpose` 字段。

### 6.4 RBAC
- 角色：`guest / candidate / employer.owner / employer.member / employer.viewer / admin / api`。
- 权限粒度：`resource.action`，如 `job.create`、`job.update.own`、`talent.search`。
- 中间件 `@RequirePermission('job.create')` 强校验。
- 雇主 → 公司多对多（`company_members` 表，角色 Owner/Admin/Member/Viewer）。

### 6.5 2FA（TOTP）
- 算法：RFC 6238，30 秒窗口，6 位数字。
- 雇主与管理员账户**强制**启用；候选人**可选**。
- 启用流程：`/2fa/setup` 返回 `otpauth://` URI + 10 个 backup codes（一次性，bcrypt 存储）。
- 敏感操作（删除岗位、申请退款、批量导出、修改账单卡）触发 step-up：要求 5 分钟内有有效 TOTP 验证。
- 丢失设备：使用 backup code；用尽后联系客服走身份核验流程。

### 6.6 API Key
- 创建时生成 32 byte 随机 + 哈希存储；明文仅展示一次。
- 范围 `scopes`：`jobs:read`, `companies:read`, `salaries:read`, `jobs:write`（保留），`webhooks:write`。
- 限流：见 §10。

### 6.7 防护
- 登录失败：5 次/15 分钟锁账户 30 分钟；触发邮件提醒。
- 注册 / 重要操作：hCaptcha / Turnstile（可配阈值）。
- 重要操作（删账号、加 API key、改邮箱）：需邮件二次确认。
- 异地登录检测：根据 IP / 设备指纹判断；新设备首登强制 step-up 2FA + 邮件提醒。
- 会话管理：用户可在 Profile → Security 查看所有活跃 session 并一键登出。

---

## 7. 业务工作流

### 7.1 岗位发布生命周期
```
Draft ──submit──► Pending ──auto/manual review──► Live
   ▲                              │
   │                              └──reject──► Rejected
   │                              │
   │                              └──expire(60d)──► Expired
   │
   └──pause──► Paused ──resume──► Live
```
- 自动审核：黑名单关键词、雇主信用、域名年龄；触发挂起 24h 人工。
- Live 时同步索引到 search-svc；状态变更发 Kafka 事件。
- Expired 后 30 天，岗位仍可访问但 `noindex`；之后归档至历史索引。

### 7.2 申请生命周期
```
Submitted ──viewed──► Viewed ──reply──► Replied
                                   ├──reject──► Rejected
                                   └──hire──► Hired
求职者可任意时刻 Withdraw → Withdrawn
```

### 7.3 订单生命周期
```
Created(pending) ──checkout──► AwaitingPayment ──webhook success──► Paid
                                              │
                                              └──webhook fail / 24h timeout──► Failed
Paid ──refund──► Refunded
```
- 支付完成 → 触发 `order.paid` → billing-svc 解锁 add-ons / 写入 bundle_balances → jobs-svc 将关联岗位置为 Live。

### 7.4 Bundle 消费
- 雇主发布岗位时，billing-svc 校验有余额且未过期；扣减 1 个 credit；记录消费历史。
- 多个 Bundle 时按 FIFO（早过期优先消费）。

### 7.5 退款
- 自助退款：72h 内 + 无 Apply 点击 + 无 Featured 已生效 → 自动通过。
- 其它：人工后台审批；按比例计算（剩余天数 / 总有效期）。

---

## 8. 爬虫与聚合服务（crawler-svc）

### 8.1 总体架构（Python）
```
[Scheduler (Prefect)] → [Source Worker pool (Celery)] → raw_jobs table → [Normalizer] → [Dedup] → jobs-svc gRPC
                                                                                                       │
                                                                                                       ▼
                                                                                                  Kafka job.created
```

### 8.2 源类型
| 类型 | 数量 | 抓取方式 |
| --- | --- | --- |
| Greenhouse API | ~200 公司 | 公开 JSON API |
| Lever API | ~120 公司 | 公开 API |
| Ashby API | ~80 公司 | 公开 API |
| RSS Feed | ~50 来源 | 解析 |
| 项目官网 HTML | ~300 | Playwright headless |
| Crypto Twitter Bot | 1 | 第三方 API |

### 8.3 字段映射
- 每个 source 维护 YAML：
  ```yaml
  source: greenhouse
  fields:
    title: $.title
    location: $.location.name
    description: $.content
    apply_url: $.absolute_url
    posted_at: $.updated_at
    tags_from: $.metadata[*].name
  rules:
    is_remote: location matches /(?i)remote/
    salary_extract: regex \$([0-9]+)k[- ]+\$([0-9]+)k
  ```
- 归一化器 normalize：货币换 USD、薪资单位换年薪、地名标准化（Mapbox geocoding cache）。

### 8.4 去重策略
- 主键：`(source, external_id)` UNIQUE。
- 二级：SimHash on `(company_id, title, location)`，相似度 ≥ 0.9 视为重复。
- 跨源融合：将 multiple sources 指向同一逻辑岗位（保留首次出现 ID + 关联表）。

### 8.5 监控
- 每个 source 每次抓取记录 `crawl_runs(source, started_at, finished_at, items_found, items_new, errors_count)`。
- 24h 内 zero new items 或 errors_count > 10% → 告警。
- Dashboard：成功率、平均耗时、新岗位数趋势。

### 8.6 合规
- 遵守 robots.txt；UA 自报 `Web3CareerBot/1.0 (+https://web3career.example/bot)`。
- 单源 ≤ 1 req/s。
- 不抓取 PII，仅公开职位信息。

---

## 9. 搜索（search-svc）

### 9.1 选型
- **Elasticsearch 8**（v1）：强大、语义化分析。
- 可选 Meilisearch：实例小、latency 极低，作为 fallback。

### 9.2 索引
- `jobs_v1`：每条岗位一份 doc；字段：`title, description, company_name, tags[], country_code, region, is_remote, salary_min, salary_max, posted_at, status`。
- `companies_v1`：`name, slug, description, tags[], hq_country`。
- `tags_v1`：用于自动补全。
- 全文分析：`english` analyzer + 自定义 synonym（solidity ↔ smart-contract）。

### 9.3 同步
- jobs-svc 写入后异步发 Kafka `job.created/updated`，search-svc 消费并 upsert；失败重试 5 次后 DLQ + 告警。
- 全量重建：每日凌晨从 Postgres 物化视图 reindex 到新 alias `jobs_v1-YYYYMMDD`；切流量。

### 9.4 查询
- 公开 API 通过 `q=` 全文 + 多 facet（tag, country, salary range, posted_within）。
- 结果排序：默认 `_score * recency_decay`；可强制 `posted_at desc` / `salary desc`。
- 拼写纠错：`suggest` API；返回 "Did you mean"。

### 9.5 自动补全
- `GET /v1/suggest?q=`：返回 tag、公司、岗位标题混合结果，按 popularity 加权。

---

## 10. API 网关 / 限流 / 配额

### 10.1 网关
- **Kong（开源）或 Envoy + Lua plugin**；前置鉴权、限流、API key 计费、CORS、日志。
- 公网入口仅暴露网关；内部服务 mTLS 通信。

### 10.2 限流
| 路径模式 | 限流策略 |
| --- | --- |
| `POST /v1/auth/*` | 10 req/min/IP |
| `POST /v1/applications` | 5 req/min/IP |
| `POST /v1/jobs` | 10 req/hour/user |
| 公开 `GET /v1/jobs*` | 60 req/min/IP（匿名）/ 600 req/min（API Free） |
| API Starter / Pro / Enterprise | 见 PRD §10 |

实现：Redis token bucket，原子 Lua 脚本。

### 10.3 配额
- 每月 `monthly_quota` 字段；超出返回 `402 Payment Required`，引导升级。
- 续费在 UTC 月初重置。

### 10.4 计费记账
- 每次成功请求写 ClickHouse `api_usage`；每月 1 号生成账单。
- Webhook 投递失败：指数退避重试（1, 5, 25, 125 分钟）；5 次失败标记 endpoint 暂停。

---

## 11. 支付（v1 仅 Stripe）

### 11.1 法币（Stripe）
- 接入 **Stripe Checkout Session**（pre-built UI，托管页面，平台属 PCI SAQ-A 最低级合规）。
- 关键 webhook：`checkout.session.completed`、`charge.refunded`、`charge.dispute.created`、`invoice.paid`。
- 税务：Stripe Tax 自动计算（EU VAT、US Sales Tax、印度 GST、英国 VAT 等），按账单地址。
- 发票：Stripe Invoicing 自动开票 → 同步 `invoice_id` 到我方 `invoices` 表 → 提供站内 PDF 下载。
- 安全：Webhook 签名校验（`Stripe-Signature` + endpoint secret + 5 分钟时间戳窗口）；幂等 key 防止重复处理。
- 失败重试：Stripe 内置自动重试 4 次；最终失败标记 `order.status=failed` + 邮件通知雇主。

### 11.2 退款
- Stripe Refund API（全额或部分）；退款写 `refunds` 表 + audit_log。
- 自助退款规则：72h 内 + 无 Apply 点击 + Sticky 未生效 → 自动通过；其他人工审批。
- 退款触发后：jobs-svc 立刻将关联岗位置为 `expired`，撤回 Featured / Sticky / Newsletter 等增值权益（若未消耗）。

### 11.3 防欺诈
- Stripe Radar 自动评分；高风险订单强制 3DS。
- 同公司域名 24h 内多 IP / 多卡 → 触发风控人工。
- 雇主连续退款率 > 5% / 3 个月 → 限制发布额度并人工审核。
- 拒付率（chargeback rate）每月监控，超过 0.75% 触发 Stripe 风险升级。

### 11.4 v1.1 加密支付（预留设计，非 v1 范围）
- 候选方案：**NOWPayments** 或 **Coinbase Commerce** 托管收银台；用户在第三方页面完成转账，平台**不接触私钥、不要求站内连接钱包**。
- 触发：用户在 Checkout 选择"Pay with crypto" → 后端 `POST /v1/billing/checkout/crypto` 创建第三方 invoice → 跳转网关页面 → 用户线下转账 → 网关 webhook 回调入账。
- 风险与限制：确认数（USDC 12 / ETH 12 / BTC 3）；超时 30 分钟自动取消订单；不接受已知混币器地址。
- v1 阶段：相关代码与 webhook 入口仍预留 feature flag `payments.crypto.enabled=false`，便于后续灰度开启。

---

## 12. 通知服务

### 12.1 邮件类别
- 事务（Resend，IP pool A）：注册验证、密码重置、订单收据、申请回执、Bundle 到期提醒。
- 营销（Resend，IP pool B）：Newsletter、岗位推荐、Alert。
- 模板：MJML → HTML；多语言版本；管理后台可视化编辑。

### 12.2 Newsletter
- 每周二 14:00 UTC 群发；订阅用户分批 SMTP（每秒 50 封）。
- 内容：本周新增高薪岗位 Top 20、热门 tag 趋势、广告位（Newsletter Header SKU）。
- 退订 token 每用户唯一；点击直接退订。

### 12.3 Alert
- 候选人创建 alert → notifications-svc cron 每日/每周扫描 `jobs` 表匹配 → 发邮件。
- 触发条件去抖：同一 alert 24h 内不重复。

### 12.4 站内信
- 实现 `messages` 表（雇主 ↔ 候选人）；申请回复触发邮件 + 站内消息。

### 12.5 Twitter / Discord
- 雇主 add-on 触发 → notifications-svc 调用 Twitter API v2 / Discord Webhook 发布预填文本。
- 失败重试 3 次；后台可手动重发。

---

## 13. 缓存策略

### 13.1 层次
1. **CDN（Cloudflare）**：公开页面 HTML（Vercel ISR），TTL 60s-3600s。
2. **应用层 Redis**：
   - 岗位详情 JSON：`job:{id}` 5min。
   - 列表查询结果：`jobs:list:{hash(query)}` 60s。
   - Tag popularity：`tags:popular` 1h。
3. **Postgres 物化视图**：薪资聚合、Top Companies、Tag 统计。

### 13.2 失效
- 岗位变更 → 主动 `DEL job:{id}` + 发 Kafka `job.updated` → Next.js `revalidatePath`。
- 列表缓存：因 query 组合多，依赖 TTL 自然失效。

### 13.3 防穿透
- 不存在的 ID：写 `not_found` 占位 60s。
- 热点 key：本地 LRU 二级缓存避免雪崩。

---

## 14. 消息队列与事件

### 14.1 Kafka topic
- `users.events`：user.created/email_verified/deleted。
- `jobs.events`：job.created/updated/expired/sticky_*。
- `companies.events`：company.claimed/verified。
- `orders.events`：order.paid/refunded。
- `applications.events`：application.submitted/replied。
- `crawler.events`：crawler.found_job。
- `notifications.events`：mail.send/sms.send。
- `analytics.events`：track.*。

约定：JSON 包含 `event_id`, `event_name`, `version`, `produced_at`, `tenant_id`, `data`；schema 版本化。

### 14.2 BullMQ
- 轻量任务：发送单封邮件、生成 PDF、生成 OG 图像。
- 失败策略：3 次指数重试；超出进 DLQ；DLQ 7 天保留供后台 reprocess。

### 14.3 Temporal
- 长流程：注册 → 邮箱验证 → onboarding 任务串；订单 → 支付等待 → 上线流程；爬虫 source pipeline。
- 工作流可观测：UI 查看每一步状态、重试。

---

## 15. 可观测性

### 15.1 日志
- 结构化 JSON；字段 `ts, level, svc, env, trace_id, span_id, user_id, request_id, msg, extra`。
- 收集到 Loki；Grafana Explore 查询。
- 30 天热存 + 6 个月冷存（对象存储）。

### 15.2 指标（Prometheus）
- 服务级：请求 RPS、P50/95/99 latency、错误率、依赖调用耗时。
- 业务级：
  - 每分钟新增岗位数
  - 每小时 Apply 点击
  - 每日付费转化率
  - 爬虫成功率、抓取耗时分布
  - Webhook 处理延迟
- 告警规则示例：
  - `auth-svc 5xx > 1% / 5min` → P1
  - `crawler 成功率 < 90% / 30min` → P2
  - `payment.webhook latency > 30s` → P1
  - `kafka consumer lag > 10k` → P2

### 15.3 链路追踪
- OpenTelemetry SDK；trace_id 沿 HTTP / gRPC / Kafka header 传递（`traceparent`、`b3`）。
- 通过 Grafana Tempo 可视化。

### 15.4 Sentry
- 前后端共用 organization；release tag 与 git commit 关联；source map 上传。
- 错误聚合规则：忽略已知 noise（如 user cancel）；分配 owner 自动指派。

### 15.5 运行 Runbook
- 关键路径（支付、登录、爬虫、搜索）各自一份 Runbook：症状 → 检查命令 → 缓解 → 升级。

---

## 16. 安全

### 16.1 OWASP 防御
- SQL 注入：Prisma 参数化；禁止 raw query 写库。
- XSS：返回 JSON；前端渲染时严格 sanitize（DOMPurify）；岗位描述支持 Markdown 但白名单标签。
- CSRF：JWT in HttpOnly cookie + `SameSite=Lax` + 自定义 header（`X-CSRF-Token`）双重防御。
- SSRF：所有"由用户提供的 URL"出站请求走 sandbox proxy（屏蔽内网、AWS metadata、127.0.0.1）。
- RCE：禁止 eval/动态 require；Markdown 渲染走 `markdown-it` 白名单。
- 文件上传：MIME 校验 + magic number + 病毒扫描（ClamAV）+ 静态托管子域。

### 16.2 数据保护
- 静态加密：Postgres TDE / RDS encryption；S3 SSE-S3。
- 传输加密：TLS 1.3 only；HSTS preload；内部 mTLS。
- 字段级加密：2FA secret、API key（KMS 包裹）。
- 备份：Postgres 每 6h 全量 + WAL；保留 30 天；季度演练恢复。

### 16.3 密钥管理
- AWS KMS / GCP KMS / Vault；服务通过 IAM Role 取密钥；禁止仓库内出现真实密钥（CI 用 `gitleaks` 阻断）。

### 16.4 漏洞响应
- 安全策略文件 `SECURITY.md`；安全邮件 `security@`；72h SLA。
- 季度第三方渗透测试；年度 SOC 2 / ISO 27001 路线图。

### 16.5 合规
- GDPR：DPO 邮箱；数据导出/删除 30 天 SLA；Cookie 分级。
- CCPA：Do Not Sell 入口；删除 API 公开。
- PCI DSS：Stripe 托管，平台属 SAQ-A。
- 内容审查：违法违规岗位人工审核 24h 内处理；按当地法律下架。

---

## 17. 基础设施 & 部署

### 17.1 集群拓扑
- 主区域：`us-east-1`（生产）+ `eu-west-1`（容灾）。
- Kubernetes：3 个环境（dev / staging / prod），节点池区分（system, general, data, gpu-optional）。
- 数据库：托管 Postgres（多 AZ + read replica）；Redis Cluster 3+3；Kafka 3 节点（MSK 或 self-host）。
- 对象存储：Cloudflare R2 主 + S3 灾备。
- DNS：Cloudflare；故障切换。

### 17.2 IaC
- **Terraform**：网络 / 数据库 / K8s 集群 / IAM / DNS。
- **Helm chart**：每个服务一个 chart；values 区分环境。
- **ArgoCD**：监听 main 分支，自动 sync staging；prod 需手动 promote。

### 17.3 部署流程
1. PR 合并 main → CI 构建 image → 推送 ECR / GAR。
2. ArgoCD 检测到 image tag 变更 → 应用到 staging。
3. 自动跑 smoke test（关键路径 30s 内验证）。
4. 人工 promote prod；分批 rolling，10% → 50% → 100%。
5. 失败自动回滚到上一个稳定 image。

### 17.4 配置管理
- 12-Factor App；所有配置走环境变量。
- 敏感值放 Vault / AWS Secrets Manager，启动时注入。

### 17.5 灰度与开关
- Feature flag（GrowthBook）与代码同生命周期；上线后 14 天必须清理或永久化。
- 数据库变更（schema）始终向后兼容；先发布兼容版本，再切流量，再清旧字段。

---

## 18. 性能与扩展性

### 18.1 容量规划（v1 目标）
- 50 万 MAU；并发 5k；峰值 RPS 2k（公开 API + 浏览）。
- 数据规模：jobs 200 万行（含历史）、applications 50 万、users 30 万。
- 存储：Postgres ~200GB；Elasticsearch ~150GB；ClickHouse ~500GB/年。

### 18.2 优化策略
- 公开列表全部走 Elasticsearch + Redis；Postgres 仅事务。
- 读写分离：列表 / 详情读 replica；写主库。
- 慢查询监控：> 200ms 自动记录 + 周报 review。
- 大表分区：jobs 按 `posted_at` 月分区；applications 按 `submitted_at` 季度分区。

### 18.3 扩展点
- API 网关与各 svc 水平扩展（HPA 基于 CPU + 自定义 metric）。
- Kafka partition：jobs.events 16 partition；按 company_id hash 路由。
- ClickHouse 集群分片：按 month。

---

## 19. 测试

### 19.1 单元 / 集成
- Jest（Nest）；覆盖率 ≥ 80% lines。
- Python crawler：pytest + responses + factory_boy。

### 19.2 契约测试
- 服务间 gRPC：`buf breaking` 阻断破坏性变更。
- 公开 API：Pact / Schemathesis 基于 OpenAPI 跑 fuzz；CI 阶段检测。

### 19.3 集成测试
- Docker Compose 启 Postgres + Redis + Kafka + ES；NestJS supertest。

### 19.4 性能测试
- k6：每周 nightly 跑公开列表 / 详情；目标 RPS 与 P95 阈值。

### 19.5 数据正确性
- 爬虫去重：测试 1000 条样本，要求 ≤ 0.1% 重复。
- 薪资聚合：与人工抽样对比 ≤ 1% 误差。

### 19.6 演练
- 每季度跑一次 DB 恢复演练（从备份恢复到非生产集群）。
- 每月一次 chaos 演练：删 Redis pod 验证降级；模拟 Kafka 不可用看队列积压。

---

## 20. CI/CD 详细

### 20.1 触发
- PR：lint + typecheck + unit + integration + image build（push 到临时 tag）。
- main：完整流水线 + image push + ArgoCD sync staging + smoke。
- tag `v*`：变更日志生成；准备 prod promote。

### 20.2 缓存
- pnpm store cache、turbo remote cache、docker buildx cache。

### 20.3 必备检查
- 安全：`trivy`（镜像）、`gitleaks`（仓库）、`semgrep`（代码）。
- 数据库迁移：`prisma migrate diff` 与上次发布对比；含 `BREAKING` 标签触发额外审批。

---

## 21. 数据策略

### 21.1 ETL / Pipeline
- 实时：Kafka → ClickHouse（Vector / Kafka Engine）。
- 批量：每日凌晨 Postgres → Snowflake / BigQuery（备选）做长期分析。

### 21.2 报告
- **2025/2026 Intelligence Report**：自动每月由 salaries-svc 汇总；输出 JSON → 模板渲染成 PDF（Playwright）。
- 关键指标：岗位数趋势、按链分布、薪资分布、招聘公司类型变化、热门技能。

### 21.3 数据治理
- PII 字段标记（schema 注解）；查询日志审计。
- 数据保留：候选人主动删除 → 30 天硬删；申请记录在岗位关闭 12 个月后归档。

---

## 22. 国际化（后端视角）

- 所有用户内容字段在 Postgres 直接存原文本（不翻译）。
- 系统消息 / 邮件模板按 locale 选择。
- 时区：`users.timezone`；定时任务（newsletter、alert）按用户本地时间发送（窗口 ±1h）。
- 地理：Mapbox / Google Geocoding API；缓存到 `geocoded_locations` 表，避免重复请求。

---

## 23. 失败处理 / 弹性

### 23.1 降级
- 搜索不可用：fallback 到 Postgres `ILIKE`（限制最近 30 天 5000 条）。
- 邮件不可用：写 outbox 表，恢复后补发。
- 支付 webhook 延迟：用户页面显示"Processing..."，后端轮询 24h；超时回滚订单。

### 23.2 重试
- 所有外部调用使用熔断（resilience4j 风格）+ 指数退避。
- Kafka consumer：DLQ + 重放工具。

### 23.3 灾备
- Postgres：跨区域只读复制 + 月度切主演练。
- 静态资源：R2 + S3 双写。
- RTO 4h / RPO 1h。

---

## 24. 验收清单（后端 Done 标准）

- [ ] 所有公开 API 通过 OpenAPI 校验且文档站可访问。
- [ ] 单元 + 集成测试覆盖率 ≥ 80%；契约测试覆盖前后端共用接口。
- [ ] Postgres / Redis / Kafka / ES 在 staging 持续运行 2 周无 P1 故障。
- [ ] 爬虫导入真实岗位 ≥ 50,000；去重率 ≥ 99.9%。
- [ ] Stripe + 加密支付 happy path 与退款流程跑通；webhook 幂等通过。
- [ ] 监控看板上线（API、爬虫、支付、邮件 4 个看板）；告警接入 PagerDuty。
- [ ] 备份策略与恢复演练完成；文档归档。
- [ ] 安全：trivy 高危为 0；gitleaks 通过；依赖每周自动升级。
- [ ] GDPR 数据导出与删除 API 自测通过，30 天 SLA 文档化。
- [ ] API 公开计费完成对账：使用量 vs 计费金额误差 ≤ 0.1%。

---

## 25. 开放问题

1. 是否引入 GraphQL（BFF 层）替代部分 REST？取决于前端需要的字段灵活度。
2. 中长期是否自建 ATS？目前依赖外部，但若 Talent Pool 做大可考虑。
3. 加密支付（NOWPayments / Coinbase Commerce）是否在 v1.1 上线？取决于 Stripe 在新兴市场的覆盖与海外用户的支付偏好数据。
4. AI 写岗位描述、AI 评分匹配度：是否在 v1.1 引入 LLM 服务（如 Anthropic Claude）。
5. 爬虫源是否做付费数据合作（避免 ToS 风险）：商务跟进。
