# $run reference

## Task table

```markdown
| ID | Task | Status | Depends | Blocker | Acceptance |
|---|---|---|---|---|---|
| T01 | ... | ready | - | - | ... |
```

Statuses are `todo`, `ready`, `doing`, `blocked`, `done`.

## Worktree enums

```text
worktree_status: none | active | smoke_pending | ready_to_merge | pruned
smoke_status: pending | passed | waived-by-user
integration_next: none | merge | pr | keep-branch | prune
worktree_git_status: clean | dirty | unknown | not-applicable
commit_status: committed | uncommitted | unknown | not-applicable
binding_decision: pending | continue-current | bind-existing | new-workstream
```

Never encode compound or free-form values in these fields. Automated smoke belongs in `notes` or the execution log.

`worktree_git_status`, `commit_status`, and `binding_decision` are durable decision fields, not prose. `commit_status: uncommitted` blocks close. `binding_decision: pending` blocks adding a task when the fit check found scope drift.

## Progress and integration prompt

Every advancing reply starts with a `$run` status line and includes the resolved binding, phase, current task statuses, worktree status/path, and one next action. Emit it after recovery, task transitions, verification, phase changes, and stops; never wait for a user status request.

When all task rows are done, tests are fresh, and the worktree is not explicitly disposed, use this prompt:

```text
当前任务已完成，自动验证已通过；worktree 仍为 <status>。
请确认：
1. 当前 worktree 已完成，并提供人工 smoke + integration disposition；
2. 继续当前 worktree；或
3. 新建 worktree/workstream 后再继续。
```

The prompt is a hard integration gate. `ready_to_merge` means technically ready, not human-confirmed complete. Never infer a new worktree request or close disposition from silence.

## Binding and code-management prompts

When a request does not clearly fit the bound workstream, use this prompt before creating a task or mutating code:

```text
当前绑定：<project>/<workstream>
发现：<mixed scope / stale backlog / independent deliverable>
请确认：
1. 继续当前 workstream：<why it still belongs>
2. `$run bind` 到已有 active workstream
3. `$run new <name>` 创建新 workstream
```

When git reports uncommitted changes at integration, use this prompt:

```text
当前 worktree：<path> · git：dirty · commit：uncommitted
请确认：
1. 提交当前变更（先审查 diff，再 commit）
2. 保留当前分支，暂不提交（workstream 保持 open）
3. 继续当前任务，但先记录这些变更的归属
```

Never turn a dirty tree into `ready_to_merge` or `closed` without explicit handling.

## Self-review

```yaml
review_status: good | revise | blocked | escalate
issues: []
recommended_action: "continue Tn"
ask_user: false
auto_mode: true | false
```

Use `verification-before-completion` before every `doing → done`. Evidence must be fresh in the same turn; tests, lint, or build output are not a substitute for user smoke at the integration gate.

## Hard blocks

Stop and ask/escalate for cross-repo confirmation, true product forks, irreversible operations, state contradiction, recover anomaly, bind ambiguity, missing workstream parent, unbound mutation, parallel merge conflict, subagent workspace writes, unresolved workspace, or premature close. Ordinary test failures are revise-and-fix conditions.

## Companion boundaries

Companions provide phase discipline only. They do not own a second workflow, write workspace state, skip task accounting, or close workstreams. The parent `$run` remains the sole writer for `.run-state`, `tasks.md`, and `context.md`.
