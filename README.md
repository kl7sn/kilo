# $run

> Durable execution for coding agents. Bind a workstream, keep state in Markdown, verify before `done`, and resume from a bounded Handoff — not from yesterday's chat.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![Install](https://img.shields.io/badge/install-npx%20skills-6366f1?style=flat-square)](https://skills.sh/kl7sn/run)
[![Agents](https://img.shields.io/badge/agents-Cursor%20%7C%20Claude%20%7C%20Codex-555?style=flat-square)](#supported-agents)
[![State](https://img.shields.io/badge/state-Markdown%20workspace-lightgrey?style=flat-square)](#workspace)
[![中文](https://img.shields.io/badge/docs-中文-informational?style=flat-square)](README_CN.md)

Skills follow the [Agent Skills](https://agentskills.io/) format and install via [skills.sh](https://skills.sh).

## What it is

`$run` is an **engineering process assistant** — a skill protocol for Cursor, Claude Code, and Codex.

It turns multi-step work into a recoverable loop:

```text
bind workstream → explore / plan / execute → verify → hand off → continue
```

Durable state lives in a **Markdown workspace** (Obsidian optional). Each git repo keeps a small `.run-state` index for session binding. No control plane. No SaaS.

## Why it exists

Coding agents are good at writing code. They are weak at:

- **Continuity** — losing the thread between chats, tools, and weekends
- **Accountability** — marking work `done` without evidence
- **Scope control** — drifting off-plan or skipping task accounting

Frameworks that *own the whole process* (GSD, BMAD, Spec-Kit, issue-tracker agents) can help — but they also take away control and make process bugs hard to fix.

`$run` keeps **you** in charge: plain files, explicit phases, hard stops where it matters.

## Key features

- **Three-layer model** — project → workstream → tasks (`tasks.md` rows)
- **Session sticky** — bound repos must stay on `$run`; no silent ad-hoc coding
- **Single writer** — only parent `$run` updates workspace state; subagents may edit code (prefer worktrees)
- **Verification gate** — `doing → done` requires evidence in the execution log
- **Acceptance freeze** — confirm the pass bar before execute; later chat cannot soften it
- **Implementation review** — read-only reviewer audits code against Acceptance before human smoke
- **Separate review file** — Acceptance + rounds live in `review.md`; `context.md` keeps only status mirrors
- **Inherited project knowledge** — `project.md` `## Gotchas` / `## Key Decisions` carry across sibling workstreams
- **Integration gate** — all tasks `done` ≠ workstream closed; human smoke + worktree disposition required
- **Handoff block** — resume from `## Handoff` in `context.md`, not chat archaeology
- **`$run auto`** — unattended advance with dual-agent design gates and real hard stops

### Strong binding

- **One session ↔ one workstream ↔ one primary worktree** — never advance multiple lines in one session
- **New sessions must bind** — restore or choose a workstream before explore / plan / execute
- **Missing worktree hard-stop** — `worktree_status: missing` blocks mutation; never fall back to the main checkout
- **Status line always shows `wt=`** — primary worktree short path, `missing`, or `none` (no `dirty` / `branch` in the compact line)

## Quick start

### 1. Install

```bash
npx skills add kl7sn/run -g
```

Installs **`run`**. Common flags:

```bash
npx skills add kl7sn/run -g -y              # non-interactive
npx skills add kl7sn/run -g -a cursor       # Cursor only
npx skills add kl7sn/run --list             # preview packaged skills
npx skills update                           # refresh later
```

Contributors with a clone: `./install.sh all` (symlink into agent dirs).

### 2. Create a workstream

In your project repo:

```text
$run init demo          # project container (once)
$run new hello          # nested workstream under the project
```

Or point `RUN_WORKSPACE` / `.run-state` at an existing workspace folder.

### 3. Run

```text
$run                    # advance explore → plan → execute
$run auto               # unattended (hard stops still apply)
```

Status line on every advancing reply:

```text
[$run · lang=en · auto=off · 01-demo/01.01-hello · wt=none · T01 ready]
```

## Packaged skill

| Skill | Role |
| --- | --- |
| [`run`](skills/run/SKILL.md) | Process protocol — bind, phases, tasks, Handoff, gates |

`$run` is **not** a general skill toolkit. Other skills (TDD, grilling, domain tools) stay separate and optional.

The `run` skill uses progressive disclosure: the entrypoint `skills/run/SKILL.md` is intentionally compact (under 500 lines), while detailed workspace, recovery, execution, auto, and reference protocols live under `skills/run/protocols/` and are loaded only when relevant.

## Commands

| Command | Description |
| --- | --- |
| `$run init` [projectId] | Create project container |
| `$run new` [workstreamId] | Create nested workstream |
| `$run bind` | Rebind this session interactively |
| `$run lang` [en\|zh] | Show or set document language |
| `$run` | Advance current phase |
| `$run auto` | Unattended advance |

## Workspace

Resolution order: `.run-state` → `RUN_WORKSPACE` → explicit setup required. There is no implicit `~/run-workspace` fallback.

```text
<workspace>/
└── Projects/
    └── 01-demo/                    # project  NN-<slug>
        ├── project.md              # workstreams+worktrees · shared Gotchas · Key Decisions
        └── 01.01-hello/            # workstream  NN.MM-<slug>
            ├── workstream.md
            ├── tasks.md
            ├── context.md          # Handoff · Gotchas · Key Decisions · Execution Log
            ├── review.md           # Acceptance · ReviewIndex · Claims · ReviewThread
            └── spec.md             # optional input contract
```


Sample: [`examples/01-demo/`](examples/01-demo/) · Templates: [`templates/`](templates/) (`*.zh.md` for Chinese)

Repo session index (`.run-state` at git root):

```yaml
workspace: /absolute/path/to/workspace/Projects/01-demo/01.01-hello
lang: en
project: 01.01-hello
repo: .
```

## Supported agents

| Agent | Install target |
| --- | --- |
| Cursor | `~/.cursor/skills/` |
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |

Use `npx skills add kl7sn/run -g -a <agent>` to pick one. The `install.sh` helper also covers `~/.agents/skills/`.

## What $run is not

| | |
| --- | --- |
| ❌ Hosted agent platform | ✅ Markdown workspace + skill protocol |
| ❌ Issue tracker you must live in | ✅ `tasks.md` rows you can grep |
| ❌ General skill hub / registry | ✅ Process assistant only |
| ❌ "Looks good" completion | ✅ Verification + human smoke before close |

## Optional companions

`$run` orchestrates; phase discipline skills are optional:

- **Defaults:** superpowers (`brainstorming`, `writing-plans`, TDD, `verification-before-completion`)
- **Cherry-picks:** [mattpocock/skills](https://github.com/mattpocock/skills) — e.g. `grill-with-docs`, `to-tickets`, `code-review`
- **Do not** dual-run their `handoff` / `implement` or move durable state out of the workspace

See [`skills/run/SKILL.md`](skills/run/SKILL.md) → *Companion skills*.

## Documentation

| Document | Purpose |
| --- | --- |
| [`skills/run/SKILL.md`](skills/run/SKILL.md) | Entrypoint / short protocol; details in [`skills/run/protocols/`](skills/run/protocols/) |
| [`docs/design.md`](docs/design.md) | Design notes and tradeoffs |
| [`README_CN.md`](README_CN.md) | 中文说明 |

## License

[MIT](LICENSE)
