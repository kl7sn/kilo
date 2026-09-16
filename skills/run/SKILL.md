---
name: run
description: "Use when a coding task needs a durable project/workstream binding, explicit phase routing, task accounting, recovery, verification gates, or unattended execution through the $run protocol."
---

# $run — durable engineering workflow

`$run` is the process entry for multi-step engineering work. It binds one repository session to one active workstream, routes the task through explore/plan/execute/recover, and records durable state in Markdown.

## Codex-facing syntax

Always show `$run` and `$run <subcommand>` in prompts, status lines, examples, templates, and replies. Do not expose the legacy slash spelling as a user command.

## Critical rules

1. **No ad-hoc engineering on a bound repo.** Recover the binding, map the request to a task row, claim it, then edit code/config.
2. **Closed lines stay closed.** If the binding points to a completed/archived workstream, create `$run new <name>` under its parent or bind an active sibling; never reopen it.
3. **One session ↔ one workstream ↔ one primary worktree.** Never advance multiple workstreams in one session. Ambiguous candidates require an interactive bind. Subagent isolation worktrees are allowed; they are not the primary binding.
4. **New session requires explicit bind.** No matching `session_id` → hard stop; require `$run bind` or `$run new`; never auto-bind the sole active line. Do this before recover advance.
5. **Parent is the workspace writer.** Subagents may edit isolated code, but only the parent updates `.run-state`, `tasks.md`, `context.md`, and `reviews.md`.
6. **Fail closed on workspace resolution.** Use `.run-state` `workspace:` first, then non-empty `RUN_WORKSPACE`; if neither resolves, stop before creating directories or durable state. Never silently use `~/run-workspace`.
7. **Mutation preflight is mandatory.** Before any external mutation, the intent must map to a `doing` task and `context.md` Handoff `current_tasks` must match it.
8. **Done requires fresh evidence.** Run verification before marking a task `done`; record the command and result in the execution log.
9. **All tasks done is not closed.** Code lines need implementation review (`reviews.md`) then human smoke and worktree disposition before close.
10. **Acceptance is frozen, not mined.** Freeze `## Acceptance` before execute on code lines; do not scrape long chat for the pass bar. Explicit `$run accept` / 「验收改成…」only to revise.
11. **ReviewThread is the cross-agent bus, in its own file.** Reviewer and implementer rounds append to the workstream `reviews.md`; `context.md` keeps only a bounded `## ReviewPointer`. Never inline rounds into `context.md`, and never ask the user to paste long review/fix text between agents.
12. **Progress is proactive.** During an advancing turn, report the current binding and the next execution step at each phase or task transition; do not wait for the user to ask for status.
13. **Worktree decisions are proactive.** When execution reaches the integration gate, determine whether the current worktree is complete. If human smoke or disposition is still pending, ask the user to confirm completion, continue in the current worktree, or request a new worktree before more mutations.
14. **Strict workstream fit.** Non-continuation requests set `binding_decision: pending` before adding tasks. Mixed domains, independent deliverables, stale backlog, or repeated follow-up work require an explicit choice to continue-current, `$run bind`, or `$run new <name>`; never silently pile unrelated work into one line.
15. **Dirty code is visible.** Before integration or close, inspect git status, branch/upstream, and the latest commit. Uncommitted code is a blocking state for close and must be surfaced with an explicit commit, keep-branch, or continue decision.
16. **Bidirectional worktree audit.** On recover, bind, new, and integration, compare `git worktree list --porcelain` with Handoff and `.run-state`. Orphans (git has, state lacks) need adopt/register, keep for later, or prune authorization. **`missing` (state has, git lacks) is a hard stop**: recreate / adopt an existing path / close then `$run new`. Never silently ignore, delete, or recreate.
17. **Code mutations only in the primary worktree.** Never fall back to the main checkout when `worktree_status` is `missing`.

## Commands

| Command | Purpose |
|---|---|
| `$run` | Recover and advance the current workstream |
| `$run auto` | Unattended advance with design-gate and impl-review gates |
| `$run review` | Dispatch read-only impl review (Acceptance + `reviews.md` + git) |
| `$run accept …` | Draft or revise `## Acceptance` (re-freeze before execute/review) |
| `$run init <project>` | Create a numbered project container |
| `$run new <workstream>` | Create a numbered workstream under a project |
| `$run bind` | Interactively switch to an active workstream/project |
| `$run lang [en\|zh]` | Show or set durable document language |

