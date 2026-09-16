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

账本落在 **Obsidian Markdown 库**；每个代码仓根目录只保留小型 `.run-state` 会话索引，并指向该库。无控制面，无 SaaS。

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
- **验收冻结** —— 进 execute 前确认通过线，之后闲聊不得改软
- **实现审核** —— 只读审核 agent 对照 Acceptance 证伪，通过后才进人工冒烟
- **审核独立成文** —— 验收与回合都写在 `review.md`，`context.md` 只留状态镜像
- **项目级知识继承** —— `project.md` 只存稳定事实和坑位*索引*，细节留在踩坑的那条线
- **集成闸** —— 全部 task `done` ≠ 可关线；须人工冒烟 + worktree 处置
- **Handoff** —— 从 `context.md` 的 `## Handoff` 续跑，不考古聊天
- **`$run auto`** —— 无人值守推进，设计闸双 agent 共识，真硬停仍停

### 强绑定

- **一会话 ↔ 一 workstream ↔ 一主 worktree** —— 禁止同会话推进多条线
- **新会话必须绑定** —— 恢复或选择 workstream 后才能 explore / plan / execute
- **缺失 worktree 硬停** —— `worktree_status: missing` 禁止改代码；不得回退到主工作区

## 快速开始

### 1. 安装

```bash
npx skills add kl7sn/run -g
```

会安装 **`run`**。常用参数：

```bash
npx skills add kl7sn/run -g -y              # 非交互
npx skills add kl7sn/run -g -a cursor       # 仅 Cursor
npx skills add kl7sn/run --list             # 预览包内 skill
npx skills update                           # 之后更新
```

本地 clone 贡献者：`./install.sh all`。

### 2. 指向 Obsidian 库，再创建 workstream

账本写在 Obsidian 库里（`RUN_WORKSPACE` 或 `.run-state` 的 `workspace:`）。在已绑定的代码仓里：

```text
$run init demo          # 在库里建项目容器（一次）
$run new hello          # 项目下新建 workstream
```

`.run-state` 写在**代码仓** git 根；`project.md` / `tasks.md` / … 落在 Obsidian 库。

### 3. 运行

```text
$run                    # 推进 explore → plan → execute
$run auto               # 无人值守（硬停仍生效）
```

状态行（每次推进回复开头）：

```text
[$run · lang=zh · auto=off · 01-demo/01.01-hello · wt=none · T01 ready]
```

## 包内 skill

| Skill | 作用 |
| --- | --- |
| [`run`](skills/run/SKILL.md) | 流程协议 —— 绑定、阶段、tasks、Handoff、闸门 |

`$run` **不是**通用 skill 工具集。TDD、grill、领域工具等保持独立、可选。

`run` skill 采用 progressive disclosure：入口 `skills/run/SKILL.md` 保持精简（不超过 500 行），工作区、恢复、执行、auto 和参考细节按需放在 `skills/run/protocols/` 下读取。

## 命令

| 命令 | 说明 |
| --- | --- |
| `$run init` [projectId] | 在 Obsidian 库创建项目容器 |
| `$run new` [workstreamId] | 创建嵌套 workstream |
| `$run bind` | 交互重绑本会话 |
| `$run accept` … | 起草或修订冻结验收 |
| `$run review` | 发起只读实现审核 |
| `$run lang` [en\|zh] | 查看或设置文档语言 |
| `$run` | 推进当前阶段 |
| `$run auto` | 无人值守推进 |

## Workspace

状态分两处落地，不要混：

- **代码仓库（git 根）**：只放 `.run-state` 会话索引（绑定哪条任务包、哪个 worktree）。
- **Obsidian 工作区（Markdown 库）**：放全部账本（`project.md` / `tasks.md` / `context.md` / `review.md` 等）。`.run-state` 的 `workspace:` 指向这个库。

路径优先级：`.run-state` → `RUN_WORKSPACE` → 必须显式配置。协议不再隐式回退到 `~/run-workspace`。

```text
<code-repo>/.run-state              # 仅会话索引，在 git 仓根

<obsidian-vault>/                   # Obsidian 库 = RUN_WORKSPACE
└── Projects/
    └── 01-demo/                    # 项目  NN-<slug>
        ├── project.md              # 任务包+worktree · 稳定事实 · 坑位索引
        └── 01.01-hello/            # 任务包  NN.MM-<slug>
            ├── workstream.md
            ├── tasks.md
            ├── context.md          # Handoff · Gotchas · 关键决策 · 执行日志
            ├── review.md           # Acceptance · ReviewIndex · Claims · ReviewThread
            └── spec.md             # 可选，输入契约
```

示例：[`examples/01-demo/`](examples/01-demo/) · 模板：[`templates/`](templates/)（中文用 `*.zh.md`）

仓内会话索引（git 根 `.run-state`）示例：

```yaml
workspace: /absolute/path/to/obsidian-vault/Projects/01-demo/01.01-hello
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
| ❌ 通用 skill 入口 / 注册表 | ✅ 仅流程助手 |
| ❌ 「看起来没问题」就完成 | ✅ 验证 + 关线前人工冒烟 |

## 可选 companion

`$run` 负责编排；阶段纪律 skill 可选：

- **默认：** superpowers（`brainstorming`、`writing-plans`、TDD、`verification-before-completion`）
- **可选：** [mattpocock/skills](https://github.com/mattpocock/skills) —— 如 `grill-with-docs`、`to-tickets`、`code-review`
- **不要** 与他们的 `handoff` / `implement` 双跑，不要把 durable state 迁出 workspace

详见 [`skills/run/SKILL.md`](skills/run/SKILL.md) → *Companion skills*。

## 文档

| 文档 | 作用 |
| --- | --- |
| [`skills/run/SKILL.md`](skills/run/SKILL.md) | 入口/精简协议；细节见 [`skills/run/protocols/`](skills/run/protocols/) |
| [`docs/design.md`](docs/design.md) | 设计与取舍 |
| [`README.md`](README.md) | English |

## License

[MIT](LICENSE)
