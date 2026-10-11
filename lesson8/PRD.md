# Web3 Career 复刻项目 PRD

> 文档版本：v1.0
> 编写日期：2026-05-17
> 参考站点：https://web3.career/
> 目标：实现一个功能等价的 Web3 招聘聚合平台（含前后端、雇主付费、薪资数据、内容站、API）

---

## 0. 文档读法

本 PRD 面向产品、设计、前后端、测试、运维全角色。每个模块按"目标 → 功能清单 → 字段/状态 → 交互流程 → API/数据要求"五段式描述。读者可只读对应章节即可独立开工。

---

## 1. 产品概述

### 1.1 产品定位
**一站式 Web3 招聘聚合平台**：把"招聘信息抓取/发布 + 薪资数据 + 公司榜 + 学习资源 + API + 媒体广告"打通，向求职者免费，向雇主、广告主和 API 调用者收费。

### 1.2 价值主张
| 受众 | 痛点 | 我们的价值 |
| --- | --- | --- |
| 求职者 | Web3 行业岗位分散在 Discord、Twitter、各项目官网，难比较 | 75k+ 岗位 + 7k+ 项目集中索引；提供薪资基准、远程岗位、入门级岗位、按链/语言筛选 |
| 雇主 | 招 Web3 人才贵且分散，传统 LinkedIn 转化差 | 9k Discord + 41k Twitter + 63 万月浏览的高纯度 Web3 流量；按需选择套餐、Featured、邮件推送、社媒分发 |
| 投资/记者/数据团队 | 缺乏行业招聘趋势数据 | 提供 API、月度 Intelligence Report、薪资数据 |
| 广告主 | 难触达高净值开发者 | Banner / Newsletter / 推广岗位等多形态广告位 |

### 1.3 商业模式
1. **职位发布收费**：免费基础发布 + 增值项（Featured、Sticky、Logo、Color、Premium Support）。
2. **套餐 Bundle**：批量购买，24 个月有效期。
3. **API 订阅**：按月/年付费，按调用量分档。
4. **广告位**：Newsletter、Banner、首页 Featured 位、Twitter 推广。
5. **培训分发**：与 Bootcamp（如 Metana）分润；提供"Job Guaranteed"通道。
6. **数据报告**：年度/季度 Intelligence Report 下载需注册或付费。

### 1.4 关键指标（北极星）
- 月独立访客 ≥ 50 万
- 在线有效职位 ≥ 5 万
- 求职者注册量 ≥ 30 万
- 雇主付费转化率 ≥ 3%
- Newsletter 订阅 ≥ 10 万
- 平台 NPS ≥ 40

### 1.5 范围说明
**包含**：Web 前端（PC + 移动）、后端 API、管理后台、爬虫/聚合服务、邮件服务、计费、数据看板、公开 API。
**不包含（v1）**：原生 App、招聘外包服务、独立 ATS 完整功能、链上招聘奖励代币、薪资发放/合规中介。

---

## 2. 用户角色与场景

### 2.1 角色
| 角色 | 描述 | 核心权限 |
| --- | --- | --- |
| Guest 访客 | 未登录用户 | 浏览岗位、公司、薪资、内容；订阅 Newsletter |
| Candidate 求职者 | 注册用户 | 收藏岗位、申请岗位、Talent Pool 展示、订阅 Alert、上传简历 |
| Employer 雇主 | 公司账号 | 发布岗位、购买套餐、查看申请、搜索人才池、查看广告效果 |
| Author 内容贡献者 | 邀请制 | 撰写 Learn 板块文章、编辑教程 |
| Admin 平台管理员 | 内部员工 | 内容审核、用户/订单管理、爬虫调度、运营配置 |
| API Consumer | 第三方 | 拉取岗位/薪资数据（凭 API Key） |

### 2.2 关键用户场景
- **S1：开发者 1 分钟刷岗位**：访客无登录 → 首页 → Tag 筛选`solidity` + `remote` → 查看 5-10 条卡片 → 点开 Apply 跳转外链 → 24h 后通过邮件订阅再回访。
- **S2：HR 30 分钟发岗位**：注册公司 → 上传 Logo → 填表 → 选择 Featured 30 天 + Newsletter → 信用卡或 USDC 支付 → 实时上线 → 后台看到点击/申请。
- **S3：候选人加入 Talent Pool**：求职者填写技能/期望薪资/可工作时区 → 简历审核 → 雇主在后台搜索匹配 → 站内信邀约。
- **S4：第三方数据消费**：分析师注册 API Key → 调用 `/api/v1/jobs?tag=rust&limit=100` → 同步到自家 BI。
- **S5：内容获客**：访客通过 Google 搜索"solidity developer salary"→ 命中 `/salaries` SEO 落地页 → 注册 Alert。

---

## 3. 信息架构与站点地图

