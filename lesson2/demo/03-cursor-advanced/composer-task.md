# Composer 演示任务

> 把这段整体粘到 Cursor 的 Composer（Ctrl+I）输入框。

---

请在本仓库做一个跨文件的小改动：

1. 在 `lesson1/demo/claude-demo/btc_kline.py` 的文件头部 docstring 之后，添加一行 `__author__ = "AI Course Team"` 常量
2. 在 `lesson1/demo/cursor-demo/btc_kline.py` 的同样位置添加一行 `__author__ = "AI Course Team"` 常量
3. 在 `lesson1/README.md` 的"演示"小节末尾追加一段说明：

   ```
   两份脚本的 `__author__` 字段都已统一为 "AI Course Team"，便于追溯。
   ```

约束：

- 不修改任何函数实现
- 不动 `lesson2/`、`homework/` 目录下的文件
- 严格遵守 `.cursor/rules/project-conventions.mdc`：注释中文、时间 UTC

完成后给我一个跨文件的 diff，我 review 后决定是否 apply。

---

## 演示后 cleanup

学员看完 diff 之后**不要 apply**——这只是演示，让 Composer 退出即可。如果不小心 apply 了，用 `git restore` 还原。
