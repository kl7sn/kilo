# /run design notes

Public summary of the workflow. Full rules live in `skills/run/SKILL.md`.

## Identity

`/run` is an **engineering process assistant** (bind → advance → verify → hand off). It is **not** a general skill toolkit or hub for arbitrary local skills.

## Model

1. **Project** — `Projects/<NN-slug>/project.md`
2. **Workstream** — nested `Projects/<NN-slug>/<NN.MM-slug>/` with `workstream.md` + `tasks.md` + `context.md`
3. **Tasks** — rows in `tasks.md` (`todo` / `ready` / `doing` / `blocked` / `done`)

## Durable state

- **Workspace folder**: Markdown only. Obsidian optional.
- **`.run-state`**: per code-repo session index (`workspace`, `lang`, `project`, `projects[]`, `session_id`).
- Prefer `~/…` or absolute paths; keep spaced paths (e.g. iCloud) consistent across all bind entries. After moving a vault, rewrite every bound repo’s state file.

## Document language

- `lang: en | zh` — resolve Handoff → `.run-state` → `RUN_LANG` → default `en`.
- `/run lang` shows or sets the value. Controls durable prose + human-facing replies; enums/keys stay English.
- Templates: `templates/*.md` (en) and `templates/*.zh.md` (zh).

## Quality

- Done requires verification evidence in `context.md` execution log.
- **Automated gates** satisfy task `done`; **human smoke** on the worktree satisfies workstream close.
- Illegal multiple `doing` (no parallel wave) is a hard block.
- Independent ready tasks may run in parallel via subagents; **only the parent writes workspace files**. Prefer worktree isolation for code edits.

## Integration gate

- Do not set `Handoff status: closed` while `smoke_status: pending` or an active unmerged worktree exists without disposition.
- Handoff tracks `worktree_path`, `worktree_branch`, `worktree_status`, `smoke_status`, `integration_next`.
- `/run new` should surface orphan worktrees from sibling lines before adding another.

## Auto mode

- `/run auto` keeps advancing ready work.
- Design gates (explore→plan, scheme choice, **mid-execute design docs**) use dual-agent consensus with a **mechanical preflight**: recorded verdict, `design-review:` status line, no idle “please confirm / continue”.
- Asking for human design confirmation under `auto=on` is a protocol error → correct in-turn via dual-agent review.
- True product forks (goal/non-goal change, capability removal, irreversible release/compliance) still full-stop; routine scoped design does not.

## Handoff

`context.md` uses **`## Handoff` as the only runtime section** (no separate “Current status”). Optional `## Gotchas` for long-lived constraints; `## Key Decisions` for decision history; `## Execution Log` for evidence.

## Acceptance and review file

The frozen pass bar and the rounds that audit it share one file, **`review.md`** (`## Acceptance`, `## ReviewIndex`, `## Claims`, `## ReviewThread`): the reviewer gets a single attachment, and `context.md` stays cheap to reload. Handoff carries only `acceptance_status` / `impl_review_status` mirrors, so gates fire without opening the file; `review.md` is loaded at freeze/revise, during review/triage, or when answering a finding/task history question.

Acceptance is per workstream and versioned. Appending in-scope work (finding fixes, tests) keeps the same `version` but resets an `approved` review to `re_review`; work that widens the deliverable needs an explicit revise (`version+1`) or a new line.

## Inherited project knowledge

Project level stores **facts and pointers, never copies**, because "every new line must read the project gotcha list" just relocates context bloat instead of removing it.

- `project.md` `## Stable Facts` — long-lived verifiable facts (build/run commands, directory conventions, external-system contracts). Read on every explore.
- `project.md` `## Gotcha Index` — one pointer line per topic (`- <topic>: <conclusion> → [[01.03-slug/context]]`). Followed only when the topic touches the current line.
- `context.md` `## Gotchas` — full text, stays with the line that learned it.
- `context.md` `## Key Decisions` — line-local, **not** inherited; queried on demand.

Promotion order: mechanize first (test / lint / type / CI beats prose, because a document entry depends on an agent remembering to read it), else one `Stable Facts` line, else one `Gotcha Index` pointer, else keep it local. Uncertainty defaults to *not* promoting. Both project sections are pruned on expiry — a stale entry is worse than a missing one, since agents obey it.

**Fact drift.** A landed fact is current truth, not settled history; later requirements will contradict it. When a line invalidates an entry it must record the conflict as accountable work, ask the user first if a sibling line is `active`/`smoke_pending` on the old truth, update the entry in place at close, and put the reason in its own `## Key Decisions`. If the invalidated fact was referenced by the frozen Acceptance, the bar is revised (`version+1`) rather than reinterpreted. A line cannot close leaving a known contradiction in `project.md`.

`project.md` also tracks each workstream's worktree path, branch, and state.

`status: closed` ends the workstream. New durable work must **not** reopen it — `/run new` under the parent (or bind another active line). Binding a closed line while needing tasks/decisions/code is an abnormal bind / hard block.

## Comparison

Full table: [README § Comparison](../README.md#comparison). Summary:

- **ai-memory** — cross-session capture & handoff injection; `/run` — explicit tasks, verification, workstream close rules. Often used together.
- **mattpocock/skills** — composable phase toolbox; `/run` owns workspace orchestration. Cherry-pick only; no dual `handoff`/`implement`.
- **GSD / BMAD / Spec-Kit** — own the pipeline; `/run` stays a small Markdown + skill protocol with visible hard stops.

## Companion skills

`/run` orchestrates; it does not replace phase disciplines. Default to local superpowers (`brainstorming`, `writing-plans`, `tdd`, `systematic-debugging`, `verification-before-completion`). Optionally cherry-pick from [mattpocock/skills](https://github.com/mattpocock/skills) (`grill-with-docs`, `to-tickets`, `code-review`) — never dual-run their `handoff`/`implement` or a full pack that moves durable state out of the workspace.