### 3.1 主要路由
```
/                                      首页
/login, /register                      登录/注册（求职者 & 雇主分流）
/forgot-password                       重置密码
/dashboard                             求职者主控台
/employer/dashboard                    雇主主控台
/admin                                 管理后台

# 岗位浏览
/jobs                                  全部岗位（默认按时间排序）
/jobs/{slug}-{id}                      岗位详情
/{tag}-jobs                            按技能/标签聚合页（如 /solidity-jobs, /rust-jobs）
/remote-jobs                           远程岗位
/internships                           实习岗位
/entry-level-jobs                      入门级岗位
/non-tech-jobs                         非技术岗位
/jobs/city/{city}                      按城市聚合（如 /jobs/city/new-york）
/jobs/region/{region}                  按区域聚合（asia/europe/...）
/jobs/chain/{chain}                    按链聚合（solana/ethereum/l2/...）

# 公司
/companies                             Top 100 公司列表
/companies/{slug}                      公司详情（含其在招岗位、融资、文化等）

# 薪资
/salaries                              薪资总览
/salaries/{role}                       某岗位薪资（如 /salaries/solidity-developer）
/salaries/region/{region}              按区域
/salaries/chain/{chain}                按链
/highest-paid-jobs                     最高薪聚合

# 雇主
/hire                                  雇主着陆页
/post-a-job                            发布单个岗位（表单 + 支付）
/post-a-job/bundle                     批量套餐
/advertise                             广告位说明 & 询价
/api                                   API 介绍 & 申请

# 内容
/learn                                 学习中心首页
/learn/{category}                      分类（articles/books/courses/...）
/learn/{category}/{slug}               文章/资源详情
/intelligence-report                   年度报告

# 静态
/about, /faq, /pricing, /terms, /privacy, /contact

# 工具
/sitemap.xml, /robots.txt, /rss.xml
```

### 3.2 顶部导航（PC）
`Logo | Home | Salaries | Internships | Learn | TOP Web3 Jobs | Hire | API | Advertise | Buy a Bundle | [Post a Job CTA]`

移动端将主导航折叠为汉堡菜单，保留 `Post a Job` 主 CTA 始终可见。

### 3.3 底部导航（5 列）
1. 产品：Jobs / Salaries / Internships / Top Companies
2. 雇主：Post a Job / Bundle / Advertise / API
3. 学习：Articles / Books / Bootcamps / Glossary
4. 关于：About / FAQ / Contact / Press
5. 法律 & 社交：Terms / Privacy / Twitter / Discord / RSS

---

## 4. 详细功能需求

### 4.1 首页（/）

**目标**：3 秒内传达"Web3 行业最大招聘聚合平台"，并完成"订阅 / 看岗位 / 发岗位"任一关键转化。

#### 4.1.1 页面模块（自上而下）
1. **Hero 区**：标语 + 计数（`Browse 74,396 blockchain jobs in web3 at 7,207 projects`） + 邮件订阅表单（First Name / Last Name / Email）+ Logo 墙。
2. **快捷 Tag 云**：60+ 个胶囊（按热度排序），如 `ai`, `solidity`, `rust`, `backend`, `marketing`, `remote`, `defi` 等；点击进入对应 `/{tag}-jobs`。
3. **Featured Jobs**：默认展示 10-12 条 Sticky 岗位；每张卡片字段见 §4.2.1。
4. **生态合作横幅**：可配置广告位（如行业活动、Bootcamp、合作媒体）。
5. **Latest Jobs**：按发布时间倒序的最新 20 条；底部"Load more / Browse all"。
6. **Bootcamp 推荐**：广告位（如 Metana）。
7. **Browse by Category**：远程 / 非技术 / 入门级 / 设计 等分类入口。
8. **Salaries Snapshot**：3-5 个高薪职位 Mini 卡（平均/最高/最低）+ 跳转 `/salaries`。
9. **Top Cities**：20 个城市 + 岗位数；点击进入聚合页。
10. **Top Regions**：Asia / Europe / Africa / Americas / Oceania。
11. **Learn 资源**：11 个分类入口。
12. **FAQ**：6-10 条折叠问答。
13. **Testimonials**：3-5 条用户证言（含头像、姓名、公司）。
14. **Footer**：见 §3.3。

#### 4.1.2 交互细节
- Hero 订阅表单提交后弹 Toast "Subscribed!"；后端写入 `subscriptions` 表并触发 Welcome 邮件。
- Tag 胶囊默认显示 60 个，点击"Show all"展开 200+。
- Latest Jobs 区每 30 秒前端轮询一次，新增岗位带 `NEW` 角标。
- 所有可点击 Logo 须带 `rel="nofollow"`（除非雇主购买了 DoFollow 增值）。

### 4.2 岗位列表与详情

#### 4.2.1 列表页（/jobs 与所有聚合页）
**页面元素**：
- `H1`：「{Tag} Jobs」或「Web3 Jobs」+ 副标题 `{Month Year} ({N} New)`。
- SEO 段落：可折叠"What does a {role} do?"模板化文案。
- 顶部 Filter 栏：Search（标题/公司/关键词）、Remote 开关、Location 下拉、Salary range slider（$0–$500k）、Seniority、Benefits 多选、Chain 多选、Posted within 7/30/90 天。
- 排序：`Most Recent`（默认）/ `Highest Paid` / `Most Applied`。
- 列表：每页 25 条；卡片字段见下；底部分页 + URL 同步参数（`?page=2&tag=solidity`）。
- 右侧栏（PC ≥ 1280px）：相关 Tag、Top 5 Companies in this category、CTA `Post a Job`。
- 底部：相关 Tag 聚合链接（SEO 互链）。

**Job Card 字段**：
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| company_logo | image | 80×80 圆角 |
| title | string | 鼠标悬停展开摘要 |
| company_name | link | 跳到公司详情 |
| posted_at | relative time | "9h", "3d", "2w" |
| location | string + 国旗 icon | "Remote" 或 "New York, US" |
| salary_min, salary_max | currency | 缺失时显示"Salary undisclosed" |
| tags[] | chip[] | 最多展示 6 个，溢出 `+N` |
| is_remote | bool icon | 地球 icon |
| is_sticky | bool | 黄色高亮背景 |
| has_logo_upgrade | bool | 1.5x 视觉放大 |
| apply_btn | button | "Apply Now" |
| save_btn | icon | 心形（需登录）|

