# 学生判断：对每条建议的取舍

> 作业的关键产出**不是"有没有派 subagent"**，而是**"你怎么对待它返回的每条建议"**。
> AI 给的审阅结论不是金科玉律——有的真问题、有的伪问题、有的判断对但严重度判得不准。
> 必须逐条过，标"采纳 / 部分采纳 / 驳回"，并写理由。

## 逐条判断

### #1 — `datetime.now()` 无 UTC 时区

- **判断：✅ 采纳**
- **理由**：`CLAUDE.md` 明文规定时间必须 UTC。第 70 行的 `datetime.now().timestamp()` 在不同时区机器上会产生**完全不同**的 epoch 毫秒数，跨机协作时直接出 bug。这是真问题。
- **修法**：
  ```python
  from datetime import datetime, timedelta, timezone
  end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
  start_ms = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
  ```

### #2 — `datetime.fromtimestamp()` 无 tz

- **判断：✅ 采纳**
- **理由**：第 93 行从 Binance 收到的 epoch 毫秒数是 UTC，但 `fromtimestamp()` 不带 tz 时按**本地时区**解释，结果 DataFrame 的 Date 列在不同机器上数值不同。和 #1 同性质。
- **修法**：
  ```python
  "Date": datetime.fromtimestamp(item[0] / 1000, tz=timezone.utc),
  ```

### #3 — `pd.DatetimeIndex` 未指定 `tz="UTC"`

- **判断：⚠️ 部分采纳**
- **理由**：subagent 的描述偏严，但**结论是对的**。如果 #1 #2 已修，源 datetime 都是 tz-aware UTC，pandas 会自动保持时区——这一行其实**已经隐含 UTC**，不必再显式 `tz="UTC"`。但为了**让代码自己说话**（不依赖前面的修复），加一句 `pd.to_datetime(df.index, utc=True)` 是好习惯。
- **修法**：保留这条修改，但把它当成"防御性表达"而不是"修 bug"。

### #4 — HTTP 无重试

- **判断：❌ 驳回（在本场景下）**
- **理由**：这是**生产代码的诉求**，不是教学样例的诉求。Binance 这个公开接口稳定性很高，加重试和退避会让脚本读起来更复杂——演示重点不在网络治理上，**会偏离教学焦点**。课程后续讲到 MCP / 工作流时再展开"健壮性"话题更合适。
- **备注**：如果是**学员的真实生产项目**遇到同样建议，则应该采纳。

### #5 — "缺少 `from datetime import timezone`，代码无法导入 timezone 模块"

- **判断：❌ 驳回（措辞错误）**
- **理由**：subagent 的措辞**不严谨**。当前代码**根本没有用** `timezone`，所以"无法导入"是个伪问题——目前代码运行起来没毛病。**真正的因果**应该这样表述：
  > "如果采纳 #1 #2，需要补充 `from datetime import timezone`。"
- 它把"修复 #1 #2 的前置条件"包装成了一个独立的**高严重度**问题——属于**虚高警报**。
- **正确做法**：把 #5 合并进 #1 #2 的修法步骤里，不单列。

## 整体反思

5 条建议里：

- 真有用的：3 条（#1、#2、#3）
- 严重度判得偏高的：1 条（#5 应是低，被报成高）
- 完全不该提的（在本场景下）：1 条（#4）

**这就是要"派 subagent 审阅"而不是"让 AI 直接帮你修"的核心理由**：审阅结论需要人决策。如果让主线 AI 直接动手修，它会**全部照做**，把 5 条建议都改进代码——结果可能引入不必要的复杂度（重试逻辑），还会显得"修复了一个不存在的导入问题"那种 PR review 时让人发笑的改动。

## 是否对 lesson1 真做修复？

不在本作业范围内——本作业的产出物**只是审阅结论 + 判断**。
是否真的把这些修复 push 进 `lesson1/demo/claude-demo/btc_kline.py`，是 lesson1 的事，需要单独决策（教学考虑：是否要"故意保留"违规当反例？还是修干净作正面样例？）。
