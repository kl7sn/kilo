# $run execution protocol

## Phase routing

- Missing or incomplete design → explore and write `spec.md`.
- Design exists and all task rows are todo → plan and create an acyclic task table with at least one ready row.
- Ready rows → execute.
- Blocked only → report blockers.
- All rows done → integration gate; do not auto-close.

## Pre-mutation gates

Before mutation-accounting preflight, adding a task row, or any external mutation:

1. **Primary worktree must be usable.** If `worktree_status` is `missing`, hard-stop with the missing-worktree prompt from [reference.md](reference.md); never fall back to the main checkout. If the task touches code/config and `worktree_status` is `none`, stop and create/register the primary worktree (`$run new` / bind path) before continuing. Code mutations require an `active` (or later integration) primary worktree path—not `missing` or docs-only `none`.
2. **Strict workstream-fit.** Non-continuation requests must not add a task row or mutate. Set `binding_decision: pending`, emit the non-continuation prompt from [reference.md](reference.md), and stop for continue-current / `$run bind` / `$run new <name>`.

### Continuation check

A request is a continuation only when:

- it clearly targets the current `doing` row or a specific `ready` task (including `Txx`); or
- it explicitly says continue/finish the current work and exactly one sensible target exists.

Everything else—mixed domains, independent deliverables, stale backlog, “顺便”, “再加一个”, or ambiguous follow-up—is non-continuation and requires an explicit binding decision before add-task or mutate. `$run auto` treats these gates as hard stops (no guessing).

## Mutation-accounting preflight

Before the first code/config edit, commit, upload, restart, or other external mutation:

1. The request maps to an existing task row (add it first if needed, only after the pre-mutation gates pass).
2. That row is `doing`.
3. Handoff `current_tasks` contains exactly the claimed task or legal parallel wave.
4. The edit is within the task’s bounds.

If any check fails, stop and repair accounting before mutating. A later `recovery backfill` is an audit marker, not permission to code first.

## Proactive progress checkpoints

Every advancing turn reports state without waiting for a user prompt. Emit a compact status line plus one checkpoint. The status line **must** include `wt=<short-path|missing|none>` for the primary worktree; omit `dirty`, `branch`, and `primary=` from the compact line.

```text
[$run · lang=<lang> · auto=<on|off> · <project>/<workstream> · wt=<short-path|missing|none> · <task state>]
绑定：<project>/<workstream> · 阶段：<explore|plan|execute> · wt：<short-path|missing|none> · 进度：<done/doing/ready> · 下一步：<one action>
```
Refresh the checkpoint after binding/recovery, each task claim, each verification result, each phase transition, and every stop. Keep it factual and concise; do not claim completion until the integration gate is satisfied.

## Language-specific preflight

For a task that writes, modifies, fixes, or refactors Go code:

1. Invoke `use-modern-go` before the first mutation.
2. Run its `list` command for every relevant Go file and read the complete output.
3. Resolve the Go version from `go.mod`, `go.work`, or the local toolchain; do not apply guidance unavailable to that version or incompatible with the change.
4. Call `explain` only for guideline IDs being evaluated.
5. If the CLI cannot be loaded, stop with an actionable blocker rather than silently falling back.

Include the guidance command and result in the task's evidence line.

## Serial and parallel work

Default to serial when tasks touch the same package, directory, or unclear boundary. Parallelize only independent ready rows. Parent claims all rows and writes workspace state; code-changing subagents use isolated worktrees and return paths, commands, results, and failures. Multiple `doing` rows require `parallel_wave: true` and a log entry.

## Task completion

For each row: implement, run fresh verification, review scope, append evidence, set `done`, refresh Handoff, and recompute dependents. Verification failure means `review_status: revise`; never mark done or claim success.

Evidence shape:

```markdown
- T01 done: <summary> | paths: <paths> | guidance: <use-modern-go command> → <result> | verify: <command> → <result>
```

## Integration gate

Automated tests satisfy task rows but cannot close a workstream. Closing requires:

1. Every task done with evidence.
2. User-confirmed smoke (`passed`) or explicit waiver (`waived-by-user`).
3. `integration_next` set to `merge`, `pr`, `keep-branch`, or `prune`.
4. Any worktree disposition executed or explicitly deferred with `keep-branch`.

Until then keep Handoff open with `smoke_status: pending` and, when applicable, `worktree_status: smoke_pending`.

After all tasks are done, proactively inspect the worktree rather than waiting for a status question. If completion, smoke, or disposition is not explicit, ask the user whether to:

1. finish the current worktree (then provide smoke evidence and choose `merge`, `pr`, `keep-branch`, or `prune`);
2. continue with another task in the current worktree; or
3. create a new worktree/workstream before further mutations.

This prompt is required in normal and auto mode. Auto mode may not guess the answer or close the line on the user's behalf.