#### 4.2.2 岗位详情页（/jobs/{slug}-{id}）
**布局**：左主区 70% + 右浮动卡 30%。
- 主区：公司 Logo + 标题 + 元信息（时间、地点、薪资、tag、福利徽章）→ Apply CTA → 「About the company」「The role」「Responsibilities」「Requirements」「Nice to have」「Benefits」「Application Process」分段（支持 Markdown） → 相关岗位列表（同公司其它岗位 / 同 Tag 其它岗位）。
- 右浮动卡：Apply 按钮（吸顶）、Bookmark、Share（Twitter/Discord/LinkedIn/Copy Link）、Job 元信息卡、Report 按钮。
- 行为：
  - 点击 Apply：若 `apply_type=external` 直接 302 到外链并埋点；若 `apply_type=internal` 弹出 Talent Pool 申请表单。
  - 浏览数 +1 / 申请数 +1 写入 `job_metrics`。
  - 未登录用户点击 Save / Apply 弹起注册引导。

### 4.3 公司模块

#### 4.3.1 公司列表（/companies）
- 标题"Top Web3 Companies - {Month Year}"；分页 25 条；最多展示 Top 100。
- 字段：Logo / 名称 / 总融资 / 团队规模 / 总部 / 在招岗位数 / 平均薪资 / 标签（exchange / wallet / L1 / DeFi / Gaming）。
- 筛选：industry tag、地区、规模、是否在招、是否远程友好。
- 排序：在招岗位数（默认）/ 融资规模 / 平均薪资。

#### 4.3.2 公司详情（/companies/{slug}）
- Banner（封面 + Logo + Tagline）。
- Tabs：Overview / Jobs ({N}) / Salaries / News / Reviews。
- Overview：介绍（Markdown）、官网、社交账号、融资、Founders、Tech Stack、Office Locations。
- Jobs：当前所有在招岗位（沿用 Job Card）。
- Salaries：该公司岗位分布（小提琴/箱线图）。
- News：最近 10 条来自爬虫聚合的新闻 / Tweets。
- Reviews：求职者匿名评价（v1.1）。
- 雇主认领按钮："Claim this profile"（验证流程）。

### 4.4 薪资模块

#### 4.4.1 概览（/salaries）
- 顶部摘要：Web3 行业 5 个核心指标（平均 / 中位 / Top 25%）。
- 三张数据表：
  - **By Role**：Quantitative Developer $200k 平均 ($70k-$300k) 等，共 30+ 行。
  - **By Region / Country**：北美 / 欧洲 / 亚洲 + 50 国家。
  - **By Seniority**：Junior / Mid / Senior / Lead / CTO。
- 趋势图：2022-01 至当月的月度均薪折线（可切换岗位）。
- 月度数据：Postings 数、Applicants 数。
- 数据更新：每月 1 号晚 23:59（UTC）跑批；显示"Last updated: {date}"。

#### 4.4.2 子页 `/salaries/{role}`、`/salaries/region/{region}`、`/salaries/chain/{chain}`
统一模板，SEO 友好；面包屑 + 同类岗位互链。

### 4.5 雇主端

#### 4.5.1 雇主着陆页（/hire）
- 三大卖点：流量、人才池、效果案例。
- 关键数据：「31 days reach: 631,803 views / 41,000 Twitter / 9,000 Discord」。
- 客户 Logo 墙；Pricing 概要；Testimonial。
- CTA：`Post a Job` / `Buy a Bundle` / `Talk to Sales`。

#### 4.5.2 发布岗位（/post-a-job）
**表单字段**（带必填校验）：
| 字段 | 类型 | 必填 | 备注 |
| --- | --- | --- | --- |
| first_name, last_name | string | ✅ | 联系人 |
| email | string | ✅ | 接收申请 |
| company_name | string | ✅ | |
| company_url | url | ✅ | `https://` 强制 |
| twitter_handle | string |  | 用于自动 @ 推文 |
| position_title | string | ✅ | ≤ 100 字 |
| location | string | ✅ | "Remote" 或城市 |
| is_remote | bool | ✅ | |
| main_skill | enum | ✅ | 单选 60+ 主技能 |
| extra_skills[] | enum[] |  | 多选 ≤10 |
| benefits[] | enum[] |  | 4-day-week / Equity / Pay-in-crypto / 401k / Healthcare 等 |
| salary_min, salary_max | int | ✅ | $10k–$500k，min ≤ max |
| description | markdown | ✅ | 富文本/Markdown 编辑器，≤ 20k 字符 |
| apply_type | enum | ✅ | `external_url` / `internal_form` |
| apply_url | url | 条件必填 | apply_type=external_url 时必填 |
| application_email | email | 条件必填 | apply_type=internal_form 时必填 |
| invoice_company, invoice_address, invoice_vat | string |  | 发票信息 |

**增值项 Add-ons**（独立勾选 / 计入小计）：
- Premium Support: $99
- Logo: $49（1.5x 浏览量）
- Color Highlight Standard: $99
- Color Highlight Custom Brand: $149
- Sticky 24h: $49 (1x)
- Sticky 3d: $99 (3x)
- Sticky 7d: $149 (6x)
- Sticky 14d: $199 (12x)
- Sticky 30d: $299 (24x)
- Newsletter Blast: $199（一次）
- Twitter Promo Post: $99
- Discord Announce: $59

**支付**：Stripe 信用卡（v1）；预留加密货币支付接入口（v1.1，通过 NOWPayments/Coinbase Commerce 等托管网关，用户线下转账，无需在站内连接钱包）。
**有效期**：单条岗位默认上线 60 天（可续费）；Bundle 中的发布额度有效期 24 个月。
**退款**：72 小时内未购买增值且无申请，全额退款；其他情况按比例退回剩余天数。

