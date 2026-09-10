# $run recover and Handoff protocol

## Recover order

1. Read `.run-state`; identify session id and top-level binding.
2. Match `projects[]` by session id; sync the top-level entry.
3. Resolve homepage type (`project` or `workstream`) and required parent.
4. Read `tasks.md`, then bounded `context.md`: Handoff, Gotchas, recent related log.
5. Check closed-line, multiple-doing, worktree, and workspace contradictions.
6. Run `git worktree list --porcelain` and compare every path/branch with Handoff and `.run-state`; surface unregistered or missing entries for explicit triage before mutation.
7. Inspect `git status --porcelain=v1`, current branch/upstream, and latest commit. Record `worktree_git_status` and `commit_status`; dirty or uncommitted carry-over is a visible blocker, not a reason to continue silently.
8. Run a workstream-fit check. If the request is a different domain/deliverable, or the current line has mixed/stale backlog, set `binding_decision: pending` and ask continue-current, `$run bind`, or `$run new <name>` before adding a task.
9. Map the current request to a task row; create one only after the binding decision is resolved.
10. Run mutation preflight, then continue from the breakpoint.
11. Before continuing, emit a recovery checkpoint with the bound project/workstream, phase, task statuses, worktree/git state, blocker, and exactly one next action. Do this proactively; a user status request is not required.

If a bound workstream is closed (`Handoff status: closed` or index `completed|archived`) and durable work is requested, do not reopen it. Use `$run new` under the parent or bind an active sibling, and link the closed line from the new context.

## Handoff rules

`context.md` has one runtime section named `## Handoff`. Keep it bounded and refresh it at every breakpoint, task transition, full-stop, or session switch. Tasks are authoritative when Handoff conflicts with `tasks.md`.

Required fields:

```yaml
status: open|closed
updated: <timestamp>
workstream: <project>/<workstream>
parent_project: <project>
lang: en|zh
auto_mode: true|false
phase: explore|plan|execute
review_status: good|revise|blocked|escalate
current_tasks: []
last_completed: <task-id or ->
blocker: none|<machine-readable short>
next_action: <one executable step>
resume_hint: <hint>
```

When a code worktree exists, also record `worktree_path`, `worktree_branch`, `worktree_status`, `smoke_status`, and `integration_next` using the exact enums in [reference.md](reference.md). If the worktree is active or smoke is pending, surface that state in the next status checkpoint instead of silently treating the line as complete.

## Full-stop

For hard blocks or auto stops, update tasks and Handoff with a machine-readable blocker, `review_status: escalate` when applicable, a next action, and a resume hint. Reply with the status line and a short Handoff summary; stop without claiming completion.

## Proactive worktree decision

When all task rows are `done` and fresh verification exists, recover must route to the integration gate. Inspect the worktree and smoke fields and ask the user to choose one of these explicit outcomes:

- confirm the current worktree is complete, then provide smoke evidence and an integration disposition;
- continue in the current worktree with another task;
- create a new worktree/workstream before any further mutation.

Do not infer completion from `ready_to_merge`, a successful test run, or a prior status message. Do not silently create a fallback worktree.

## Orphan worktree triage

An orphan is a worktree path/branch returned by `git worktree list --porcelain` that is not represented by the current Handoff or any matching `.run-state projects[]` entry. Stop before mutation and list each orphan with path, branch, dirty state, and last commit. Ask the user to:

- adopt/register it to an existing workstream;
- keep it for later investigation (record `binding_decision: pending` and leave it untouched); or
- prune it only after explicit authorization and a separate safety check.

Never infer ownership from a folder name and never remove an orphan during recover.
