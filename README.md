<p align="center">
  <img src="docs/images/run-mark.svg" width="72" height="72" alt="run" />
</p>

<h1 align="center">run</h1>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License: MIT" /></a>
  <a href="https://skills.sh/kl7sn/run"><img src="https://img.shields.io/badge/install-npx%20skills-6366f1?style=flat-square" alt="Install" /></a>
  <a href="#supported-agents"><img src="https://img.shields.io/badge/agents-Cursor%20%7C%20Claude%20%7C%20Codex-555?style=flat-square" alt="Agents" /></a>
  <a href="#workspace"><img src="https://img.shields.io/badge/state-Markdown%20workspace-lightgrey?style=flat-square" alt="State" /></a>
</p>

<p align="center">
  <a href="README_CN.md">中文</a>
</p>

<p align="center"><strong>Durable execution for coding agents.</strong></p>

<p align="center">
  Bind a workstream, keep state docs in Markdown, no <code>done</code> without evidence,<br />
  and continue from Handoff — not from old chat history.
</p>

<p align="center">
  <a href="https://skills.sh/kl7sn/run"><strong>Install run</strong></a>
  · follows
  <a href="https://agentskills.io/">Agent Skills</a>
  via
  <a href="https://skills.sh">skills.sh</a>
</p>

## What it is

`/run` is a process skill for Cursor, Claude Code, and Codex.

Multi-step work you can pause and resume:

```text
bind workstream → explore / plan / execute → verify → hand off → continue
```

![/run main flow](docs/images/run-readme-main-flow.svg)

State docs live in an **Obsidian Markdown vault**. The code repo only keeps a small `.run-state` pointer. No control plane. No SaaS.

## Why it exists

Agents write code well. They struggle with:

- **Continuity** — lose the thread across chats, tools, weekends
- **Evidence** — mark `done` with nothing to show
- **Scope** — drift off-plan or skip task rows

Full-process frameworks (GSD, BMAD, Spec-Kit, …) can help, but they often take over the process — and then process bugs are hard to fix.

`/run` keeps state in files, keeps phases explicit, and stops when it should instead of pushing ahead.

## What it does

- **Three layers** — project → workstream → tasks (`tasks.md` rows)
- **Sticky session** — once a repo is bound, stay on `/run`; no silent ad-hoc edits
- **Single writer** — only parent `/run` updates workspace; subagents may edit code (prefer worktrees)
- **Verification gate** — `doing → done` needs evidence in the execution log
- **Acceptance freeze** — lock the pass criteria before execute; later chat can't soften it
- **Implementation review** — a read-only reviewer checks code against Acceptance before human smoke
- **Separate review file** — Acceptance + rounds live in `review.md`; `context.md` only mirrors status
- **Project knowledge** — `project.md` keeps durable facts plus a gotcha *index*; details stay where you learned them
- **Integration gate** — all tasks `done` ≠ workstream closed; you still need human smoke + worktree disposition
- **Handoff** — resume from `## Handoff` in `context.md`, not from old chats
- **`/run auto`** — unattended advance; design reviews need dual-agent consensus; hard-stop conditions still stop

### Hard binding rules

- **One session ↔ one workstream ↔ one primary worktree** — don't advance multiple workstreams in one session
- **New sessions must bind first** — restore or pick a workstream before explore / plan / execute
- **Missing worktree = hard stop** — `worktree_status: missing` blocks code changes; don't fall back to the main checkout

## Quick start

### 1. Install

```bash
npx skills add kl7sn/run -g
```

That installs **`run`**. Common flags:

```bash
npx skills add kl7sn/run -g -y              # non-interactive
npx skills add kl7sn/run -g -a cursor       # Cursor only
npx skills add kl7sn/run --list             # see what's in the package
npx skills update                           # refresh later
```

### 2. Point at an Obsidian vault, then create a workstream

State docs go under the vault (`RUN_WORKSPACE` or `.run-state` `workspace:`). From a bound code repo:

```text
/run init demo          # project container in the vault (once)
/run new hello          # nested workstream under the project
```

