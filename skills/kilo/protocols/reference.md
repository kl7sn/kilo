# $kilo reference

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

`impl_review_status: none` is for docs-only lines. Code workstreams use the other values per [execute.md](execute.md) implementation review gate. `acceptance_status` mirrors `review.md` `## Acceptance.status` so gates can fire without opening that file; `review.md` remains authoritative.

## Acceptance and review file

Parent writes every durable file; reviewers read only. Acceptance is the audit contract and the rounds audit it, so both live in `review.md` — one attachment for the reviewer, and `context.md` stays small enough to reload every turn.

```text
context.md               # reloaded every turn
├── ## Handoff           # includes acceptance_status + impl_review_status mirrors
├── ## Gotchas           # line-local
├── ## Key Decisions
└── ## Execution Log

review.md                # created at Acceptance freeze (or first review/claim)
├── ## Acceptance        # frozen pass bar, versioned
├── ## ReviewIndex       # finding → task → commit → status
├── ## Claims            # optional
└── ## ReviewThread      # reviewer / implementer rounds
```

`context.md` has no pointer block. Handoff `acceptance_status` and `impl_review_status` are the only cheap signals: read `review.md` when `acceptance_status` is not `frozen` and a freeze/revise is due, when `impl_review_status` is `pending|in_triage|re_review`, when `$kilo review` runs, or when the user asks about a finding or a task's review history. `review.md` always wins over a stale mirror; refresh the mirror instead of editing history.

### Acceptance template (in `review.md`)

```yaml
## Acceptance
status: missing|draft|frozen
version: <int>
supersedes: <prior version or ->
updated: <iso>
user_prompt: |
  <verbatim>
spec_anchors:
  - path: "<doc>"
    note: "<sheet/section>"
constraints: []
pass_bar: "<one line>"
```

`version` starts at 1 and increments only on an explicit revise (`$kilo accept …` / 「验收改成…」). Each reviewer round records the `acceptance_version` it audited, so an approval never silently covers a later, wider bar.

### ReviewIndex template (in `review.md`)

```markdown
| Finding | Severity | Task | Commit | Status | Round |
|---|---|---|---|---|---|
| F1 | high | T06 | <sha> | fixed | R1 → R2 |
```

This table is the lookup path for "what did review say about `Txx`, and what changed"; keep one row per finding and update it whenever a disposition changes.

### ReviewThread template (in `review.md`)

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
    acceptance_version: <int>
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

Rules: reviewer rounds only append findings; implementer rounds only set dispositions via `responses`, and each response names the fixing task plus commit. Do not paste Thread contents through the user as the transport — the parent passes `review_file` and a digest into the next `$kilo review` prompt. Append rounds; never rewrite or compact history in place.

## Inherited project knowledge

Project level stores **facts and pointers, never copies**. Full gotcha text stays in the workstream that learned it.

| Location | Holds | Read when |
|---|---|---|
| `project.md` `## Stable Facts` | long-lived verifiable facts every line needs: build/run commands, directory conventions, external-system quirks | every explore/plan, and before the first mutation of a new line |
| `project.md` `## Gotcha Index` | one pointer line per topic: `- <topic>: <one-line conclusion> → [[01.03-slug/context]]` | same; follow a pointer only when its topic touches this line |
| `context.md` `## Gotchas` | full text, line-local | every recover |
| `context.md` `## Key Decisions` | this line's decisions | on demand — **not** inherited, not indexed, not required reading |

### Promotion order

Before writing anything at project level, try to mechanize:

1. Can it become a test, lint rule, type constraint, or CI check? **Do that instead** and record the check in the execution log. A mechanized constraint needs no document entry.
2. Not mechanizable, and it is a durable fact (command, convention, external contract)? Add one line to `## Stable Facts`.
3. Not mechanizable, and it is a trap another line could hit? Add one pointer line to `## Gotcha Index`; leave the detail in the origin `context.md`.
4. Otherwise it stays line-local. Uncertainty is not a reason to promote — the default is *don't*.

Both project-level sections are bounded and pruned: delete a fact the moment it stops being true, and drop an index entry once the codebase enforces it or the origin line is archived. A stale entry is worse than a missing one, because agents obey it.

Never copy `context.md` gotcha text upward, never restate a project fact back down, and never let an index line grow into reproduction steps.

### Fact drift and conflict

A landed fact is only "current truth", not settled history. Later lines change requirements, so a fact will eventually contradict the work in hand. Silent coexistence is the failure mode: this line builds on the new understanding while `project.md` keeps teaching the next line the old concept.

When explore/plan finds that this line will change or invalidate a project-level fact or index conclusion:

1. **Do not route around it.** Record the conflict as a task row (or an explicit plan decision naming the entry), so the update is accounted for instead of remembered.
2. **Check who is mid-flight.** If any sibling row in the workstreams table is `active` or `smoke_pending`, that line may be building on the old fact — surface the conflict and ask the user before changing shared truth.
3. **Update in place at close.** Replace the entry with the new current value and re-tag its origin line. `## Stable Facts` and `## Gotcha Index` hold only what is true now; do not accumulate a changelog there.
4. **Put the history where history lives.** Why it changed (old → new, trigger) goes into this line's `context.md` `## Key Decisions`.
5. **Check Acceptance.** If the invalidated fact is referenced by this line's `spec_anchors` or `constraints`, the frozen bar no longer describes reality: revise Acceptance explicitly (`version+1`) rather than reinterpreting it.

An index conclusion that this line disproved must be rewritten or deleted in the same turn — never left pointing at a `context.md` whose conclusion no longer holds.