#### 4.5.3 套餐购买（/post-a-job/bundle）
| Bundle | 价格 | 包含 | 适用 |
| --- | --- | --- | --- |
| Starter | $299 | 3 条岗位 + 全部基础发布 | 小团队 |
| Growth | $899 | 10 条 + 1 次 Newsletter + 7d Sticky | 中型公司 |
| Scale | $2,499 | 30 条 + 2 次 Newsletter + 14d Sticky + Twitter Promo | 招聘旺季 |
| Enterprise | 询价 | ≥ 100 条 + API + Talent Pool Search + Banner | 大客户 |

每个 Bundle 中的发布额度有效期 24 个月。

#### 4.5.4 雇主主控台（/employer/dashboard）
- 数据看板：今天/本周 浏览数、点击 Apply 数、岗位数、剩余 Bundle 余额。
- 岗位列表：状态 (Draft / Pending Review / Live / Paused / Expired) + 操作 (编辑/暂停/续费/下架)。
- 申请管理（针对 internal_form）：候选人列表 + 状态 + 站内信。
- Talent Pool 搜索（付费）：按技能/期望薪资/时区/简历关键词。
- 账单：发票 PDF 下载、订阅管理、Bundle 余额。
- 团队成员：邀请同事，角色 Owner/Member/Viewer。

### 4.6 求职者端

#### 4.6.1 注册 & 登录（/register, /login）
- 入口：邮箱+密码、Google OAuth、GitHub OAuth、Magic Link（邮箱免密一次性登录链接）。
- 求职者 vs 雇主在注册时选择身份；雇主额外填写公司名 / URL。
- 邮箱验证强制；忘记密码标准 OTP 流程。
- 可选 2FA（TOTP）保护雇主与管理员账户。

#### 4.6.2 主控台（/dashboard）
- Tabs：Saved / Applied / Alerts / Profile / Resume / Talent Pool Visibility。
- Saved：收藏的岗位列表 + 备注。
- Applied：申请记录 + 状态（提交 / 已查看 / 已回复 / 已拒绝）。
- Alerts：按 Tag / Location / Salary 设置邮件提醒（每日/每周）。
- Profile：姓名、头像、简介、社交（GitHub/LinkedIn/Twitter/个人站点）、技能、期望薪资、可工作国家、时区、签证状态。
- Resume：上传 PDF / 在线 Resume Builder（v1.1）。
- Talent Pool Visibility：开关；仅显示给"经过身份认证"的雇主。

#### 4.6.3 申请流程
- 默认：跳转到雇主提供的外部 ATS / 网站，前端不收集任何隐私。
- 内部表单：候选人提交（姓名、邮箱、简历、Cover Letter、回答 3 道雇主自定义问题），数据落到 `applications` 表，雇主可查看 & 回复。

### 4.7 学习中心（/learn）
- 分类：Articles / Books / Bootcamps / Challenges / Courses / Interviews / News / Open Sources / Tutorials / Videos / Whitepapers。
- 文章字段：标题、作者、发布时间、阅读时长、封面、摘要、标签、正文（Markdown）、相关岗位（同 tag）。
- 列表筛选：分类、Tag、Author、Free/Paid（默认全部 Free）。
- 评论 & 点赞：v1.1（v1 仅显示分享按钮）。
- 后台编辑器：所见即所得 + Markdown 双模式 + 草稿 / 待审核 / 发布 三态。

### 4.8 API 模块（/api）

#### 4.8.1 公开能力
- `GET /api/v1/jobs`：分页拉取岗位；支持 `tag`, `chain`, `location`, `remote`, `salary_min`, `salary_max`, `limit`(1-100), `cursor`, `include_description`(bool)。
- `GET /api/v1/jobs/{id}`：详情。
- `GET /api/v1/companies`：公司列表。
- `GET /api/v1/companies/{slug}`：公司详情 + 岗位。
- `GET /api/v1/tags`：所有 Tag 及统计。
- `GET /api/v1/salaries`：薪资数据。
- `GET /api/v1/stats`：实时计数。
- `POST /api/v1/subscribe`：Newsletter 订阅。
- `POST /api/v1/webhooks`（付费）：注册 `job.created` / `company.updated` 等事件。

#### 4.8.2 认证 & 限流
- Header：`Authorization: Bearer <api_key>`。
- 速率：
  - Free：60 req/min，1k req/day。
  - Starter $49/mo：600 req/min，50k req/day。
  - Pro $199/mo：3k req/min，500k req/day。
  - Enterprise：自定义。
- 429 时返回 `Retry-After` 头；HTTP 200 时 `X-RateLimit-Remaining`。

#### 4.8.3 文档站
独立 `/api/docs`，OpenAPI 3.1 规范；提供 cURL / Node / Python / Go 多语言示例。

### 4.9 广告（/advertise）
- 广告位 SKU：
  - 首页 Hero Banner：$3,000 / 周
  - Sidebar Banner：$1,500 / 周
  - Newsletter Header：$2,500 / 期（每周 1 期，10 万订阅）
  - Sponsored Job：$499 / 14 天
  - Twitter 推广：$199 / 推文
- 申请流程：表单提交 → 销售跟进 → 合同 → 支付 → 上线。

### 4.10 管理后台（/admin）
- 用户管理：搜索 / 封禁 / 切换角色 / 重置密码。
- 内容审核：岗位待审核队列、举报队列、内容修改记录。
- 计费 & 订单：所有交易、退款、发票。
- 爬虫调度：源站列表、抓取频率、失败任务重跑、字段映射可视化。
- 运营配置：首页 Hero 文案、Featured 岗位排序、Tag 热度调整、Banner 投放。
- 数据看板：DAU/MAU、付费转化、Top Tag、Top Country、Funnel。

