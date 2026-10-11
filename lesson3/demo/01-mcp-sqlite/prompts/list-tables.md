# Demo prompt: 列出 sqlite MCP 暴露的工具与表

> **用法**：在 `lesson3/project/` 下启动 Claude Code 后，整段粘贴下面这条 prompt。

---

我现在挂载了一个 sqlite MCP server，请：

1. 列出它暴露的所有工具（list_tables / read_query / write_query / create_table / describe_table / append_insight）
2. 用其中一个工具列出 `prices.db` 的所有表
3. 对每张表，告诉我列名和类型

不要解释 MCP 是什么，直接干活。

---

## 期望表现

Claude 调用 `list_tables` 列出 `ohlc` 表，然后用 `describe_table` 或 `read_query` (`PRAGMA table_info(ohlc)`) 拿到 7 列定义：symbol / open_time / open / high / low / close / volume。

不应该把整张 ohlc 表的数据 dump 出来。