A fact entry may carry an optional `check:` (command or path) that makes it cheaply falsifiable. Verify it only when that fact bears on the current task; a `check:` that now fails is a drift signal, not a blocker to work around.

`project.md` also tracks each workstream's worktree (`Worktree`, `Branch`, `State` columns) using the Handoff enums, so sibling lines with an `active` or `smoke_pending` worktree are visible without opening every `context.md`. The parent refreshes those cells on `$kilo new`, at the integration gate, and on disposition.

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

Every advancing reply starts with a `$kilo` status line that includes `wt=<short-path|missing|none>` for the primary worktree, plus the resolved binding, phase, current task statuses, and one next action. Do not put `dirty`, `branch`, or `primary=` in the compact status line. Emit it after recovery, task transitions, verification, phase changes, and stops; never wait for a user status request.

While impl-review is active, include `impl-review: pending|in_triage|re_review|approved|escalated` in the status tail.

When all task rows are done, tests are fresh, **impl-review is approved** (code lines), and the worktree is not explicitly disposed, use this prompt:

```text
当前任务已完成，自动验证与实现审核已通过；worktree 仍为 <status>。
请确认：
1. 当前 worktree 已完成，并提供人工 smoke + integration disposition；
2. 继续当前 worktree；或
3. 新建 worktree/workstream 后再继续。
树已 prune、线仍 open 时，下一棵树用 `$kilo adopt <path>`，不必 `$kilo new`。
```

The prompt is a hard integration gate. `ready_to_merge` means technically ready, not human-confirmed complete. Never infer a new worktree request or close disposition from silence. Do not show this prompt while `impl_review_status` is `pending`, `in_triage`, `re_review`, or `escalated`.

## Binding and code-management prompts

New session unbound — no restored workstream binding yet:

```text
新会话尚未绑定 workstream。
请选择：
1. `$kilo bind` — 绑定已有 active workstream（并校验其 worktree）
2. `$kilo new <name>` — 新建 workstream + 对应 worktree
未绑定前不会恢复或改代码。
```

Non-continuation / pile-up risk — request does not clearly continue the bound line:

```text
当前绑定：<project>/<workstream> · worktree：<path|missing>
当前任务：<doing/ready 摘要>
本次请求不像续做上述任务。
请确认：
1. 仍属当前线：说明对应哪个任务后继续
2. 关闭当前 workstream（先走 integration/smoke/disposition）再 `$kilo new <name>`
3. `$kilo bind` 到其它 active workstream
```

Missing worktree — Handoff path/branch not present in `git worktree list`:

```text
worktree 缺失：Handoff 登记 <path>@<branch>，git worktree list 无对应。
请确认：
1. 按登记重建 worktree
2. `$kilo adopt <path>`（path 已在 git worktree list）
3. 关闭当前线后 `$kilo new <name>`
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

## `.kilo-state` write safety

`.kilo-state` is structured YAML-ish with a `projects:` list plus trailing runtime keys. Never rewrite it with naive line-stripping or regex that can delete the `projects:` body. Prefer surgical field updates (replace one `note:` / `status:` line under a known `project:` block, or append only the trailing `- updated:` / `- next_action:` keys). If the file is corrupted, restore from conversation-known bindings or a backup before continuing `$kilo`.

## Self-review

```yaml
review_status: good | revise | blocked | escalate
issues: []
recommended_action: "continue Tn"
ask_user: false
auto_mode: true | false
```

Use `verification-before-completion` before every `doing → done`. Evidence must be fresh in the same turn; tests, lint, or build output are not a substitute for user smoke at the integration gate.

Parent-chain self-review (`review_status`) is **not** a substitute for the implementation review gate (`impl_review_status` + `review.md`). Self-review cannot approve smoke entry alone on code workstreams.

## Hard blocks

Stop and ask/escalate for:

- new-session unbound (no bind/new yet — no restore or code mutation)
- worktree-missing (`worktree_status: missing` unresolved)
- `$kilo adopt` when `worktree_status` is `active` / `smoke_pending` / `ready_to_merge`, or when `<path>` is not in this repo's `git worktree list`, or when `<path>` is another line's current primary
- sole-active silent bind (forbidden — never auto-bind the only active workstream without explicit `$kilo bind` / user choice)
- mutation outside primary worktree
- Acceptance not frozen on a code workstream when entering execute, `$kilo review`, or smoke/close
- unresolved review blockers in `review.md` (`open` high findings, undecided `disagreed`/`deferred`/`ask_user`) when entering smoke/close
- Acceptance or review rounds inlined into `context.md` instead of `review.md`
- gotcha text copied into `project.md` instead of a pointer, or a mechanizable constraint written as prose without attempting the test/lint route
- a known conflict with a project-level fact or index conclusion left unrecorded and unresolved at close (silent divergence), or shared truth rewritten while a sibling line is `active`/`smoke_pending` without asking the user
- tasks added or reopened after `impl_review_status: approved` without resetting to `re_review`
- an appended task that widens the deliverable beyond the frozen Acceptance, without an explicit revise or `$kilo new`
- cross-repo confirmation, true product forks, irreversible operations, state contradiction, recover anomaly, bind ambiguity, missing workstream parent, unbound mutation, parallel merge conflict, subagent workspace writes, unresolved workspace, or premature close

Ordinary test failures are revise-and-fix conditions.

## Companion boundaries

Companions provide phase discipline only. They do not own a second workflow, write workspace state, skip task accounting, or close workstreams. The parent `$kilo` remains the sole writer for `.kilo-state`, `tasks.md`, `context.md`, and `review.md`.
