# 任务 1：再接一个 MCP，让 AI 做组合查询（必做）

## 时长

30 分钟内可完成。**不要求写 Python 代码**，主要是配置 `.mcp.json` 和设计 prompt。

## 任务描述

在 `lesson3/project/.mcp.json` 里再加一个 MCP server，让 Claude 同时调用两个 MCP（sqlite + 第二个）完成一次组合查询。

> **想换别的 server 试？** 下面 A/B 是默认推荐，但你完全可以挑自己喜欢的——MCP server 的查找清单见 [lesson3 主讲义"延伸阅读 → 去哪里找别的 MCP server"](../../README.md#去哪里找别的-mcp-server)。换成 fetch / memory / git / postgres 等都行，提交时把对应配置贴上来就好。

**任选一个方向（推荐零门槛）：**

### A 方向：filesystem MCP（推荐零账户）

接 `@modelcontextprotocol/server-filesystem`，让 Claude 同时：
- 读 `lesson1/README.md`（lesson 1 课堂讲了什么）
- 查 sqlite ohlc 表（BTC 这一个月走势）
- 写一段对比报告

### B 方向：github MCP（需 GitHub PAT）

接 `@modelcontextprotocol/server-github`（需要一个 GitHub Personal Access Token），让 Claude 同时：
- 读你某个 repo 的最近 5 条 commit
- 查 sqlite ohlc 表
- 写一段"项目活跃度 vs 行情"的轻分析

> **提示**：A 方向最简单，零账户、5 分钟搞定 server 配置。建议没接触过 MCP 的同学先做 A。B 方向更接近真实工作场景，但需要花几分钟去 GitHub Settings 开 PAT（仅勾 read 权限即可）。

## 操作步骤

### 步骤 1：复制参考配置

把同目录下的 `.mcp.json.example` 复制成 `lesson3/project/.mcp.json`（覆盖原来只有 sqlite 的配置），改成你自己选的方向：

```bash
cp lesson3/homework/task1-second-mcp/.mcp.json.example lesson3/project/.mcp.json
```

然后：
- **A 方向**：把 `fs.args` 里的占位路径 `/abs/path/to/your/ai_lesson` 改成你本机上 `ai_lesson` 仓库的**绝对路径**。filesystem MCP 出于安全只允许访问指定目录树，必须显式指定。
- **B 方向**：把 `github.env.GITHUB_PERSONAL_ACCESS_TOKEN` 设为你的 PAT；同时把 fs server 那一段删掉（或保留也无所谓，只是多挂一个）。

### 步骤 2：在 lesson3/project/ 启动 Claude

```bash
cd lesson3/project && claude
```

Claude 启动时会显示挂载了几个 MCP server。如果只挂上 1 个、漏了你新加的，看 `claude --debug` 启动日志找原因（常见：路径写错、PAT 无效、server 包名拼错）。

### 步骤 3：粘贴组合查询 prompt

**A 方向**整段粘贴：

```
你现在挂载了两个 MCP server：sqlite 和 fs。请：

1. 用 fs 读 ../lesson1/README.md，提炼 lesson 1 主要讲了什么（约 100 字）
2. 用 sqlite 查 ohlc 表中 BTCUSDT 过去 30 天的最高、最低、均价、最近收盘
3. 写一段约 200 字的中文对比："lesson 1 课堂讲了什么 vs 数据上看 BTC 这一个月怎么样"

所有 SQL 和文件路径你自己处理。
```

**B 方向**整段粘贴：

```
你现在挂载了两个 MCP server：sqlite 和 github。请：

1. 用 github 列出 <你的 GitHub 用户名>/<某个 repo> 最近 5 条 commit 的标题和日期
2. 用 sqlite 查 ohlc 表中 BTCUSDT 过去 30 天的最高、最低、均价、最近收盘
3. 写一段约 200 字的中文："这个 repo 这段时间活跃度 vs BTC 行情" 的轻分析

所有 SQL 和 API 调用你自己处理。
```

### 步骤 4：观察 Claude 怎么协调两个 MCP

**重点观察**：
- Claude 是不是自己判断什么时候用 fs、什么时候用 sqlite？还是要你引导？
- 两次工具调用的顺序：先文件再 SQL，还是穿插着调？
- 如果某个工具失败（比如 PAT 失效、文件路径错），Claude 怎么处理？

## 提交内容

1. **修改后的 `.mcp.json`** —— 脱敏（PAT 留空 / 用 `<REDACTED>`）
2. **会话片段** —— 完整对话从你粘贴 prompt 到 AI 写完报告，含工具调用框
3. **3 句话感受** —— 任选其中两个问题回答即可：
   - 两个 MCP 是怎么协作的？
   - AI 自动判断用哪个工具，还是要你提示？
   - 哪一次工具调用最有"惊喜感"或"意料之外"？

## 还原（练完想恢复成 lesson 3 单 sqlite 配置）

```bash
git checkout lesson3/project/.mcp.json
```