---

## 5. 非功能需求

### 5.1 性能
- 首页 LCP ≤ 2.0s（4G）；TTFB ≤ 200ms。
- 列表页 SSR + 增量静态再生（ISR）每 60s 重建。
- 详情页：CDN 缓存 5 分钟 + Stale-while-revalidate。
- API P95 < 200ms。

### 5.2 可用性
- 月度可用性 ≥ 99.9%。
- 关键路径：发布岗位、Apply、订阅。任何一项失败需告警 ≤ 1 分钟。

### 5.3 安全
- OWASP Top 10：CSRF Token、严格 CSP、HSTS、X-Frame-Options、Subresource Integrity。
- 密码：bcrypt 12 rounds；2FA（TOTP）对雇主与管理员强制启用。
- 雇主账户验证（防欺诈）：邮箱 + 域名 SPF 检查 + 公司域名 ≥ 30 天注册。
- 防爬：登录态接口加速率限制；公开页提供 sitemap，但敏感字段（如雇主邮箱）不外露。
- 隐私：求职者简历仅在显式同意下被雇主访问；可一键删除账号（GDPR）。

### 5.4 可访问性
- WCAG 2.2 AA 合规。
- 所有交互组件键盘可达；表单 label 与 input 关联；颜色对比 ≥ 4.5。

### 5.5 国际化
- v1 仅英文；UI 字符串集中 i18n（`next-intl` / `i18next`），便于后续支持 zh / es / fr / ja / ko。
- 时间统一 UTC 存储，前端按用户时区渲染。
- 金额统一 USD（v1.1 支持 EUR / GBP / JPY 转换）。

### 5.6 SEO
- SSR 必选；URL 全部 `kebab-case`；canonical 标签；多链聚合页生成专属 H1、meta description、JSON-LD JobPosting / Organization / BreadcrumbList。
- sitemap.xml 自动按 50k 上限分片，包含 lastmod。
- robots.txt 允许公开页，禁止 `/admin`、`/employer/dashboard`。

### 5.7 可观测性
- 集中日志：Loki / ELK；按 trace_id 串联。
- 指标：Prometheus + Grafana；业务面板（DAU/付费转化/抓取成功率）。
- 错误：Sentry（前后端）。
- 链路追踪：OpenTelemetry，关键路径标注。

### 5.8 合规
- GDPR：数据导出、删除接口；Cookie Banner（必要 / 分析 / 营销分级）。
- CCPA：Do Not Sell 入口。
- 支付：Stripe 满足 PCI DSS；加密支付走 NOWPayments，平台不接触私钥。
- 内容：自动检测违禁词（赌博、毒品、传销）；可疑岗位人工复核 24h。

---

## 6. 技术架构

### 6.1 总体拓扑
```
[Browser/Mobile Web]
        │ HTTPS
        ▼
[Cloudflare CDN + WAF]
        │
        ▼
[Next.js Edge SSR/ISR]  ── 公开页
        │
        ▼
[BFF (Next.js Route Handlers / tRPC)]
        │  REST/gRPC
        ▼
┌──────────────────────────────────────────────┐
│ Backend Services (NestJS / Go microservices) │
│  - auth-svc        - jobs-svc                │
│  - companies-svc   - salaries-svc            │
│  - billing-svc     - notification-svc        │
│  - admin-svc       - api-gateway             │
│  - crawler-svc (Python)                      │
└──────────────────────────────────────────────┘
        │
        ▼
[PostgreSQL Primary + Replica] [Redis] [Elasticsearch/Meilisearch] [S3] [ClickHouse 数据仓]
        │
        ▼
[Kafka / RabbitMQ]  (异步事件：JobCreated, ApplicationSubmitted, PaymentSucceeded, EmailDispatch)
```

### 6.2 前端
- 框架：**Next.js 15 (App Router) + React 19 + TypeScript**。
- 样式：**Tailwind CSS + shadcn/ui**；色板见 §7。
- 状态：服务端组件 + Zustand（客户端少量交互态）。
- 表单：React Hook Form + Zod 校验。
- 富文本：TipTap（Markdown 双向）。
- 图表：Recharts / Visx。
- 国际化：next-intl。
- 测试：Vitest + Playwright。

### 6.3 后端
- 主服务：**NestJS (TypeScript) 微服务**；爬虫 / 数据计算用 **Python (FastAPI + Celery)**。
- API 层：tRPC（前端内部）+ REST（公开 API，OpenAPI）+ GraphQL（可选 v1.1）。
- 身份：自研 + NextAuth.js v5（前端）+ JWT（HS256→RS256 升级路径）；可选 Keycloak 用于企业 SSO。
- 邮件：Resend / Postmark；模板 MJML。
- 队列：BullMQ（Redis）/ Kafka。

### 6.4 数据存储
- **PostgreSQL 16**：核心事务表（users, companies, jobs, applications, orders, ...）。
- **Redis**：缓存、Session、限流、队列。
- **Elasticsearch / Meilisearch**：全文搜索 + 复合过滤；岗位/公司/内容索引。
- **ClickHouse**：埋点、PV/UV、薪资聚合、API 调用日志。
- **S3 兼容存储（AWS S3 / R2）**：Logo、简历、文章封面、报告 PDF。

