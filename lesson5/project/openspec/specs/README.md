# project/openspec/

OpenSpec 风格工作目录。两个子目录：

- `specs/` — 项目**当前**已有的规范（source of truth）。每个文件描述一个领域的"现在是什么样"。
- `changes/` — 具体的变更提案。每个变更一个目录，含 5 段：proposal / specs / design / tasks / implementation note。

变更走完后，把 `changes/<id>/specs.md` 的内容**合并**到 `specs/<相关文件>.md`，让 specs/ 始终反映现状。

> 这一套约定**不需要安装 OpenSpec CLI**。本课用纯文件演示流程；如果你的项目想用 CLI 自动化，参考 https://github.com/<openspec-repo>。