Details: [workspace.md](protocols/workspace.md), [recover.md](protocols/recover.md), [execute.md](protocols/execute.md), [auto.md](protocols/auto.md), [reference.md](protocols/reference.md).

## Startup route

1. Read repo `.run-state` and resolve the workspace; unresolved means hard stop.
2. Handle an explicit subcommand before normal phase detection.
3. Resolve `lang`: open Handoff → `.run-state` → `RUN_LANG` → `en`.
4. Match `CODEX_THREAD_ID`/session id in `.run-state projects[]`. **If no `session_id` match → emit the new-session bind prompt (`$run bind` or `$run new`) and stop** before recover advance; never auto-bind the sole active line.
5. After bind, run bidirectional worktree audit (orphan + missing) before fit check or task mapping. `missing` is a hard stop (recreate / adopt / close then `$run new`).
6. Read the bound homepage, `tasks.md`, and bounded `context.md` Handoff / Acceptance / ReviewPointer / Gotchas / log. Open `reviews.md` only for review, triage, or a review-history question.
7. If the line is closed and this turn needs durable landing, stop recover and create/bind an active line.
8. Strict workstream-fit before mapping or adding tasks: non-continuation → set `binding_decision: pending` and stop for continue-current / `$run bind` / `$run new <name>`.
9. Map the current request to an existing task or add a task row only after the binding decision is resolved.
10. Route: missing design → explore; all tasks todo → plan; plan→execute needs Acceptance freeze; ready tasks → execute; blocked only → report; all done → impl-review gate then integration gate; `$run review` → impl-review on demand.
11. Inspect dirty/commit state before advancing. Uncommitted carry-over requires explicit triage before further mutation.
12. Emit a status checkpoint containing the resolved binding, phase, task statuses, worktree/git state, Acceptance/impl-review state, and next action before advancing. Emit another checkpoint after each task claim, verification result, phase transition, audit finding, or hard stop.

## Workspace resolution

Resolution order is exactly:

```text
.run-state workspace: → RUN_WORKSPACE → explicit setup required
```

The workspace variable points to the workspace root. Project and workstream files live below `Projects/<projectId>/<workstreamId>/`. A successful `$run init`, `$run new`, or `$run bind` persists the absolute bound path in `.run-state`.

If unresolved, stop with an actionable instruction such as:

```zsh
export RUN_WORKSPACE='/absolute/path/to/workspace'
```

Do not guess, create, select, or write a fallback directory.

## Binding and state model

- Project: `Projects/NN-slug/project.md`, `type: project`.
- Workstream: `Projects/NN-slug/NN.MM-slug/workstream.md`, `type: workstream`, with full `parent`.
- Tasks: rows in the workstream `tasks.md` (`todo`, `ready`, `doing`, `blocked`, `done`).
- Runtime truth: the workstream `context.md` `## Handoff` block.
- Acceptance truth: `context.md` `## Acceptance` (frozen pass bar).
- Review truth: the workstream `reviews.md` (`## ReviewIndex`, `## Claims`, `## ReviewThread`), pointed at by `context.md` `## ReviewPointer`.
- Session index: repo-root `.run-state`; one repo may list many workstreams, but one session advances one.

Number new entities. `NN` is the project number; workstream `MM` increments under that project. Do not rename unnumbered legacy folders unless requested.

## Handoff minimum

Keep one bounded `## Handoff` section with `status`, `updated`, `workstream`, `parent_project`, `lang`, `auto_mode`, `phase`, `review_status`, `impl_review_status`, `current_tasks`, `last_completed`, `blocker`, `next_action`, `resume_hint`, `key_paths`, and integration fields (`worktree_path`, `worktree_branch`, `worktree_status`, `smoke_status`, `integration_next`).

Also keep `## Acceptance` and, once review starts, a bounded `## ReviewPointer` into `reviews.md` per [execute.md](protocols/execute.md) / [reference.md](protocols/reference.md).

`status: closed` requires all tasks done, fresh evidence, impl-review approved on code lines, explicit human smoke (`passed` or `waived-by-user`), and a recorded integration disposition. See [reference.md](protocols/reference.md).

