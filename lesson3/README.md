# 第 3 课：MCP 与外部能力接入

> 课程视频回放：[点击观看](https://appibxs98ig9955.h5.xet.pomoho.com/p/course/video/v_6a1c5580e4b0694c5bcddab2?product_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&course_id=course_2xArq45EVWERVb4oHPYEmCLzHG5&sub_course_id=subcourse_3EUmreviThPpAUC2IJ1NTqoDbk5)

上节课讲了让工具替你做更多事——Hook 自动触发、Subagent 独立跑任务。这节课往前走一步：**让 AI 看见你环境之外的东西**。MCP（Model Context Protocol）是 Anthropic 提出的开放协议，让 Claude 能按需调用外部能力，比如直接查数据库、读文件系统、查 GitHub。

时长约 25 分钟，四个主题：
1. MCP 是什么
2. 接上 sqlite MCP（5 分钟动手）
3. 让 AI 自己写 SQL（5 分钟动手）
4. 反模式 + 作业

> **跟着课件做**：每个"动手做"小节都有可直接复制的命令和 prompt。建议第一遍学习时**真打开终端跟着做一次**，不要只读。

---

## 〇、前置确认（30 秒）

开始前，确认以下各项：

- [ ] Claude Code 已安装（`claude --version` 能跑）
- [ ] `uv` 工具链已安装（`uvx --version` 能跑；没有则步骤 2.1 会装）
- [ ] `ai_lesson` 仓库已 clone 到本地（`ls lesson3/project/seed_db.py` 能找到文件）
- [ ] Python 3.11+（`python --version` 确认）
- [ ] `requests` 库已安装（`pip install requests`；`seed_db.py` 需要它拉 K 线数据，`sqlite3` 和 `pathlib` 是标准库无需安装）
- [ ] 网络能访问 `api.binance.com`（或备用镜像 `data-api.binance.vision`）

全部打勾，继续。

---

## 一、MCP 是什么

**MCP 之于 AI，就像 USB 之于电脑**。电脑本身不会凭空多出键盘、U 盘、摄像头——但插上 USB 接口就有了。MCP 是一套标准接口，让任何人都能写一个"MCP server"，把某项能力（查数据库、搜代码、调 API）暴露给 AI。AI 不需要知道这项能力怎么实现的，只需要知道"我可以调用它"。

MCP 有三类原语：

| 原语 | 是什么 |
|---|---|
| **Tools** | AI 可以主动调用的函数，比如 `read_query`（执行 SQL）、`list_tables` |
| **Resources** | AI 可以读取的数据，比如一张表的 schema、一份文件的内容 |
| **Prompts** | server 提供的现成 prompt 模板，AI 可以按需调用 |

本课只用 **Tools**——因为查数据库是一个动作，不是静态数据。

一个 MCP server 可以同时暴露多个 Tool。`mcp-server-sqlite` 暴露了 `list_tables`、`read_query`、`write_query`、`create_table`、`describe_table`、`append_insight` 六个工具，Claude 根据你的问题自主判断调用哪个，你不需要手动选。

**与 Lesson 2 学过的能力对比**：

| 能力 | 触发方式 | 典型场景 |
|---|---|---|
| **Hook** | 事件驱动（Edit 完自动跑 lint） | 每次 AI 改文件都要做的事 |
| **Subagent** | 主动派遣（你让 AI 去干某件独立任务） | 代码审阅、文档探索 |
| **MCP** | 按需调用（AI 判断需要时主动调用 server） | 查数据库、读文件系统、搜代码 |

核心区别：**Hook 是被动触发，Subagent 是独立派遣，MCP 是让主线 AI 多一双手**。

---

## 二、动手做（5 分钟）：装上 sqlite MCP

**前置**：你正在 `ai_lesson` 仓库根目录。

**步骤 1**：进入 `lesson3/project/` 目录，确认 `uvx` 可用（已装则跳过安装）。

```bash
cd lesson3/project
which uvx || curl -LsSf https://astral.sh/uv/install.sh | sh
```

期望：`which uvx` 输出一个路径（如 `/home/你的用户名/.local/bin/uvx`），或安装脚本运行完毕打印 `uv installed`。安装后**新开一个终端**让 PATH 生效，再 `which uvx` 确认。

> `uvx` 是 `uv` 工具链自带的 runner，相当于 `npx`：它能不事先 pip install、直接从 PyPI 拉包并运行，第一次慢（需要下载），之后本地缓存秒启。

**步骤 2**：拉 90 天 BTC/ETH K 线数据落库。

```bash
python seed_db.py
```

期望 stderr：
```
[seed] BTCUSDT: 写入 90 行
[seed] ETHUSDT: 写入 90 行
[seed] 完成，180 行落库到 .../lesson3/project/prices.db
```

这一步从 Binance 公共 API 拉日线 K 线数据，写入 `prices.db` 的 `ohlc` 表。数据落库后供 Claude 查询用。

**步骤 3**：检查 `.mcp.json`——仓库已经帮你配好了，不需要手写。

```bash
cat .mcp.json
```

期望输出（`args` 数组格式可能为单行或多行，语义相同）：
```json
{
  "mcpServers": {
    "sqlite": {
      "command": "uvx",
      "args": [
        "mcp-server-sqlite",
        "--db-path",
        "./prices.db"
      ]
    }
  }
}
```

这份配置告诉 Claude Code：在这个目录里，有一个叫 `sqlite` 的 MCP server，通过 `uvx mcp-server-sqlite` 启动，连接本地 `./prices.db`。`.mcp.json` 是**项目级**配置，只对 `lesson3/project/` 目录（及其子目录）下启动的 Claude 会话生效；全局用户级配置在 `~/.claude/settings.json`，本课不用改它。

**步骤 4**：在 `lesson3/project/` 目录启动 Claude，验证 sqlite server 已加载。

> **为什么必须 cd 到 `lesson3/project/`？** `.mcp.json` 里 `--db-path ./prices.db` 是**相对路径**，相对的是你启动 `claude` 的目录。在仓库根目录启动会让 MCP server 去找仓库根下的 `./prices.db`，找不到，导致"表不存在"之类的静默失败。

```bash
claude
```

启动后整段粘贴到 Claude 对话框：

```
列出当前可用的 MCP server 和 tool 清单。
```

期望：Claude 回复列出 `sqlite` server 及其工具，包括：

```
sqlite:
  - list_tables
  - read_query
  - write_query
  - create_table
  - describe_table
  - append_insight
```

> 如果工具名和上面略有出入（比如 `execute_query` 而不是 `read_query`），不用担心——`mcp-server-sqlite` 的版本不同工具名略有差异，能用就行。继续用 Claude 实际报出来的名字理解即可。

**排错表**：

| 现象 | 原因 | 解决 |
|---|---|---|
| Claude 说"没有可用 MCP server" | 不在 `lesson3/project/` 目录启动 | 退出（`Ctrl+D`）→ `cd lesson3/project` → 重启 `claude` |
| `command not found: uvx` | 装完 uv 后没刷新 PATH | 关掉当前终端，新开一个；或 `export PATH="$HOME/.local/bin:$PATH"` |
| `prices.db` 不存在 | 没跑步骤 2 | 先 `python seed_db.py`，再重启 `claude` |
| `requests.HTTPError` / 拉不到 K 线 | `api.binance.com` 在当前网络被屏蔽 | 把 `seed_db.py` 里 URL 改成 `https://data-api.binance.vision/api/v3/klines` 重跑 |

---

## 三、动手做（5 分钟）：让 AI 自己写 SQL

在同一会话里继续（不要 `/clear`）。如果不小心 `/clear` 了，没事——退出 Claude（`Ctrl+D`）后 `cd lesson3/project && claude` 重启即可。整段粘贴：

```
通过 sqlite MCP 查 ohlc 表中 BTCUSDT 过去 30 天的最高、最低、均价、最近收盘价，
用一段话总结趋势。
```

期望对话片段（**你的数字会和这里不一样，30 天行情每天都在变**）：

> Claude 会自动调用 sqlite MCP 的工具完成查询：

```
⏺ MCP(sqlite/read_query)
  ⎿ [{'max_high': 81323.52, 'min_low': 67732.01, 'avg_close': 75663.88, 'latest': 80933.55}]

⏺ BTC 过去 30 天最高 81,323.52 USDT，最低 67,732.01 USDT，
  均价 75,663.88 USDT；最近收盘 80,933.55 USDT，高于均价约 6.96%，
  说明市场在经历大幅震荡（高低差约 20%）后，近期价格已从均价显著回升并接近
  本周期高点，呈现出短期强势反弹态势，但距历史高点仍有一定空间，投资者
  可关注能否在 81,000 USDT 上方确立支撑。
```

观察三点：

- Claude **自己写了 SQL**（你没给它），通过 `read_query` 调用送进 sqlite MCP
- 主线对话里只看到一次 MCP 工具调用 + 文字总结，**没有把整张表 dump 出来**
- 这就是 MCP 的价值：**给 AI 一个"会写 SQL 的能力接口"，而不是把数据塞进 prompt**

---

## 四、关键认知

**MCP 给 AI 的是能力的接口，不是工具的实现。** `mcp-server-sqlite` 实现了"执行 SQL"这件事，Claude 决定"什么时候用、用哪条 SQL"。AI 不需要理解 SQLite 的内部实现，只需要知道它有 `read_query` 这把手。这和调用库函数是一样的道理——你知道 `max()` 的入参/返回值，不需要知道它的底层排序算法。

**与 Hook 的对比**：Hook 是被动的，AI 改了文件，lint 自动跑，AI 看到输出再决定要不要修——AI 没有"要不要触发"的权力。MCP 是主动的，AI 判断"我现在需要查数据库"才调用，不用就不调用。

**与 Subagent 的对比**：Subagent 是把整个任务甩给一个独立上下文去跑；MCP 是让主线 AI 多一双手，上下文连续。查一条 SQL → 用结果继续对话，这种"顺手调用"适合 MCP，不适合 Subagent。

记忆口诀：

```
Hook  = 有事发生 → 自动做
Subagent = 把整件事交给另一个 AI 去干
MCP   = AI 伸手用一个外部能力，手缩回来继续说话
```

---

## 五、权限与安全边界

`mcp-server-sqlite` 默认同时暴露读写工具：`read_query`、`write_query`、`create_table`、`append_insight` 等。教学场景里我们都开着方便演示；生产环境你应当收紧：

| 场景 | 推荐做法 |
|---|---|
| AI 只需要查询历史数据 | 在 server 包装层只暴露 `read_query`，或用只读用户连 DB |
| AI 需要写入分析结果 | 显式给 `append_insight`，不开 `write_query`（避免任意改表） |
| AI 操作生产数据库 | **永远不要** —— 用副本或 read replica，写入走审批流 |

**最小权限原则**：只给 AI 完成当前任务需要的最少能力。接 MCP 之前先问"如果 AI 把这个 server 的所有工具都用一遍，最坏结果是什么"。

---

## 六、反模式（3 条）

**1. 把 MCP 当 prompt 替代品**

数据能直接写进 prompt 的，偏要包一层 MCP server 传进来。比如一份固定的配置文件、一段几百字的背景说明——这些完全可以直接粘进 prompt，却绕道 MCP 走一次 IPC 调用。MCP 的价值在于 **按需调用外部动态能力**（执行 SQL、调实时 API），不是替代 prompt 喂静态数据。低带宽场景多绕一圈只会慢，不会更好。

**2. 给一个项目接 20 个 MCP server**

每个 MCP server 启动时占一个子进程，所有 server 暴露的 tool 合并进 AI 的上下文。tool 数量一旦爆炸，Claude 在选工具时变慢、选不准，启动开销也让每次会话都更重。解决方法是**按需精简**：当前任务用到几个就接几个，其他的临时加、用完就移，不要把所有可能用到的 server 全挂在一份配置里。

**3. 让 AI 直连生产数据库或真实交易所写接口**

`write_query` 开着的时候，一句"帮我清理重复数据"可能变成 `DELETE FROM ohlc WHERE ...`，回滚成本很高。生产写接口更不用说——量化策略出一次 bug，账户清零。**测试/演示一律用副本数据**，生产写入永远走人工审核。

---

## 七、作业

> **完整任务说明**：[homework/task1-second-mcp/README.md](./homework/task1-second-mcp/README.md)

**任务：再接一个 MCP server**（filesystem 或 GitHub 任选），让 Claude 同时用两个 MCP 完成一次组合查询：读一份本地文件或 GitHub README，结合 sqlite 里的 BTC/ETH 行情，写一段对比报告。

30 分钟内可完成，**不要求写 Python 代码**，主要是配置 `.mcp.json` + 设计 prompt。

提交内容：
1. 修改后的 `.mcp.json`（如含 token/PAT，留空占位符再提交）
2. 完整对话片段：从粘贴 prompt 到 AI 写完报告
3. 3 句话感受：两个 MCP 怎么协作的？AI 自动判断了什么时候用哪个工具？还是你得在 prompt 里提示它？

---

## 学完这课，你能做什么

- 在 `lesson3/project/` 下配一份 `.mcp.json`，让 Claude 直接 SQL 查本地 SQLite，不用把数据 dump 进 prompt
- 让 AI 面对陌生数据库时自己写 SQL、自己聚合、自己给出分析，全程不需要你动一行 SQL
- 区分 Hook（事件触发）/ Subagent（独立派遣）/ MCP（按需调用）三种模式，选对场景用对工具
- 判断什么场景适合接 MCP、应当开哪些权限、如何避免把生产能力暴露给 AI

---

## 延伸阅读

### 协议本身

- MCP 官方文档与协议规范：[https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)
- 本课使用的 sqlite server 源码：[modelcontextprotocol/servers · src/sqlite](https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite)

### 去哪里找别的 MCP server

按"官方度"从高到低排：

| 来源 | 网址 | 说明 |
|---|---|---|
| **MCP 官方 servers 目录** | [modelcontextprotocol.io/examples](https://modelcontextprotocol.io/examples) | Anthropic 背书的参考实现，质量最稳 |
| **官方 servers 仓库** | [github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | filesystem / github / fetch / memory / git 等核心 server |
| **awesome-mcp-servers** | [github.com/punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | 社区聚合，最大最杂，按类别分类 |
| **mcp.so** | [mcp.so](https://mcp.so/) | Web 注册表，可分类筛选、看 README 截图 |
| **Smithery** | [smithery.ai](https://smithery.ai/) | MCP server 注册中心 + 一键安装 CLI |
| **Glama** | [glama.ai/mcp/servers](https://glama.ai/mcp/servers) | 另一个 web 注册表，带评分和使用量 |
| **Anthropic Connectors Directory** | claude.ai → Settings → Connectors | 桌面/网页客户端能直接挂的官方目录 |

实操时记住：包本身只来自两个地方——

- **Node 系**（最多）：`npx -y @modelcontextprotocol/server-xxx`，发布在 npm
- **Python 系**：`uvx mcp-server-xxx`，发布在 PyPI

判断"这个 server 能不能用"的最快办法：看它给的 `claude mcp add` 一行命令，把 `command` + `args` 抄到 `.mcp.json` 即可。
