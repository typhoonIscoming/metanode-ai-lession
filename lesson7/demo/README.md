# 演示：Agent Teams + Hermes 配置样例

本目录是 lesson 7 课堂演示的参考资料——讲师课上不会逐字读这些文件，但学员课后想自己上手时**这两份样例就是起点**。

| 子目录 | 内容 | 课后用途 |
|---|---|---|
| `01-agent-teams/` | Claude Code Agent Teams 启动 prompt 样例集 + settings.json 片段 + 一份小 team 配置示例 | 想跑通 §六.A 作业的学员直接拷过去改改用 |
| `02-hermes/` | Hermes Agent 安装 / 配置 / 切模型样例：`config.yaml` 片段 + `.env` 模板 + Telegram 网关启动命令 | 想跑通 §六.B 作业的学员直接拷过去改改用 |

## 怎么用

```bash
cat lesson7/demo/01-agent-teams/spawn-prompts.md     # 4 个起 team 的 prompt 范本
cat lesson7/demo/01-agent-teams/settings.json        # ~/.claude/settings.json 片段
cat lesson7/demo/02-hermes/config.yaml               # ~/.hermes/config.yaml 片段
cat lesson7/demo/02-hermes/env.example               # ~/.hermes/.env 模板（不含真 key）
```

## 注意

`01-agent-teams/` 里的 prompt 不是"跑一次就能复刻"的脚本——Agent Teams 每次起 team 名字、teammates ID 都不一样，落盘在 `~/.claude/teams/<随机名>/`，这是设计如此。课后**你自己电脑上跑一次** > 死读这些 prompt。

`02-hermes/.env.example` 里的 key 全是占位符。真实 key 务必只放在 `~/.hermes/.env`（Hermes 默认 0600 权限，不进 git）。

## 与课堂的关系

讲师现场演示按 README §二、§三 走，**不会照着 demo 文件念**。这两个 demo 子目录是为**你课后自己跑一遍**准备的——讲师演示完你回家想动手，照着这两份样例最快。

## 一个真实 Hermes 产出样例

`lesson7/hermes-project/` 是讲师用 Hermes 跑出来的一个完整小项目——Binance Token Heatmap（Express 后端 + 前端热力图，定时拉取 24h 成交额前 100 token）。**不是"hello world"，是真能跑能扩的东西**。课后想看 Hermes 实际能产出什么级别的代码，进那个目录翻一翻 src / test / scripts 就有答案。