## Execute contract

Before editing:

```text
intent → task row exists → task is doing → Handoff.current_tasks matches → mutate
```

Code workstreams also require `## Acceptance` `status: frozen` before the first execute mutation.

For each task: implement within bounds, verify freshly, append one evidence line, set `done`, refresh Handoff, and recompute dependents. If verification fails, use `review_status: revise`; never claim done.

For tasks that write, modify, fix, or refactor Go code, also use `use-modern-go` before the first mutation. Resolve the repository Go version from `go.mod`, `go.work`, or the local toolchain; run its `list` command for each relevant Go file and read the complete output. Use `explain` only for guideline IDs under consideration. Apply guidance only when it compiles with the declared version and preserves behavior. If the guideline CLI cannot be loaded, stop with an actionable blocker; do not silently fall back. Record the guidance command and result in the task evidence.

Parallel work is legal only for independent tasks in an explicitly recorded wave. Use isolated worktrees for code-changing subagents; otherwise run serially. See [execute.md](protocols/execute.md).

## Auto contract

`$run auto` sets `auto_mode: true` and keeps ready tasks flowing. Design gates and implementation-review gates both dispatch read-only reviewers (`verdict: approve|revise|escalate`); `reviews.md` is the durable transport. True product forks, irreversible operations, bind ambiguity, illegal multi-`doing`, unresolved workspace, undecided deferred/disagree asks, and impossible verification remain hard stops. See [auto.md](protocols/auto.md).

## Status line

Every advancing reply starts with a compact line that **must** include the primary worktree slot `wt=`:

```text
[$run · lang=zh · auto=off · 05-run/05.02-workspace-routing · wt=<short-path|missing|none> · T04 doing]
```

`wt` is the primary worktree identity for this binding: a short path/basename when registered and present, `missing` when Handoff records a worktree that git lacks, or `none` for docs-only lines. Do **not** put `dirty`, `branch`, or `primary=` in the compact status line — branch lives in Handoff; dirty git state belongs in the dirty-tree prompt or checkpoint notes only when it blocks work.

Use `design-review: pending|approved|revise|escalate` while an auto design gate is active; use `impl-review: pending|in_triage|re_review|approved|escalated` during implementation review; use `smoke_pending` until human smoke passes.

During execution, do not provide a bare status line only. Follow it with a concise checkpoint:

```text
绑定：<project>/<workstream> · 阶段：execute · wt：<short-path|missing|none>
进度：T04 done，T05 doing，T06 ready · 下一步：运行 <verification command>
```

For session bind, non-continuation fit, and missing-worktree stops, use the three standard prompts in [reference.md](protocols/reference.md) **Binding and code-management prompts** (new-session, non-continuation, missing). Do not invent alternate wording.

At the integration gate (only after impl-review is approved on code lines), proactively present one decision prompt when the current worktree is not explicitly complete:

```text
当前任务已完成，自动验证与实现审核已通过；worktree 仍为 <status>。
请确认下一步：
1. 当前 worktree 已完成：进行人工 smoke，并选择 merge / pr / keep-branch / prune
2. 继续当前 worktree：提出下一项任务
3. 新建 worktree：指定新 workstream 或确认 `$run new <name>`
```

Do not close the workstream, create a new worktree, or start new mutations until the decision is explicit. In `$run auto`, this is still a hard integration stop; auto mode must not guess the worktree disposition.

## Companion skills

Use phase companions only when needed: brainstorming for explore, writing-plans for plan, TDD/systematic-debugging for execute, `use-modern-go` for Go code changes, verification-before-completion before every done, and using-git-worktrees for isolation. Companions return results; the parent remains the sole workspace writer.

## Progressive disclosure map

- Workspace setup, init/new/bind, numbering, language: [protocols/workspace.md](protocols/workspace.md)
- Recover, Handoff, and session sticky: [protocols/recover.md](protocols/recover.md)
- Explore/plan/execute, Acceptance freeze, `reviews.md` separation, impl-review, integration gate: [protocols/execute.md](protocols/execute.md)
- Auto mode, design gates, and impl-review gates: [protocols/auto.md](protocols/auto.md)
- Templates, enums, hard blocks, self-review: [protocols/reference.md](protocols/reference.md)
