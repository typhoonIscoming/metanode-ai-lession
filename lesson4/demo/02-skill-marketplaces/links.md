# Skill 市场速览（lesson4 §二 配套链接）

| 来源 | URL | 一句话定位 |
|---|---|---|
| Anthropic 官方 skills | https://github.com/anthropics/skills | reference skill 集合，最权威 |
| Superpowers | https://github.com/obra/superpowers | 方法论框架，lesson 2 已装 |
| Everything Claude Code (ECC) | https://github.com/affaan-m/everything-claude-code | Claude Code 增强包，含一组工程类 skill |
| skill.sh | https://skill.sh | 社区聚合站，按主题分类 |
| skillsmp | https://skillsmp.com | 另一个社区聚合站，规模较小，垂直领域 |

## 安装方式速记

- 官方仓库 + Superpowers + ECC：通过 Claude Code 内 `/plugin` 命令安装 marketplace
- skill.sh / skillsmp：手动复制 SKILL.md 到 `~/.claude/skills/<name>/SKILL.md`，然后 `/skill <name>` 调用

## 选择心法

- 找 reference 实现 → 官方仓库
- 找 TDD/code-review/brainstorming 这类工作流 → Superpowers
- 找代码审查/build/lint 这类工程 skill → ECC
- 找冷门垂类（量化、生信、运维特殊场景） → skill.sh / skillsmp 搜
