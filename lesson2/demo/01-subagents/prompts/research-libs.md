# Research Subagent Prompt 模板

> 复制下面这段，作为 `Agent` 工具调用的 prompt（subagent_type=general-purpose）。

---

## 任务

对比 `mplfinance` 和 `plotly` 两个 Python 库，给出"画 K 线"场景下的选型建议。

## 背景

第 1 课 demo 当前用的是 `mplfinance`（基于 matplotlib，输出 PNG）。我们在考虑后续课程是否切到 `plotly`（交互式 HTML）。需要一个独立的第二意见：**对培训演示这个具体场景**，哪个更合适。

## 需要回答的问题

1. 两个库各自的核心定位（一句话）
2. 画 K 线 + MA 均线的代码量对比（粗略行数级别）
3. 输出形式差异：静态图 vs 交互图，对培训演示分别有什么利弊
4. 安装/依赖大小、是否需要浏览器渲染
5. **推荐选哪个**？给一个倾向性建议 + 一句话理由

## 输出格式

不超过 20 行。结尾必须有一行明确推荐：`推荐: <mplfinance | plotly>`，不要骑墙。

## 边界

- 可以使用 WebSearch / WebFetch 查官方文档和 README
- 不要写代码，只做选型分析
- 如果两个都不合适，直接说"两个都不合适，原因是 X"，不要硬选