`.run-state` lives at the **code repo** git root; `project.md` / `tasks.md` / … land in the vault.

### 3. Run

```text
/run                    # advance explore → plan → execute
/run auto               # unattended (hard stops still apply)
```

Every advancing reply starts with a status line:

```text
[/run · lang=en · auto=off · 01-demo/01.01-hello · wt=none · T01 ready]
```

## What's in the package

| Skill | Role |
| --- | --- |
| [`run`](skills/run/SKILL.md) | Process protocol — bind, phases, tasks, Handoff, gates |

`/run` is **not** a general skill toolkit. TDD, grilling, domain tools stay separate and optional.

The entrypoint `skills/run/SKILL.md` stays short (under 500 lines). Workspace, recovery, execution, auto, and reference details live under `skills/run/protocols/` and load only when needed.

## Commands

| Command | Description |
| --- | --- |
| `/run init` [projectId] | Create project container in the Obsidian vault |
| `/run new` [workstreamId] | Create nested workstream |
| `/run bind` | Rebind this session interactively |
| `/run accept` … | Draft or revise frozen Acceptance |
| `/run review` | Dispatch read-only implementation review |
| `/run lang` [en\|zh] | Show or set document language |
| `/run` | Advance current phase |
| `/run auto` | Unattended advance |

## Workspace

State lands in two places — don't mix them:

- **Code repo (git root):** only `.run-state` — which workstream / worktree this session is bound to.
- **Obsidian vault:** all state docs (`project.md` / `tasks.md` / `context.md` / `review.md`, …). `.run-state` `workspace:` points here.

![Two landing places: code repo vs Obsidian vault](docs/images/run-readme-two-places.png)

Resolution order: `.run-state` → `RUN_WORKSPACE` → you must set it up. No silent fallback to `~/run-workspace`.

```text
<code-repo>/.run-state              # session index only, at git root

<obsidian-vault>/                   # Obsidian vault = RUN_WORKSPACE
└── Projects/
    └── 01-demo/                    # project  NN-<slug>
        ├── project.md              # workstreams+worktrees · Stable Facts · Gotcha Index
        └── 01.01-hello/            # workstream  NN.MM-<slug>
            ├── workstream.md
            ├── tasks.md
            ├── context.md          # Handoff · Gotchas · Key Decisions · Execution Log
            ├── review.md           # Acceptance · ReviewIndex · Claims · ReviewThread
            └── spec.md             # optional input contract
```

Sample: [`examples/01-demo/`](examples/01-demo/) · Templates: [`templates/`](templates/) (`*.zh.md` for Chinese)

`.run-state` looks roughly like:

```yaml
workspace: /absolute/path/to/obsidian-vault/Projects/01-demo/01.01-hello
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

One agent only: `npx skills add kl7sn/run -g -a <agent>`.

## What /run is not

| | |
| --- | --- |
| ❌ Hosted agent platform | ✅ Markdown workspace + skill protocol |
| ❌ Issue tracker you must live in | ✅ `tasks.md` rows you can grep |
| ❌ General skill hub / registry | ✅ Process assistant only |
| ❌ "Looks good" completion | ✅ Verification + human smoke before close |

## Optional companions

`/run` orchestrates; phase-discipline skills are optional:

- **Defaults:** superpowers (`brainstorming`, `writing-plans`, TDD, `verification-before-completion`)
- **Cherry-picks:** [mattpocock/skills](https://github.com/mattpocock/skills) — e.g. `grill-with-docs`, `to-tickets`, `code-review`
- **Don't** dual-run their `handoff` / `implement`, or move durable state out of the workspace

See [`skills/run/SKILL.md`](skills/run/SKILL.md) → *Companion skills*.

## Documentation

| Document | Purpose |
| --- | --- |
| [`skills/run/SKILL.md`](skills/run/SKILL.md) | Entrypoint; details in [`skills/run/protocols/`](skills/run/protocols/) |
| [`docs/design.md`](docs/design.md) | Design notes and tradeoffs |
| [`README_CN.md`](README_CN.md) | 中文说明 |

## License

[MIT](LICENSE)