### 6.5 数据聚合 / 爬虫
- 爬虫源：50+ 项目官网（Greenhouse / Lever / Ashby ATS）、Twitter、Discord 公开频道、Y Combinator、Crypto Twitter Jobs Bot。
- 调度：Airflow / Prefect；每源 15-60 分钟一次。
- 去重：基于 `company + title + location` 模糊指纹（SimHash）+ Apply URL 主键。
- 字段对齐：每源建立 Mapping YAML；薪资字段统一为 USD 年薪。

### 6.6 第三方集成
| 用途 | 服务 |
| --- | --- |
| 支付（法币） | Stripe |
| 邮件营销 | Resend + 自建 Newsletter 调度 |
| OAuth | Google / GitHub |
| Magic Link 登录 | Resend Magic Link / NextAuth EmailProvider |
| ATS | Greenhouse / Lever / Ashby Open API |
| 反垃圾 | hCaptcha / Cloudflare Turnstile |
| 监控 | Sentry / Grafana Cloud / Better Stack |
| 文档站 | Mintlify / Nextra |
| Newsletter | 自建（避免锁定） |
| 客服 | Crisp / Intercom |
| 分析 | PostHog（自托管） |

### 6.7 部署
- 主站：Vercel（Next.js）或自托管 K8s（Kubernetes + ArgoCD）。
- 后端：Kubernetes（EKS / GKE）+ Helm。
- DB：托管 Postgres（Supabase / RDS）+ Redis（Upstash）+ Elasticsearch（Elastic Cloud）。
- 域名 / CDN / WAF：Cloudflare。
- CI/CD：GitHub Actions；PR → 预览环境（Vercel Preview + ephemeral DB）。

---

## 7. UI / UX 设计准则

### 7.1 设计原则
1. **信息密度高但层级清晰**：参考原站，每屏可见 6-10 条岗位。
2. **行动优先**：Apply / Save / Post 三个 CTA 颜色明显（主蓝/橙）。
3. **一屏一目的**：列表页只服务找岗位，详情页只服务申请决策。
4. **响应式优先**：移动端隐藏侧栏，卡片纵向堆叠。

### 7.2 设计代币（Design Tokens）
- 主色：`primary-600 #1F6FEB`（蓝），`accent-500 #FF7A00`（橙强调），`success #16A34A`，`warning #F59E0B`，`danger #DC2626`。
- 中性色：`gray-50 #FAFAFA`、`gray-100 #F3F4F6`、`gray-900 #111827`。
- 圆角：4 / 8 / 12 / 24px。
- 字体：Inter（UI）+ JetBrains Mono（代码）。
- 阴影：`sm`, `md`, `lg`, `xl` 四档；卡片默认 `sm`，悬浮 `md`。

### 7.3 关键组件库
- JobCard、CompanyCard、TagChip、FilterPanel、SalaryTable、ApplyButton、Pagination、Pricing Toggle、Stepper（发布岗位四步走）。
- 全部组件先 Figma 设计 → Storybook 实现 → 单元测试 → 集成。

### 7.4 关键流程线框（文字版）
**发布岗位四步走**：
```
Step 1: Company → Step 2: Job Details → Step 3: Add-ons & Pricing → Step 4: Payment
顶部带进度条；每步可后退；离开提示保存草稿。
```

---

## 8. 数据模型

> 仅列核心表与字段（实际开发以迁移脚本为准）。

### 8.1 ER 概览
```
User ──< Company (owner) ──< Job ──< Application
 │                              │
 │                              └──< JobTag(M:N → Tag)
 │
 ├──< Subscription
 ├──< SavedJob
 ├──< JobAlert
 └──< Resume

Company ──< CompanyTag(M:N → Tag)
Job ──< JobMetric(daily rollup)
Order ──< OrderItem ──→ Job / Bundle / Add-on
ApiKey ── owned-by ── User
Article ──< ArticleTag
```

### 8.2 关键表

#### users
| 字段 | 类型 | 备注 |
| --- | --- | --- |
| id | uuid PK | |
| email | varchar(255) | unique |
| password_hash | varchar(255) | nullable（OAuth-only 时） |
| role | enum | `candidate` / `employer` / `admin` |
| email_verified_at | timestamptz | |
| oauth_providers | jsonb | `{google, github, ...}` |
| created_at, updated_at, deleted_at | timestamptz | 软删 |

#### companies
| 字段 | 类型 | 备注 |
| --- | --- | --- |
| id, slug | pk + unique | |
| name, website, logo_url | string | |
| description | text | Markdown |
| size, founded_year, hq_location | string | |
| funding_total_usd | bigint | |
| twitter, discord, linkedin, github | string | |
| industry_tags | jsonb | |
| owner_user_id | fk users | nullable |
| is_claimed, is_verified | bool | |

#### jobs
| 字段 | 类型 | 备注 |
| --- | --- | --- |
| id, slug | pk + unique | slug = `kebab(title)-{shortid}` |
| company_id | fk | |
| title, description | string / text | description 为 Markdown |
| location, country_code, region | string | |
| is_remote | bool | |
| seniority | enum | intern/junior/mid/senior/lead/exec |
| employment_type | enum | full/part/contract/internship |
| salary_min, salary_max, salary_currency | int + char(3) | |
| benefits | jsonb | |
| main_skill_id | fk tags | |
| extra_tags | jsonb | tag id 列表 |
| apply_type | enum | external/internal |
| apply_url, application_email | string | |
| posted_by_user_id | fk users | nullable（爬虫则空） |
| source | enum | manual / crawler-{name} |
| status | enum | draft/pending/live/paused/expired/rejected |
| is_sticky_until | timestamptz | |
| has_logo_upgrade, has_color_upgrade, has_premium_support | bool | |
| color_hex | char(7) | nullable |
| posted_at, expires_at | timestamptz | |
| views_count, apply_clicks_count | int | 冗余字段，从 ClickHouse 同步 |

