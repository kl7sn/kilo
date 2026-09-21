<p align="center">
  <img src="docs/images/kilo-mark.svg" width="72" height="72" alt="kilo" />
</p>

<h1 align="center">kilo</h1>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License: MIT" /></a>
  <a href="https://skills.sh/kl7sn/kilo"><img src="https://img.shields.io/badge/install-npx%20skills-6366f1?style=flat-square" alt="Install" /></a>
  <a href="#支持的-agent"><img src="https://img.shields.io/badge/agents-Cursor%20%7C%20Claude%20%7C%20Codex-555?style=flat-square" alt="Agents" /></a>
  <a href="#workspace"><img src="https://img.shields.io/badge/state-Markdown%20workspace-lightgrey?style=flat-square" alt="State" /></a>
</p>

<p align="center">
  <a href="README.md">English</a>
</p>

<p align="center"><strong>给 Coding Agent 用的执行协议。</strong></p>

<p align="center">
  绑一条线，把状态写在 Markdown 里；没有验证依据不标 <code>done</code>；<br />
  下次从 Handoff 接着做，不用翻旧聊天记录。
</p>

<p align="center">
  <a href="https://skills.sh/kl7sn/kilo"><strong>安装 kilo</strong></a>
  · 按
  <a href="https://agentskills.io/">Agent Skills</a>
  格式，经
  <a href="https://skills.sh">skills.sh</a>
  安装
</p>

## 是什么

`/kilo` 是给 Cursor、Claude Code、Codex 用的工程流程 skill。

多步任务可以中断，也可以接着做：

```text
绑定这条线 → explore / plan / execute → 验证 → 交接 → 继续
```

![/kilo main flow](docs/images/kilo-readme-main-flow.svg)

状态文档放在 **Obsidian Markdown 库**；代码仓根目录只留一个小 `.kilo-state`，指向这个库。没有控制面，也不是 SaaS。

## 为什么需要

Agent 写代码很强，容易出问题的是：

- **连续性** —— 换窗口、换工具、隔几天，上下文就断了
- **可核对** —— 没有证据也标 `done`
- **范围** —— 计划跑偏，或漏记 task

GSD、BMAD、Spec-Kit 这类「托管全流程」的方案能用，但常常喧宾夺主，流程出了问题不好修。

`/kilo` 把状态记在文件里，阶段划分清楚；该停的地方会停，不会闷头往下跑。

## 它能干什么

- **三层结构** —— project → line（这条线）→ tasks（`tasks.md` 里一行一项）
- **会话绑定** —— 仓库绑定后必须走 `/kilo`，不能绕过协议改代码
- **状态文档只由父 `/kilo` 写入** —— subagent 可以改代码（优先用 worktree）
- **完成须有证据** —— `doing → done` 要在执行日志里留下验证记录
- **先冻结验收再执行** —— 进入 execute 前先定死通过标准，之后闲聊不能放宽
- **先实现审核再人工冒烟** —— 只读审核对照 Acceptance，通过后再做人工冒烟
- **验收与审核分开存放** —— 验收和审核回合写在 `review.md`；`context.md` 只保留状态镜像
- **项目级知识可继承** —— `project.md` 留稳定事实和已知问题索引；细节仍在原 line
- **任务全完成不等于可以关闭这条线** —— 还要人工冒烟，并处理 worktree（合并 / 保留 / 清理等）
- **从 Handoff 续跑** —— 读 `context.md` 的 `## Handoff`，不翻旧聊天
- **`/kilo auto`** —— 可以无人值守推进；设计评审需要双 agent 达成共识；碰到硬停止条件仍会停

### 绑定规则（必须遵守）

- **一个会话只绑一条 line、一个主 worktree** —— 同一会话里不要同时推进多条
- **先绑定再推进** —— 还没恢复或还没选定 line，就不要做 explore / plan / execute
- **worktree 缺失则停止** —— `worktree_status: missing` 时禁止改代码，也不要退回主工作区凑合

## 快速开始

### 1. 安装

```bash
npx skills add kl7sn/kilo -g
```

装上的是 **`kilo`**。常用参数：

```bash
npx skills add kl7sn/kilo -g -y              # 非交互
npx skills add kl7sn/kilo -g -a cursor       # 只给 Cursor
npx skills add kl7sn/kilo --list             # 看包里有什么
npx skills update                           # 之后更新
```

### 2. 指向 Obsidian 库，再新建一条线

状态文档写在 Obsidian 库里（`KILO_WORKSPACE`，或 `.kilo-state` 的 `workspace:`）。在已绑定的代码仓里：

```text
/kilo init demo          # 在库里建项目（做一次即可）
/kilo new hello          # 在项目下新建一条线
```

`.kilo-state` 在**代码仓**的 git 根目录；`project.md` / `tasks.md` 等落在 Obsidian 库。

### 3. 开始使用

```text
/kilo                    # 推进 explore → plan → execute
/kilo auto               # 无人值守（硬停止条件仍然生效）
```

只读看板（不编辑）。浏览器或原生窗口：

