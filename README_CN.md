# $run

> 面向 Coding Agent 的可恢复执行协议：绑定 workstream、状态落在 Markdown、`done` 前验证、从有界 Handoff 续跑——而不是翻昨天的聊天记录。

[![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![Install](https://img.shields.io/badge/install-npx%20skills-6366f1?style=flat-square)](https://skills.sh/kl7sn/run)
[![Agents](https://img.shields.io/badge/agents-Cursor%20%7C%20Claude%20%7C%20Codex-555?style=flat-square)](#支持的-agent)
[![State](https://img.shields.io/badge/state-Markdown%20workspace-lightgrey?style=flat-square)](#workspace)
[![English](https://img.shields.io/badge/docs-English-informational?style=flat-square)](README.md)

遵循 [Agent Skills](https://agentskills.io/) 格式，通过 [skills.sh](https://skills.sh) 安装。

## 是什么

`$run` 是 **工程流程助手** —— 给 Cursor、Claude Code、Codex 用的 skill 协议。

把多步工程收成可恢复闭环：

```text
绑定 workstream → explore / plan / execute → 验证 → 交接 → 继续
```

Durable state 在 **Markdown workspace**（Obsidian 可选）。每个 git 仓根目录保留小型 `.run-state` 会话索引。无控制面，无 SaaS。

## 为什么需要

Agent 擅长写代码，弱在：

- **连续性** —— 换窗口、换工具、隔几天就丢线
- **可追责** —— 没有证据就标 `done`
- **范围控制** —— 偏离计划或漏记 task

GSD、BMAD、Spec-Kit 等「托管全流程」的方案有用，但也容易夺走控制权，流程 bug 难修。

`$run` 让你掌控：**纯文件、显式阶段、该停就停**。

## 核心能力

- **三层模型** —— project → workstream → tasks（`tasks.md` 行）
- **会话粘性** —— 已绑定仓必须走 `$run`，禁止静默局部改代码
- **单写者** —— 只有父 `$run` 写 workspace；subagent 可改代码（优先 worktree）
- **验证门禁** —— `doing → done` 须在执行日志留证据
- **集成闸** —— 全部 task `done` ≠ 可关线；须人工冒烟 + worktree 处置
- **Handoff** —— 从 `context.md` 的 `## Handoff` 续跑，不考古聊天
- **`$run auto`** —— 无人值守推进，设计闸双 agent 共识，真硬停仍停
- **`$run review`** —— 基于 workspace 的协议复盘；内置 **`up`** 维护 skill

## 快速开始

### 1. 安装

```bash
npx skills add kl7sn/run -g
```

会安装 **`run`** + **`up`**。常用参数：

```bash
npx skills add kl7sn/run -g -y              # 非交互
npx skills add kl7sn/run -g -a cursor       # 仅 Cursor
npx skills add kl7sn/run --list             # 预览包内 skill
npx skills update                           # 之后更新
```

本地 clone 贡献者：`./install.sh all`。

### 2. 创建 workstream

在工程仓里：

```text
$run init demo          # 项目容器（一次）
$run new hello          # 项目下新建 workstream
```

或配置 `RUN_WORKSPACE` / `.run-state` 指向已有 workspace。

### 3. 运行

```text
$run                    # 推进 explore → plan → execute
$run auto               # 无人值守（硬停仍生效）
$run review             # 复盘当前 project + up 维护
```

状态行（每次推进回复开头）：

```text
[$run · lang=zh · auto=off · 01-demo/01.01-hello · T01 ready]
```

## 包内 skill

| Skill | 作用 |
| --- | --- |
| [`run`](skills/run/SKILL.md) | 流程协议 —— 绑定、阶段、tasks、Handoff、闸门 |
| [`up`](skills/up/SKILL.md) | Skill 维护 —— `$run review` 第二阶段（默认 apply） |

`$run` **不是**通用 skill 工具集。TDD、grill、领域工具等保持独立、可选。

`run` skill 采用 progressive disclosure：入口 `skills/run/SKILL.md` 保持精简（不超过 500 行），工作区、恢复、执行、auto、review 和参考细节按需放在 `skills/run/protocols/` 下读取。

## 命令

| 命令 | 说明 |
| --- | --- |
| `$run init` [projectId] | 创建项目容器 |
| `$run new` [workstreamId] | 创建嵌套 workstream |
| `$run bind` | 交互重绑本会话 |
| `$run lang` [en\|zh] | 查看或设置文档语言 |
| `$run` | 推进当前阶段 |
| `$run auto` | 无人值守推进 |
| `$run review` [scope] | 协议复盘（默认当前 project）+ `up` |
| `$run review scan-only` | 只写报告，不 patch skill |

## Workspace

路径优先级：`.run-state` → `RUN_WORKSPACE` → 必须显式配置。协议不再隐式回退到 `~/run-workspace`。

```text
<workspace>/
└── Projects/
    └── 01-demo/                    # 项目  NN-<slug>
        ├── project.md
        └── 01.01-hello/            # 任务包  NN.MM-<slug>
            ├── workstream.md
            ├── tasks.md
            ├── context.md          # Handoff · Gotchas · 证据
            └── spec.md             # 可选
```

Review 报告：`Projects/<projectId>/_run-review/YYYY-MM-DD-review.md`

示例：[`examples/01-demo/`](examples/01-demo/) · 模板：[`templates/`](templates/)（中文用 `*.zh.md`）

仓内会话索引（git 根 `.run-state`）：

```yaml
workspace: /absolute/path/to/workspace/Projects/01-demo/01.01-hello
lang: zh
project: 01.01-hello
repo: .
```

## 支持的 Agent

| Agent | 安装目录 |
| --- | --- |
| Cursor | `~/.cursor/skills/` |
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |

`npx skills add kl7sn/run -g -a <agent>` 可指定端。`install.sh` 也支持 `~/.agents/skills/`。

## $run 不是什么

| | |
| --- | --- |
| ❌ 托管 Agent 平台 | ✅ Markdown workspace + skill 协议 |
| ❌ 必须常住的 Issue 系统 | ✅ 可 grep 的 `tasks.md` |
| ❌ 通用 skill 入口 / 注册表 | ✅ 流程助手 + 仅 bundled `up` |
| ❌ 「看起来没问题」就完成 | ✅ 验证 + 关线前人工冒烟 |

## 可选 companion

`$run` 负责编排；阶段纪律 skill 可选：

- **默认：** superpowers（`brainstorming`、`writing-plans`、TDD、`verification-before-completion`）
- **可选：** [mattpocock/skills](https://github.com/mattpocock/skills) —— 如 `grill-with-docs`、`to-tickets`、`code-review`
- **不要** 与他们的 `handoff` / `implement` 双跑，不要把 durable state 迁出 workspace

详见 [`skills/run/SKILL.md`](skills/run/SKILL.md) → *Relationship to other skills*。

## 文档

| 文档 | 作用 |
| --- | --- |
| [`skills/run/SKILL.md`](skills/run/SKILL.md) | 完整 Agent 协议（英文） |
| [`skills/up/SKILL.md`](skills/up/SKILL.md) | Skill 维护 |
| [`docs/design.md`](docs/design.md) | 设计与取舍 |
| [`README.md`](README.md) | English |

## License

[MIT](LICENSE)