#### tags
`id, slug, name, category (skill/chain/role/benefit/region), description, parent_tag_id`

#### applications（仅 internal_form）
`id, job_id, candidate_user_id, status, cover_letter, answers jsonb, resume_url, submitted_at, viewed_at, replied_at`

#### orders & order_items
- orders：`id, user_id, total_amount_usd, currency, payment_method (stripe/crypto), status, provider_ref, created_at`
- order_items：`id, order_id, sku (job_post/bundle_starter/sticky_7d/...), quantity, price, metadata jsonb (linked_job_id)`

#### bundles
`id, name, price_usd, job_credits, addons jsonb, validity_months=24, status`

#### subscriptions
`id, email, first_name, last_name, source(home/footer/blog), preferences jsonb, status, verified_at, created_at`

#### job_alerts
`id, user_id, name, filters jsonb (tags/locations/salary), frequency(daily/weekly), last_sent_at`

#### api_keys
`id, user_id, key_hash, plan(free/starter/pro/enterprise), rate_limit_rps, monthly_quota, used_this_month, created_at, last_used_at`

#### salaries_aggregated (物化视图 / ClickHouse)
`role, region, country, chain, seniority, month, avg, min, max, p25, p75, sample_size`

---

## 9. API 规范（节选）

### 9.1 OpenAPI 摘要
- BaseURL：`https://api.web3career.example/v1`（公开）/ `https://api.web3career.example/internal/v1`（站内）。
- 统一响应：`{ data, meta: { pagination, request_id }, errors? }`。
- 错误码：`AUTH_REQUIRED`, `RATE_LIMITED`, `VALIDATION_FAILED`, `NOT_FOUND`, `SERVER_ERROR`。

### 9.2 典型端点

#### GET /v1/jobs
Query：`tag`（重复参数）、`chain`、`location`、`is_remote`、`salary_min`、`salary_max`、`posted_within_days`、`sort`(recent/salary)、`limit`(1-100)、`cursor`、`include_description`。
返回：
```json
{
  "data": [
    {
      "id": "job_01HX...",
      "slug": "rust-engineer-hibachi-01hx",
      "title": "Rust Engineer",
      "company": { "id": "co_...", "slug": "hibachi", "name": "Hibachi", "logo_url": "..." },
      "location": "Remote",
      "is_remote": true,
      "salary": { "min": 150000, "max": 200000, "currency": "USD" },
      "tags": ["rust", "backend", "aws", "blockchain"],
      "posted_at": "2026-05-17T08:21:00Z",
      "apply_url": "https://...",
      "is_sticky": false
    }
  ],
  "meta": { "pagination": { "next_cursor": "eyJ...", "limit": 25 } }
}
```

#### POST /v1/jobs（雇主，需登录 + 已购额度）
请求体同 §4.5.2 表单字段；返回岗位 ID 与发布状态。

#### POST /v1/applications
内部表单申请；速率：同 IP 1 分钟 5 次。

#### GET /v1/companies/{slug}
返回详情 + 在招岗位 + 聚合薪资。

#### GET /v1/salaries
Query：`role`、`region`、`chain`、`seniority`、`period` (3m/6m/12m)。

#### Auth
- `POST /v1/auth/email`（注册/邮箱密码登录）
- `POST /v1/auth/magic-link`（请求一次性登录链接）
- `GET  /v1/auth/magic-link/verify?token=`
- `POST /v1/auth/oauth/{provider}`
- `POST /v1/auth/refresh`、`POST /v1/auth/logout`
- `POST /v1/auth/2fa/enable` / `verify` / `disable`

---

## 10. 商业化与计费

### 10.1 定价表（v1）
| SKU | 价格 | 说明 |
| --- | --- | --- |
| job-post-basic | Free | 基础发布，60 天有效 |
| addon-premium-support | $99 | 含 SLA |
| addon-logo | $49 | 1.5x 浏览 |
| addon-color-std | $99 | 标准高亮 |
| addon-color-brand | $149 | 品牌色 |
| addon-sticky-24h | $49 | |
| addon-sticky-3d | $99 | |
| addon-sticky-7d | $149 | |
| addon-sticky-14d | $199 | |
| addon-sticky-30d | $299 | |
| addon-newsletter | $199 | |
| addon-twitter | $99 | |
| addon-discord | $59 | |
| bundle-starter | $299 | 3 jobs / 24 mo |
| bundle-growth | $899 | 10 jobs + sticky 7d + newsletter / 24 mo |
| bundle-scale | $2,499 | 30 jobs + 多次 sticky/newsletter |
| api-starter | $49 / mo | 50k req/day |
| api-pro | $199 / mo | 500k req/day |

### 10.2 计费流程
1. 加入购物车（前端本地）。
2. `POST /v1/orders` 创建订单（pending）。
3. 跳转 Stripe Checkout Session 完成支付。
4. Webhook `payment.succeeded` → 订单置为 paid → 写入 `bundles_balance` / 启用 add-ons → 岗位上线。
5. 发票邮件 + PDF（Stripe Invoicing + 站内归档）。
6. 退款：管理后台触发 → 调用 Stripe Refund → 标记岗位 expired。
7. （v1.1 可选）加密货币托管网关支付：用户在 NOWPayments / Coinbase Commerce 托管页面完成转账，回调到我方 webhook 后置为 paid；用户无需在站内连接钱包。

### 10.3 反欺诈
- 同一 IP 24h 内同一公司发布 > 3 → 自动 pending。
- 信用卡 + IP + 邮箱 + 设备指纹风险评分（Stripe Radar）。
- 高风险订单强制 3DS；连续退款率 > 5% 的雇主进黑名单。

