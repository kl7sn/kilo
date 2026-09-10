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
worktree_status: none | active | missing | smoke_pending | ready_to_merge | pruned
smoke_status: pending | passed | waived-by-user
integration_next: none | merge | pr | keep-branch | prune
worktree_git_status: clean | dirty | unknown | not-applicable
commit_status: committed | uncommitted | unknown | not-applicable
binding_decision: pending | continue-current | bind-existing | new-workstream
```

Never encode compound or free-form values in these fields. Automated smoke belongs in `notes` or the execution log.

`worktree_git_status`, `commit_status`, and `binding_decision` are durable decision fields, not prose. `commit_status: uncommitted` blocks close. Keep `binding_decision` values as listed; `binding_decision: pending` blocks add-task and mutation for fit drift, missing worktree, and new-session unbound cases.

## Progress and integration prompt

Every advancing reply starts with a `$run` status line that includes `wt=<short-path|missing|none>` for the primary worktree, plus the resolved binding, phase, current task statuses, and one next action. Do not put `dirty`, `branch`, or `primary=` in the compact status line. Emit it after recovery, task transitions, verification, phase changes, and stops; never wait for a user status request.

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

New session unbound — no restored workstream binding yet:

```text
新会话尚未绑定 workstream。
请选择：
1. `$run bind` — 绑定已有 active workstream（并校验其 worktree）
2. `$run new <name>` — 新建 workstream + 对应 worktree
未绑定前不会恢复或改代码。
```

Non-continuation / pile-up risk — request does not clearly continue the bound line:

```text
当前绑定：<project>/<workstream> · worktree：<path|missing>
当前任务：<doing/ready 摘要>
本次请求不像续做上述任务。
请确认：
1. 仍属当前线：说明对应哪个任务后继续
2. 关闭当前 workstream（先走 integration/smoke/disposition）再 `$run new <name>`
3. `$run bind` 到其它 active workstream
```

Missing worktree — Handoff path/branch not present in `git worktree list`:

```text
worktree 缺失：Handoff 登记 <path>@<branch>，git worktree list 无对应。
请确认：
1. 按登记重建 worktree
2. 认领已有路径：<用户给出 path>
3. 关闭当前线后 `$run new <name>`
未决前禁止改代码。
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

Stop and ask/escalate for:

- new-session unbound (no bind/new yet — no restore or code mutation)
- worktree-missing (`worktree_status: missing` unresolved)
- sole-active silent bind (forbidden — never auto-bind the only active workstream without explicit `$run bind` / user choice)
- mutation outside primary worktree
- cross-repo confirmation, true product forks, irreversible operations, state contradiction, recover anomaly, bind ambiguity, missing workstream parent, unbound mutation, parallel merge conflict, subagent workspace writes, unresolved workspace, or premature close

Ordinary test failures are revise-and-fix conditions.

## Companion boundaries

Companions provide phase discipline only. They do not own a second workflow, write workspace state, skip task accounting, or close workstreams. The parent `$run` remains the sole writer for `.run-state`, `tasks.md`, and `context.md`.
