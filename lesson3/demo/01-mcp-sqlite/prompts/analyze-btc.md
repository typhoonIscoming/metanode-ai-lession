# Demo prompt: 让 Claude 自己写 SQL 给出分析

> **用法**：在 `lesson3/project/` 下启动 Claude Code 后，整段粘贴下面这条 prompt。

---

通过 sqlite MCP 查 `ohlc` 表中 BTCUSDT 过去 30 天的：
- 最高价、最低价、均价、最近收盘价
- 涨跌幅（最近 vs 30 天前）

用一段中文（约 150 字）总结当前趋势。所有 SQL 你自己写，不要问我。

---

## 期望表现

Claude 自动写两三条 `SELECT`（如 `SELECT MAX(high), MIN(low), AVG(close) FROM ohlc WHERE symbol='BTCUSDT'` 等），通过 `read_query` 调用送进 sqlite MCP，拿到聚合结果，再写一段约 150 字的中文趋势总结。

**不应该**做的事：
- 把整张表 dump 出来再口算
- 反过来问"你想我查哪些字段"
- 解释 MCP 是什么