---

## 11. 数据迁移 / 冷启动

- **种子数据**：先用爬虫从 Greenhouse / Lever / Ashby 抓取 10 万个真实岗位作为基础（仅展示，不收费）。
- **导入榜单**：人工维护 Top 100 Web3 公司 JSON，再补充融资 / 团队规模等。
- **薪资数据**：基于岗位 salary_min / salary_max 月度聚合即可。
- **学习内容**：导入 200+ 篇优质 Web3 文章 + 30 本书 + 20 个 Bootcamp。

---

## 12. 里程碑与排期（参考 4-5 人小组）

| 阶段 | 周期 | 交付物 |
| --- | --- | --- |
| Phase 0 准备 | 1 周 | 设计稿、技术选型确认、CI/CD、基础设施 |
| Phase 1 MVP | 4 周 | 注册/登录、岗位列表 + 详情、公司列表、爬虫导入 10 万岗位、首页、SEO、移动端、订阅 |
| Phase 2 雇主端 | 3 周 | 发布岗位、Bundle、Stripe 支付、Crypto 支付、雇主控台、邮件通知 |
| Phase 3 数据与 API | 3 周 | 薪资数据计算 + 页面、Open API + 文档站、API 计费 |
| Phase 4 增值与广告 | 2 周 | Newsletter、Twitter Promo、Banner、Featured、Sticky、Top 榜单 |
| Phase 5 候选人池 | 2 周 | Talent Pool、Resume Builder、Alert、雇主搜索 |
| Phase 6 学习中心 | 2 周 | 11 个内容分类、CMS、Author 邀请 |
| Phase 7 国际化 & 2FA | 2 周 | 中/英/西/日切换；雇主与管理员 2FA |
| Phase 8 数据看板 & 报告 | 2 周 | 管理后台、年度 Intelligence Report 自动生成 |

总周期约 **5 个月** 上线 v1，可按业务优先级裁剪。

---

## 13. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
| --- | --- | --- | --- |
| 爬虫被源站封禁 | 高 | 中 | 多通道（API > RSS > HTML），UA 轮换，按 robots.txt 合规，主动给源站留 backlink |
| 假岗位 / 欺诈 | 中 | 高 | 公司域名验证 + 人工抽审 + 报告按钮 + 风控规则 |
| Stripe 拒付 | 中 | 中 | Crypto 支付备选；3DS 强制；纠纷率监控 |
| SEO 流量被竞品截胡 | 中 | 高 | 内容矩阵（Salaries / Tag / Region / Chain 长尾），结构化数据 JSON-LD JobPosting |
| 账户被盗用 | 中 | 高 | 雇主与管理员强制 2FA、异常登录提醒、风控规则 |
| 数据合规（GDPR/CCPA） | 中 | 高 | 显式同意 + 数据导出 / 删除 + DPA |
| 服务可用性 | 中 | 高 | 多 AZ + 灾备 + 优雅降级（DB 不可用时仍能展示 CDN 缓存）|

---

## 14. 验收标准（v1 上线门槛）

- [ ] 首页、Job 列表、Job 详情、Company 详情、Salaries、Learn 列表 6 类核心页面 100% 完成且通过 Lighthouse Performance ≥ 90 / Accessibility ≥ 95。
- [ ] 已导入 ≥ 5 万个岗位、200 家公司，Sitemap 自动生成。
- [ ] 求职者：邮箱密码、Magic Link、Google/GitHub OAuth 四种登录可用；可收藏、Alert、申请。
- [ ] 雇主：能完整走通"注册 → 发布 → Stripe 支付 → 上线 → 查看效果"全链路；强制开启 2FA。
- [ ] Bundle、Add-ons 计费正确；退款流程跑通。
- [ ] API 提供至少 5 个端点 + 三种 SDK 示例 + Free / Starter / Pro 三档计费。
- [ ] 邮件 Newsletter 每周自动发送，订阅 ≥ 1 万。
- [ ] 监控告警上线：核心 API P95、付费失败率、爬虫成功率。
- [ ] GDPR：数据导出 + 删除接口存在并自测通过。

---

## 15. 待决问题（Open Questions）

1. Talent Pool 是否对所有雇主免费可搜？建议仅对 Bundle Scale 及以上付费雇主开放。
2. 是否做"推荐奖励"（推荐人获得平台积分 / 抵扣券）？v1.1 评估。
3. 内容生成是否引入 AI 助手（如自动生成岗位描述、求职信）？v1.1 评估。
4. 是否做原生 App？建议先 PWA。
5. 数据报告（Intelligence Report）是否免费？建议邮箱注册可下载，深度报告付费 $99。
6. 加密支付是否在 v1 上线？建议 v1.1，先观察 Stripe 转化率与海外用户支付偏好。

---

## 16. 附录

### 16.1 名词解释
- **ATS**：Applicant Tracking System，雇主端简历管理系统。
- **DAO/DeFi/NFT/L1/L2**：Web3 行业的业务垂直分类（仅作为岗位标签存在）。
- **Bundle**：批量岗位发布额度，24 个月内可消费。
- **Magic Link**：邮箱中收到的一次性登录链接，无需密码即可登录。

### 16.2 参考链接
- 原型站点：https://web3.career/
- 竞品：cryptojobslist.com / remote3.co
- 行业报告：web3.career/learn-web3/web3-intelligence-report

### 16.3 变更记录
| 版本 | 日期 | 作者 | 说明 |
| --- | --- | --- | --- |
| v1.0 | 2026-05-17 | 产品/AI 协作输出 | 首版完整 PRD |
