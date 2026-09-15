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
commit_status: committed | uncommitted | unknown | not-applicable | merged
binding_decision: pending | continue-current | bind-existing | new-workstream
impl_review_status: none | pending | in_triage | re_review | approved | escalated
acceptance_status: missing | draft | frozen
```

Never encode compound or free-form values in these fields. Automated smoke belongs in `notes` or the execution log.

`worktree_git_status`, `commit_status`, and `binding_decision` are durable decision fields, not prose. `commit_status: uncommitted` blocks close. Keep `binding_decision` values as listed; `binding_decision: pending` blocks add-task and mutation for fit drift, missing worktree, and new-session unbound cases.

`impl_review_status: none` is for docs-only lines. Code workstreams use the other values per [execute.md](execute.md) implementation review gate. `acceptance_status` mirrors `## Acceptance.status` for Handoff convenience when useful; `## Acceptance` remains authoritative.

## Acceptance and ReviewThread

`context.md` durable sections (parent writes; reviewers read-only):

```text
## Handoff
## Acceptance
## ReviewThread
## Claims          # optional
## Gotchas
```

### Acceptance template

```yaml
## Acceptance
status: missing|draft|frozen
updated: <iso>
user_prompt: |
  <verbatim>
spec_anchors:
  - path: "<doc>"
    note: "<sheet/section>"
constraints: []
pass_bar: "<one line>"
```

### ReviewThread template

```yaml
## ReviewThread
status: open|resolved|escalated
cycle: <int>
updated: <iso>
rounds:
  - id: R1
    role: reviewer
    at: <iso>
    commit: <optional>
    acceptance_result: supported|partial|refuted
    summary: "<one line>"
    findings:
      - id: F1
        severity: high|medium|low
        title: "<short>"
        evidence: []
        status: open|fixed|deferred|disagreed|waived
  - id: R1b
    role: implementer
    at: <iso>
    commit: <sha or ->
    summary: "<one line>"
    responses:
      - finding: F1
        disposition: fixed|deferred|disagreed|waived
        note: "<short>"
    open_risks: []
    ask_user: []
```

Rules: reviewer rounds only append findings; implementer rounds only set dispositions via `responses`. Do not paste Thread contents through the user as the transport — the parent loads Thread into the next `$run review` prompt.

### Acceptance freeze prompt

```text
请确认本 workstream 验收标准（确认后冻结，开发闲聊不再改）：
1. 对照：<spec path / sheet>
2. 约束：<constraints>
3. 通过线：<pass_bar>；测试全绿不算通过
回复：确认 / 或直接改这三行
```

### Review triage prompt (deferred / disagreed)

```text
审核回合 R<n> 需要你裁决：
- deferred: <ids/titles>
- disagreed: <ids/titles>
请选择每项：接受延期(waive进smoke) / 必须补齐(转fix task) / 采纳异议 / 驳回异议
未决前不进人工 smoke。
```

## Progress and integration prompt

Every advancing reply starts with a `$run` status line that includes `wt=<short-path|missing|none>` for the primary worktree, plus the resolved binding, phase, current task statuses, and one next action. Do not put `dirty`, `branch`, or `primary=` in the compact status line. Emit it after recovery, task transitions, verification, phase changes, and stops; never wait for a user status request.

While impl-review is active, include `impl-review: pending|in_triage|re_review|approved|escalated` in the status tail.

When all task rows are done, tests are fresh, **impl-review is approved** (code lines), and the worktree is not explicitly disposed, use this prompt:

```text
当前任务已完成，自动验证与实现审核已通过；worktree 仍为 <status>。
请确认：
1. 当前 worktree 已完成，并提供人工 smoke + integration disposition；
2. 继续当前 worktree；或
3. 新建 worktree/workstream 后再继续。
```

The prompt is a hard integration gate. `ready_to_merge` means technically ready, not human-confirmed complete. Never infer a new worktree request or close disposition from silence. Do not show this prompt while `impl_review_status` is `pending`, `in_triage`, `re_review`, or `escalated`.

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

## Close confirmation phrases

Treat these as **explicit smoke waiver** when tasks are done and integration disposition is already set (`merge` / `pr` / `keep-branch` / `prune`):

- 「可以关闭了」「关掉这条线」「close the workstream」「关闭 workstream」

Set `smoke_status: waived-by-user`, `status: closed`, `auto_mode: false`, and record the waiver in the execution log. Do not invent a passed smoke. If disposition is still unset, ask for disposition before closing.

## Post-merge local reclaim

After an MR is merged into the Handoff branch (or the user says code is merged):

1. `git fetch` the target branch; confirm MR state `merged` when a forge CLI is available.
2. Move the primary checkout onto the target tip (`git pull --ff-only` when already on that branch).
3. Delete the local source branch; `git remote prune origin` for deleted remote refs.
4. Drop only the WIP stash created for that MR rebase (do not blanket-drop unrelated stashes).

**Branch held by another worktree:** `git checkout <target>` fails with `already used by worktree at <path>`. Do not force the other worktree. If that worktree is clean:

1. Fast-forward it to the merge tip.
2. `git checkout --detach HEAD` there to free the branch name (or switch it to an explicit park branch if the user prefers).
3. Reclaim `<target>` in the primary path.

Record the other worktree's detached/park state in Handoff `notes` so it is not treated as an unexplained orphan later.

## `.run-state` write safety

`.run-state` is structured YAML-ish with a `projects:` list plus trailing runtime keys. Never rewrite it with naive line-stripping or regex that can delete the `projects:` body. Prefer surgical field updates (replace one `note:` / `status:` line under a known `project:` block, or append only the trailing `- updated:` / `- next_action:` keys). If the file is corrupted, restore from conversation-known bindings or a backup before continuing `$run`.

## Self-review

```yaml
review_status: good | revise | blocked | escalate
issues: []
recommended_action: "continue Tn"
ask_user: false
auto_mode: true | false
```

Use `verification-before-completion` before every `doing → done`. Evidence must be fresh in the same turn; tests, lint, or build output are not a substitute for user smoke at the integration gate.

Parent-chain self-review (`review_status`) is **not** a substitute for the implementation review gate (`impl_review_status` + `## ReviewThread`). Self-review cannot approve smoke entry alone on code workstreams.

## Hard blocks

Stop and ask/escalate for:

- new-session unbound (no bind/new yet — no restore or code mutation)
- worktree-missing (`worktree_status: missing` unresolved)
- sole-active silent bind (forbidden — never auto-bind the only active workstream without explicit `$run bind` / user choice)
- mutation outside primary worktree
- Acceptance not frozen on a code workstream when entering execute, `$run review`, or smoke/close
- unresolved ReviewThread blockers (`open` high findings, undecided `disagreed`/`deferred`/`ask_user`) when entering smoke/close
- cross-repo confirmation, true product forks, irreversible operations, state contradiction, recover anomaly, bind ambiguity, missing workstream parent, unbound mutation, parallel merge conflict, subagent workspace writes, unresolved workspace, or premature close

Ordinary test failures are revise-and-fix conditions.

## Companion boundaries

Companions provide phase discipline only. They do not own a second workflow, write workspace state, skip task accounting, or close workstreams. The parent `$run` remains the sole writer for `.run-state`, `tasks.md`, and `context.md`.
