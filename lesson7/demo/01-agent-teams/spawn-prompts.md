# Agent Team 起 team prompt 样例集

四种最常见场景的 prompt 模板。在 Claude Code 里**整段粘贴**即可——Claude 会问你确认后开始 spawn。

> 前提：`~/.claude/settings.json` 里已开启 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`，Claude Code ≥ v2.1.32。

---

## 范本 1：Parallel Code Review（推荐第一次试这个）

```
帮我起一个 agent team review 这个项目的最近一次 commit。spawn 三个 reviewer：
- 一个专看 security implications（auth / 输入校验 / 密钥泄漏）
- 一个看 performance impact（N+1 查询 / 不必要的循环 / 大对象 copy）
- 一个 validate test coverage（关键路径有没有测、断言强不强）
让他们各自看完后报告 findings，最后给我一个 synthesized 总结。
```

**适合场景**：PR review、上线前 last-mile check。
**典型 token 消耗**：~50-100k（取决于 diff 大小）。

---

## 范本 2：Competing Hypotheses Debugging

```
用户报告：app 收到第一条消息后就退出，本来应该保持连接。
spawn 5 个 agent teammate 调查不同的假说。让他们互相对话、像
科学辩论一样**试图反驳**对方的理论。最后把幸存下来的假说和
证据更新到 ./findings.md。
```

**适合场景**：根因不清的 bug。
**关键技巧**：明确让 teammate **互相挑战**，破除单一视角锚定效应。

---

## 范本 3：跨层并行重构

```
重构 src/auth 模块——目标是把 JWT 验证从 middleware 抽出来变成可注入的 service。
起一个 3-teammate team：
- A 只改 src/auth/ 下的代码
- B 只改 src/api/ 下用到 auth middleware 的地方
- C 只改 tests/auth/ 和 tests/api/

文件所有权严格分离，禁止跨边界改文件。所有 teammate 进改动前
都要先提 plan 给我审批。我只批通过包含测试的 plan。
```

**关键设计**：用 prompt **显式分配文件所有权** + plan approval gate 卡守质量。

---

## 范本 4：新 feature 多模块并行实现

```
新功能：给 dashboard 加一个"最近 7 天活跃用户"图表。
起一个 4-teammate team，分别做：
- Designer：用 mock 数据画 UI 草图、定接口
- Backend：实现 /api/analytics/active-users 返回 7 天数据
- Frontend：用真实接口替换 mock，写图表组件
- QA：补单测 + e2e 测

Designer 先做，Backend 和 Frontend 不能在 Designer 没敲定接口前开始。
QA 看到 Backend 完成就开始写后端测试，Frontend 完成就开始写前端测试。
```

**关键设计**：用**任务依赖**（Designer 阻塞 Backend / Frontend）+ **可独立推进的部分并行**。

---

## 通用提示

- **不要一个 prompt 起 6+ teammate**。官方推荐 3-5 个，超过协调开销大于收益。
- **每个 teammate 给具体的责任范围**——不要"看看代码"这种模糊指令。
- **多个 teammate 改同一文件 = 互相覆盖**。预先分边界。
- **遇到不前进的 teammate**：`Shift+Down` 切过去直接对话。
- **完事让 lead clean up**：`clean up the team`——不能让 teammate 跑 cleanup。
