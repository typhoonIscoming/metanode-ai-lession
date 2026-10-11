# 飞书卡片模板

B-14 在此目录放入 5 种 kind + test + error 共 7 个 JSON 模板（见 backend-PRD §2.5 / §3.5）。
模板内使用 `${variable}` 占位符，由 `FeishuWebhookClient` 用 `string.Template` 替换。
