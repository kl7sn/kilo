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
3. **One window, one binding.** Never advance multiple workstreams in one session. Ambiguous candidates require an interactive bind.
4. **Parent is the workspace writer.** Subagents may edit isolated code, but only the parent updates `.run-state`, `tasks.md`, and `context.md`.
5. **Fail closed on workspace resolution.** Use `.run-state` `workspace:` first, then non-empty `RUN_WORKSPACE`; if neither resolves, stop before creating directories or durable state. Never silently use `~/run-workspace`.
6. **Mutation preflight is mandatory.** Before any external mutation, the intent must map to a `doing` task and `context.md` Handoff `current_tasks` must match it.
7. **Done requires fresh evidence.** Run verification before marking a task `done`; record the command and result in the execution log.
8. **All tasks done is not closed.** Human smoke and worktree disposition are required before closing a workstream.
9. **Progress is proactive.** During an advancing turn, report the current binding and the next execution step at each phase or task transition; do not wait for the user to ask for status.
10. **Worktree decisions are proactive.** When execution reaches the integration gate, determine whether the current worktree is complete. If human smoke or disposition is still pending, ask the user to confirm completion, continue in the current worktree, or request a new worktree before more mutations.
11. **Workstream fit is proactive.** Before adding a task, check whether the request belongs to the bound workstream. Mixed domains, independent deliverables, stale backlog, or repeated follow-up work require an explicit choice to continue, bind an active sibling, or create `$run new <name>`; never silently pile unrelated work into one line.
12. **Dirty code is visible.** Before integration or close, inspect git status, branch/upstream, and the latest commit. Uncommitted code is a blocking state for close and must be surfaced with an explicit commit, keep-branch, or continue decision.
13. **Worktrees are audited.** On recover, bind, new, and integration, compare `git worktree list --porcelain` with Handoff and `.run-state`. Unregistered worktrees require explicit adopt/register, keep for later, or prune authorization; never silently ignore or delete them.

## Commands

| Command | Purpose |
|---|---|
| `$run` | Recover and advance the current workstream |
| `$run auto` | Unattended advance with design-gate review |
| `$run init <project>` | Create a numbered project container |
| `$run new <workstream>` | Create a numbered workstream under a project |
| `$run bind` | Interactively switch to an active workstream/project |
| `$run lang [en\|zh]` | Show or set durable document language |
| `$run review [scope]` | Scan bounded workspace artifacts and maintain skills |

Details: [workspace.md](protocols/workspace.md), [recover.md](protocols/recover.md), [execute.md](protocols/execute.md), [auto.md](protocols/auto.md), [review.md](protocols/review.md), [reference.md](protocols/reference.md).

## Startup route

1. Read repo `.run-state` and resolve the workspace; unresolved means hard stop.
2. Handle an explicit subcommand before normal phase detection.
3. Resolve `lang`: open Handoff → `.run-state` → `RUN_LANG` → `en`.
4. Match `CODEX_THREAD_ID`/session id in `.run-state projects[]`; otherwise bind interactively when there is more than one candidate.
5. Read the bound homepage, `tasks.md`, and bounded `context.md` Handoff/Gotchas/log.
6. If the line is closed and this turn needs durable landing, stop recover and create/bind an active line.
7. Run a workstream-fit check before mapping the request. If the request is a distinct deliverable/domain, or the line has a stale/mixed backlog, stop for an explicit continue/current, `$run bind`, or `$run new <name>` decision.
8. Map the current request to an existing task or add a task row before mutation.
9. Route: missing design → explore; all tasks todo → plan; ready tasks → execute; blocked only → report; all done → integration gate.
10. Audit git worktrees and dirty/commit state before advancing. Unregistered worktrees or uncommitted carry-over require explicit triage before further mutation.
11. Emit a status checkpoint containing the resolved binding, phase, task statuses, worktree/git state, and next action before advancing. Emit another checkpoint after each task claim, verification result, phase transition, audit finding, or hard stop.

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
- Session index: repo-root `.run-state`; one repo may list many workstreams, but one session advances one.

Number new entities. `NN` is the project number; workstream `MM` increments under that project. Do not rename unnumbered legacy folders unless requested.

