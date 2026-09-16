# $run recover and Handoff protocol

## Recover order

1. Read `.run-state`; resolve the workspace (fail closed if unresolved).
2. **Session bind gate:** match `CODEX_THREAD_ID`/session id in `.run-state projects[]`. If no matching `session_id` → emit the new-session bind prompt (`$run bind` or `$run new`) from [reference.md](reference.md) **Binding and code-management prompts** (new-session template); **stop** before recover advance. Never auto-bind the sole active line. Do not enter execute.
3. After a session match (or after the user completes bind/new), sync the top-level binding; resolve homepage type (`project` or `workstream`) and required parent; read `tasks.md`, then bounded `context.md`: Handoff, Acceptance, ReviewPointer, Gotchas, recent related log. Do not load `reviews.md` on every recover — open it only when the phase is review/triage, `$run review` runs, or the user asks about a finding or a task's review history.
4. Closed-line check: if the bound workstream is closed (`Handoff status: closed` or index `completed|archived`) and durable work is requested, do not reopen it. Use `$run new` under the parent or bind an active sibling, and link the closed line from the new context.
5. Run `git worktree list --porcelain` and compare every path/branch with Handoff and `.run-state`. Surface **orphan** and **missing** findings for explicit triage before any further advance or mutation.
6. Inspect `git status --porcelain=v1`, current branch/upstream, and latest commit. Record `worktree_git_status` and `commit_status`; dirty or uncommitted carry-over is a visible blocker, not a reason to continue silently.
7. **Strict workstream-fit.** A request may proceed without a binding decision only if it clearly targets the current `doing` or a specific `ready` task (including `Txx`), or explicitly says continue/finish the current task when exactly one sensible target exists. Everything else (mixed domains, independent deliverables, stale backlog, “顺便”, “再加一个”, or ambiguous follow-up) is non-continuation: set `binding_decision: pending`, emit the non-continuation prompt from [reference.md](reference.md), and stop for continue-current / `$run bind` / `$run new <name>` before adding a task.
8. Map the current request to a task row; create one only after the binding decision is resolved.
9. Run mutation preflight, then continue from the breakpoint. Before continuing, emit a recovery checkpoint with the bound project/workstream, phase, task statuses, worktree/git state, blocker, and exactly one next action. Do this proactively; a user status request is not required.

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
impl_review_status: none|pending|in_triage|re_review|approved|escalated
current_tasks: []
last_completed: <task-id or ->
blocker: none|<machine-readable short>
next_action: <one executable step>
resume_hint: <hint>
```

When a code worktree exists, also record `worktree_path`, `worktree_branch`, `worktree_status`, `smoke_status`, and `integration_next` using the exact enums in [reference.md](reference.md). Treat `## Acceptance` and `reviews.md` as authoritative for freeze and review triage; do not reconstruct them from chat, and refresh `## ReviewPointer` rather than inlining rounds when they drift. If the worktree is active or smoke is pending, surface that state in the next status checkpoint instead of silently treating the line as complete.

## Full-stop

For hard blocks or auto stops, update tasks and Handoff with a machine-readable blocker, `review_status: escalate` when applicable, a next action, and a resume hint. Reply with the status line and a short Handoff summary; stop without claiming completion.

## Proactive worktree decision

When all task rows are `done` and fresh verification exists, recover must route to the **implementation review gate** first on code workstreams ([execute.md](execute.md)). Only after `impl_review_status: approved` (or docs-only skip) does recover present the integration/smoke decision. Inspect the worktree and smoke fields and ask the user to choose one of these explicit outcomes:

- confirm the current worktree is complete, then provide smoke evidence and an integration disposition;
- continue in the current worktree with another task;
- create a new worktree/workstream before any further mutation.

Do not infer completion from `ready_to_merge`, a successful test run, or a prior status message. Do not present the smoke prompt while impl-review is `pending`, `in_triage`, `re_review`, or `escalated`. Do not silently create a fallback worktree. Never silently recreate a worktree or fall back to the main checkout.

## Orphan worktree triage

An **orphan** is a worktree path/branch returned by `git worktree list --porcelain` that is not represented by the current Handoff or any matching `.run-state projects[]` entry (git has, state lacks). Stop before mutation and list each orphan with path, branch, dirty state, and last commit. Ask the user to:

- adopt/register it to an existing workstream;
- keep it for later investigation (record `binding_decision: pending` and leave it untouched); or
- prune it only after explicit authorization and a separate safety check.

Never infer ownership from a folder name and never remove an orphan during recover.

## Missing worktree triage

A **missing** worktree is recorded in Handoff (`worktree_path` / `worktree_branch`) or the matching `.run-state` entry, but absent from `git worktree list --porcelain` (state has, git lacks). This is a hard stop.

On `missing`:

1. Set `worktree_status: missing`, `binding_decision: pending`, and `blocker: worktree-missing`.
2. Emit the missing-worktree prompt from [reference.md](reference.md) **Binding and code-management prompts**.
3. Ask the user to choose exactly one of:
   - recreate the worktree at the recorded path/branch (explicit only; never silent);
   - adopt an existing path that already holds the intended branch/commits;
   - close the current line, then `$run new` under the parent (or bind an active sibling).
4. Do not mutate code, add tasks, or advance into execute until the decision is resolved.
5. When useful, surface stranded-commit hints (branch tip, reflog, or last known commit on `worktree_branch`) so the user can decide recreate vs adopt vs close.

Never silently recreate a missing worktree and never fall back to the main checkout while `worktree_status` is `missing`.
