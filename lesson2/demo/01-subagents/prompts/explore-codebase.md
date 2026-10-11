# Explore Subagent Prompt 模板

> 复制下面这段，作为 `Agent` 工具调用的 prompt（subagent_type=Explore）。

---

## 任务

摸底 `lesson1/demo/` 目录的代码结构。

## 背景

这是一个 AI 开发提效培训课的仓库，第 1 课的 demo 同时存在 `claude-demo/` 和 `cursor-demo/` 两个并排目录，**故意保留差异**作为教学对照——不要把它们当作"应该被合并的重复代码"。

## 需要回答的问题

1. 两个 demo 目录各包含哪些文件？大小级别（几行 / 几十行 / 几百行）？
2. 入口脚本是哪个？跑起来需要哪些依赖？
3. `claude-demo/` 和 `cursor-demo/` 的同名脚本（`btc_kline.py`）在**结构和实现风格**上有哪些显著差异？
4. 是否有测试文件？测试覆盖了哪些场景？

## 输出格式

不超过 15 行。Markdown bullet 列表，每个问题一段答案。**不要**贴代码原文，只要结构性描述。

## 边界

- 只读 `lesson1/demo/` 目录，不要读 `lesson2/`、`homework/` 或仓库根
- 不要修改任何文件