```bash
python3 view/serve.py --root "$KILO_WORKSPACE"
# 打开 http://127.0.0.1:8765

pip install -r view/requirements.txt
python3 view/app.py --root "$KILO_WORKSPACE"
```

每次推进时，回复**末尾**空一行，再出状态行，再空一行，再单独写 `wt`（Markdown 否则会把两行收成一段）：

```text
[/kilo · lang=zh · auto=off · line=01-demo/01.01-hello · ready: 写 hello 示例]

wt=none
```

## 包内 skill

| Skill | 作用 |
| --- | --- |
| [`kilo`](skills/kilo/SKILL.md) | 流程协议：绑定、阶段、tasks、Handoff、检查点 |

`/kilo` **不是**万能工具箱。TDD、grill、领域工具各自独立。

入口 `skills/kilo/SKILL.md` 写得较短（不超过 500 行）；细节需要时再读 `skills/kilo/protocols/`。

## 命令

| 命令 | 说明 |
| --- | --- |
| `/kilo init` [projectId] | 在库里创建项目 |
| `/kilo new` [lineId] | 在项目下新建一条线 |
| `/kilo bind` | 重新绑定当前会话 |
| `/kilo adopt` [path] | 把已有 git worktree 登记成当前线主树（仅 `missing` / `none` / `pruned`） |
| `/kilo up` | 把当前对话分类沉淀到 project / workspace 事实或现有 skill |
| `/kilo accept` … | 起草或修订已冻结的验收标准 |
| `/kilo review` | 发起只读实现审核 |
| `/kilo lang` [en\|zh] | 查看或设置文档语言 |
| `/kilo` | 推进当前阶段 |
| `/kilo auto` | 无人值守推进 |

## Workspace

状态分两处存放，不要混用：

- **代码仓（git 根）**：只有 `.kilo-state`——记录绑了哪条 line、哪个 worktree。
- **Obsidian 库**：全部状态文档（`project.md` / `tasks.md` / `context.md` / `review.md` 等）。`.kilo-state` 的 `workspace:` 指向这里。

![Two landing places: code repo vs Obsidian vault](docs/images/kilo-readme-two-places.svg)

路径怎么找：先看 `.kilo-state`，再看旧的 `.run-state`，再看 `KILO_WORKSPACE` / 旧的 `RUN_WORKSPACE`；都没有就需要显式配置。不会悄悄落到 `~/run-workspace`。

```text
<code-repo>/.kilo-state              # 仅会话索引，在 git 仓根

<obsidian-vault>/                   # Obsidian 库 = KILO_WORKSPACE
└── Projects/
    └── 01-demo/                    # 项目  NN-<slug>
        ├── project.md              # line 与 worktree · 稳定事实 · 已知问题索引
        └── 01.01-hello/            # line  NN.MM-<slug>
            ├── line.md
            ├── tasks.md
            ├── context.md          # Handoff · Gotchas · 关键决策 · 执行日志
            ├── review.md           # Acceptance · ReviewIndex · Claims · ReviewThread
            └── spec.md             # 可选的输入约定
```

示例：[`examples/01-demo/`](examples/01-demo/) · 模板：[`templates/`](templates/)（中文用 `*.zh.md`）

`.kilo-state` 大致如下：

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

只要某一个端：`npx skills add kl7sn/kilo -g -a <agent>`。

## /kilo 不是什么

| | |
| --- | --- |
| ❌ 托管 Agent 平台 | ✅ Markdown workspace + skill 协议 |
| ❌ 必须天天打开的 Issue 系统 | ✅ 能用 grep 搜的 `tasks.md` |
| ❌ 通用 skill 入口 | ✅ 只管流程 |
| ❌ 「看起来没问题」就算完 | ✅ 验证 + 关闭这条线前做人工冒烟 |

## 可选 companion

`/kilo` 负责编排；阶段纪律类 skill 可选：

- **默认：** superpowers（`brainstorming`、`writing-plans`、TDD、`verification-before-completion`）
- **按需：** [mattpocock/skills](https://github.com/mattpocock/skills) —— 例如 `grill-with-docs`、`to-tickets`、`code-review`
- **不要** 和他们的 `handoff` / `implement` 同时开；也不要把 durable state 挪出 workspace

详见 [`skills/kilo/SKILL.md`](skills/kilo/SKILL.md) → *Companion skills*。

## 文档

| 文档 | 作用 |
| --- | --- |
| [`skills/kilo/SKILL.md`](skills/kilo/SKILL.md) | 入口；细节见 [`protocols/`](skills/kilo/protocols/) |
| [`docs/design.md`](docs/design.md) | 设计取舍 |
| [`README.md`](README.md) | English |

## 从 `run` 迁移

以前叫 **`run`**（`kl7sn/run`）。请重新安装：

```bash
npx skills add kl7sn/kilo -g
```

会话文件改为 **`.kilo-state`**（仍会读旧的 `.run-state`）。环境变量改为 **`KILO_WORKSPACE`** / **`KILO_LANG`**（仍会读旧的 `RUN_*`）。下次成功写入绑定时会落盘 `.kilo-state`。

## License

[MIT](LICENSE)
