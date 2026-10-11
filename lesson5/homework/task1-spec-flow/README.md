# 任务 1：用 OpenSpec 五段为一个 feature 写 spec（必做）

## 时长

30 分钟内可完成。**不要求实现底层代码**（实现是加分项）。

## 任务

挑一个你**真正想加**到 `lesson5/project/` 的 feature，按 OpenSpec 五段全流程写一遍：proposal → specs → design → tasks → (implement)。

### 候选 feature 方向（任选其一或自选）

| 方向 | 大致范围 |
|---|---|
| 新策略 | RSI 反转 / MACD / 布林带突破等 |
| 新指标 | 把 `cumulative_return` 改成"年化收益率"输出 |
| 新数据源 | 接入 ETH 之外的另一个币种 |
| 报表导出 | `run_backtest` 多一个 `to_markdown(path)` 方法 |
| 多周期 | 一次性回测 1d / 1h / 5m 三个粒度 |

### 步骤

1. 在仓库新建 `lesson5/homework/task1-spec-flow/<your-change-id>/`，例如 `add-rsi-strategy`
2. 复制 `proposal.md.template` 为 `proposal.md`，按模板填
3. 自己写 `specs.md`、`design.md`、`tasks.md`（也可参考课堂 `lesson5/project/openspec/changes/add-dual-ma-strategy/` 的结构）
4. **加分项**：自己实现 + 跑一次自测，写 `IMPLEMENTATION.md`（实现代码放在 `lesson5/project/openspec/changes/<feature-name>/` 目录）

## 提交内容

1. 4-5 个 markdown 文件（proposal / specs / design / tasks，加分项含 IMPLEMENTATION）
2. 3 句话设计回顾：哪一段最难写？哪一段帮你最早发现"我其实没想清楚"？

## 评分维度

- proposal 是否能 30 秒读完抓到痛点
- specs 是否给出**可验证**的接口约定（"返回 dict 含 sharpe 字段" 而不是"输出指标"）
- design 是否真的列了**至少一个**备选并说明为什么没选
- tasks 是否拆到 5 步以内、每步都是动作（写 X / 跑 Y / 改 Z）

## 参考

- 课堂完整示例：`lesson5/project/openspec/changes/add-dual-ma-strategy/`（5 段全文）
- OpenSpec 概念：`docs/superpowers/specs/2026-05-05-lesson3-7-design.md` §4.3