## Handoff minimum

Keep one bounded `## Handoff` section with `status`, `updated`, `workstream`, `parent_project`, `lang`, `auto_mode`, `phase`, `review_status`, `current_tasks`, `last_completed`, `blocker`, `next_action`, `resume_hint`, `key_paths`, and integration fields (`worktree_path`, `worktree_branch`, `worktree_status`, `smoke_status`, `integration_next`).

`status: closed` requires all tasks done, fresh evidence, explicit human smoke (`passed` or `waived-by-user`), and a recorded integration disposition. See [reference.md](protocols/reference.md).

## Execute contract

Before editing:

```text
intent → task row exists → task is doing → Handoff.current_tasks matches → mutate
```

For each task: implement within bounds, verify freshly, append one evidence line, set `done`, refresh Handoff, and recompute dependents. If verification fails, use `review_status: revise`; never claim done.

For tasks that write, modify, fix, or refactor Go code, also use `use-modern-go` before the first mutation. Resolve the repository Go version from `go.mod`, `go.work`, or the local toolchain; run its `list` command for each relevant Go file and read the complete output. Use `explain` only for guideline IDs under consideration. Apply guidance only when it compiles with the declared version and preserves behavior. If the guideline CLI cannot be loaded, stop with an actionable blocker; do not silently fall back. Record the guidance command and result in the task evidence.

Parallel work is legal only for independent tasks in an explicitly recorded wave. Use isolated worktrees for code-changing subagents; otherwise run serially. See [execute.md](protocols/execute.md).

## Auto contract

`$run auto` sets `auto_mode: true` and keeps ready tasks flowing. It must not wait for a human at a design gate: dispatch a read-only reviewer, record `verdict: approve|revise|escalate`, then continue or full-stop. True product forks, irreversible operations, bind ambiguity, illegal multi-`doing`, unresolved workspace, and impossible verification remain hard stops. See [auto.md](protocols/auto.md).

## Status line

Every advancing reply starts with a compact line such as:

```text
[$run · lang=zh · auto=off · 05-run/05.02-workspace-routing · T04 doing]
```

Use `design-review: pending|approved|revise|escalate` while an auto design gate is active; use `smoke_pending` until human smoke passes.

During execution, do not provide a bare status line only. Follow it with a concise checkpoint:

```text
绑定：<project>/<workstream> · 阶段：execute · worktree：<status/path>
进度：T04 done，T05 doing，T06 ready · 下一步：运行 <verification command>
```

At the integration gate, proactively present one decision prompt when the current worktree is not explicitly complete:

```text
当前任务已完成，自动验证已通过；worktree 仍为 <status>。
请确认下一步：
1. 当前 worktree 已完成：进行人工 smoke，并选择 merge / pr / keep-branch / prune
2. 继续当前 worktree：提出下一项任务
3. 新建 worktree：指定新 workstream 或确认 `$run new <name>`
```

Do not close the workstream, create a new worktree, or start new mutations until the decision is explicit. In `$run auto`, this is still a hard integration stop; auto mode must not guess the worktree disposition.

## Review and maintenance

`$run review` scans only bounded workspace artifacts, writes a report under the current project, then applies the report backlog through `up` unless `scan-only` is requested. It does not reopen workstreams or alter code repos. See [review.md](protocols/review.md).

## Companion skills

Use phase companions only when needed: brainstorming for explore, writing-plans for plan, TDD/systematic-debugging for execute, `use-modern-go` for Go code changes, verification-before-completion before every done, and using-git-worktrees for isolation. Companions return results; the parent remains the sole workspace writer.

## Progressive disclosure map

- Workspace setup, init/new/bind, numbering, language: [protocols/workspace.md](protocols/workspace.md)
- Recover, Handoff, and session sticky: [protocols/recover.md](protocols/recover.md)
- Explore/plan/execute, waves, verification, integration gate: [protocols/execute.md](protocols/execute.md)
- Auto mode and dual-agent design gates: [protocols/auto.md](protocols/auto.md)
- Review scan, report, and `up`: [protocols/review.md](protocols/review.md)
- File templates, hard blocks, self-review, and cross-references: [protocols/reference.md](protocols/reference.md)
