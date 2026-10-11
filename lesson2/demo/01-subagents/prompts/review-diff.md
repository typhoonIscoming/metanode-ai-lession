# Review Subagent Prompt 模板

> 复制下面这段，作为 `Agent` 工具调用的 prompt（subagent_type=general-purpose 或 superpowers:code-reviewer，如已安装）。

---

## 任务

对 `lesson1/demo/claude-demo/btc_kline.py` 做一次代码审阅。

## 背景

这是培训课第 1 课的演示脚本：从 Binance 公开接口拉 BTC K 线、用 mplfinance 绘图。已上线作为教学样例，**不是生产代码**——所以"过度健壮性"不是问题，但**示范级的工程素养**必须达标。

仓库约定（详见 `CLAUDE.md`）：

- 所有时间处理必须 UTC，禁止 naive datetime
- 注释和 docstring 一律中文，标识符英文

## 重点关注

1. **时间正确性**：是否所有 datetime / pandas 时间戳都带 tz？是否存在隐式时区转换？
2. **网络健壮性**：HTTP 调用是否设置了 timeout？失败/限流如何处理？
3. **数据完整性**：返回字段不全 / K 线数量为 0 时是否会崩？
4. **可测试性**：是否把"取数"和"绘图"切开了？还是耦合在一个 main 里？
5. **是否违反 CLAUDE.md 的两条硬约束**

## 输出格式

按以下结构返回，不超过 30 行：

```
## 风险列表

| # | 文件:行号 | 风险描述 | 严重度 (高/中/低) | 建议 |
|---|---|---|---|---|

## 整体评价

[2-3 句话：这段代码作为教学样例够不够格，主要短板在哪]
```

## 边界

- 只读 `lesson1/demo/claude-demo/btc_kline.py` 和必要时 `CLAUDE.md`、`.cursor/rules/project-conventions.mdc`
- 不要读 `cursor-demo/`——那是另一份独立的代码，不在审阅范围内
- 不要修改任何文件
