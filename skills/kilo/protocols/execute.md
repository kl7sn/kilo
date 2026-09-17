# $run execution protocol

## Phase routing

- Missing or incomplete design → explore and write `spec.md`. `spec.md` is the input contract (target state the review compares against), not a running log; evidence goes to `## Execution Log`. Read `project.md` `## Stable Facts` and `## Gotcha Index` first, and follow an index pointer only when its topic touches this line, so a sibling's trap is not rediscovered without reading everything it wrote. If this line's design contradicts one of those entries, record the conflict now per the fact-drift rules in [reference.md](reference.md); never route around a stale entry silently.
- Design exists and all task rows are todo → plan and create an acyclic task table with at least one ready row.
- Plan complete / about to enter execute → **Acceptance freeze gate** (code workstreams).
- Ready rows and Acceptance frozen (or docs-only) → execute.
- Blocked only → report blockers.
- All rows done → **implementation review gate**, then integration gate; do not auto-close.
- Explicit `$run review` → same review gate on demand (does not require all tasks done).

## Acceptance freeze gate

Code workstreams (`worktree_status` not `none`) must freeze acceptance **before the first execute mutation**. Do not mine the chat transcript for acceptance after the fact.

`## Acceptance` lives in the workstream `review.md`, next to the rounds that audit it; create that file at the first draft. Handoff keeps only the `acceptance_status` mirror.

### Capture moments

| Moment | Action |
|---|---|
| `$run new` / first demand mapping | Draft `## Acceptance` in `review.md` from **this turn's** user message and/or plan success criteria (`status: draft`) |
| explore→plan / design settle | Refresh draft from approved success criteria; still `draft` |
| **plan→execute** | Emit the freeze prompt; user confirms or edits → `status: frozen` |
| Later chat | **Do not** update Acceptance |
| Explicit revise | Only `$run accept …` or clear「验收改成…」→ back to `draft`, bump `version`, set `supersedes`, then re-freeze |

`worktree_path` / `worktree_branch` always come from Handoff, never from chat.

### Freeze prompt

```text
请确认本 workstream 验收标准（确认后冻结，开发闲聊不再改）：
1. 对照：<spec path / sheet>
2. 约束：<e.g. slaveId=22>
3. 通过线：<human pass bar；测试全绿不算通过>
回复：确认 / 或直接改这三行
```

In `$run auto`, freeze from the design-approved success criteria without waiting; still write `## Acceptance` with `status: frozen` and the verbatim pass bar.

### `## Acceptance` shape

```yaml
## Acceptance
status: missing|draft|frozen
version: <int>
supersedes: <prior version or ->
updated: <iso>
user_prompt: |
  <verbatim short acceptance; do not soften>
spec_anchors:
  - path: "<doc or xlsx>"
    note: "<sheet / section>"
constraints: []
pass_bar: "<one line>"
```

Hard-stop execute mutation, `$run review`, and smoke/close when Acceptance is `missing` or `draft` on a code workstream. Softening `user_prompt` after freeze is forbidden; reopen via explicit revise only.

Optional implementer self-attestations (`## Claims` in `review.md`) may support Acceptance but must not replace it.

### Appended tasks vs a frozen Acceptance

Acceptance is per workstream, not per task, so appending work does **not** mint a new Acceptance by default:

| Appended work | Acceptance | Review |
|---|---|---|
| Fixing a finding, adding tests/docs, refactor inside the same deliverable | unchanged, same `version` | reset `impl_review_status` to `re_review`; re-audit against the same bar |
| New capability or deliverable beyond the frozen bar, still this line | explicit revise: `draft` → bump `version` → re-freeze | new review cycle against the new `version` |
| New capability that is really a different line | untouched | `$run new` under the parent (strict workstream fit) |

Any task added or reopened after `impl_review_status: approved` invalidates that approval — set `re_review` in the same turn. An approval recorded against `acceptance_version: 1` never covers `version: 2`.

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

When useful, append a falsifiable entry to `review.md` `## Claims` (task id, claim sentence, `must_trace`, `disproof_hint`). Claims serve Acceptance; tests alone are not a claim.

## Implementation review gate

For code workstreams, after all tasks are `done` with fresh evidence (or on `$run review`), run an adversarial review **before** the human smoke prompt. Docs-only lines (`worktree_status: none`) skip this gate.

Parent is the sole writer of workspace files. Cross-agent review state lives in the workstream `review.md` — never ask the user to copy-paste long reports between agents.

### Review file separation

Acceptance plus rounds are the audit contract and its history; they grow every cycle, so they do **not** live in `context.md`.

- `review.md` (same workstream folder) holds `## Acceptance`, `## ReviewIndex`, `## Claims`, and `## ReviewThread` rounds.
- `context.md` gets no pointer block. Handoff `acceptance_status` and `impl_review_status` are the cheap signals; never inline Acceptance text, round bodies, findings prose, or reviewer reports into `context.md`.
- Open `review.md` when a freeze/revise is due, when `impl_review_status` is `pending|in_triage|re_review`, when `$run review` runs, or when the user asks about a finding or a task's review history. Prefer Acceptance + index + rounds still `open`/`fixed`, not the whole file.
- If a Handoff mirror and `review.md` disagree, `review.md` wins; refresh the mirror instead of editing history.

### Dispatch (`$run review`)

1. Require Acceptance `status: frozen`; else hard-stop with the freeze prompt.
2. Set Handoff `impl_review_status: pending` (first pass) or `re_review`.
3. Build the reviewer prompt (short human ask + mechanical attachments):

```text
帮我确认下目前的版本 <Handoff.worktree_path>
分支 <Handoff.worktree_branch>
是否按照这个文档实现了功能
<Acceptance.user_prompt 原样>

--- 机械附件（只读）---
base..HEAD: <merge-base>..HEAD
diff_stat: <git diff --stat>
key_paths: <Handoff.key_paths>
gotchas: <Gotchas if any>
project_facts: <project.md ## Stable Facts if any>
review_file: <abs path to review.md>
acceptance_version: <## Acceptance.version>
review_digest: <ReviewIndex + rounds with open/fixed findings; full file only when cycles ≤ 1>
implementer_claims: <## Claims if any>
note: 测试全绿不能单独视为 Acceptance 通过；请对照 spec 证伪。有历史回合时优先复核 open/fixed 项，勿从零另起炉灶；需要更多上下文时自行读取 review_file。
```

4. Dispatch a **read-only** reviewer subagent. It must not edit `.run-state`, `tasks.md`, `context.md`, `review.md`, or product code.
5. Append a `role: reviewer` round to `review.md` `## ReviewThread` from the returned YAML (including the audited `acceptance_version`), update `## ReviewIndex`, then refresh the Handoff mirror. Do not rewrite prior finding dispositions in place.

### Reviewer return schema

```yaml
verdict: approve | revise | escalate
acceptance_version: <int audited>
acceptance_result: supported | partial | refuted
claim_results: []   # optional: id, status, note
findings:
  - id: F1
    severity: high|medium|low
    title: "<short>"
    evidence: ["path:…"]
    status: open
blocking_reasons: []
summary: "one line"
```

`approve` is illegal when any blocking `open` finding remains, or when `acceptance_result` is `refuted` without user waiver.

### Triage (parent / implementer)

After a reviewer round, set `impl_review_status: in_triage` and append a `role: implementer` round to `review.md`:

| disposition | Action |
|---|---|
| `fixed` | Add/reopen task, implement, verify, then record response with commit |
| `deferred` | Put in `ask_user`; block smoke until user accepts or waives |
| `disagreed` | Put in `ask_user`; user adjudicates before re-review or smoke |
| `waived` | Only after explicit user waiver; record who/when |

Every implementer response must name the task that carried the fix and the commit, so `## ReviewIndex` can answer "what did review say about T06 and what changed" without replaying chat.

Then either continue execute on new/reopened tasks, or `$run review` again with the digest plus `review_file` attached. Maximum **two** full review cycles after the first finding round; then `escalate` / `impl_review_status: escalated` unless the user extends.

### Entering human smoke

Allowed only when all of:

1. Acceptance is `frozen`
2. `impl_review_status: approved` (latest reviewer `verdict: approve`, or remaining blockers explicitly `waived` by the user)
3. No blocking finding still `open` / unresolved `disagreed` / unanswered `ask_user`

Otherwise stay in review/triage; do not present the smoke disposition prompt as if the line were complete.

## Integration gate

Automated tests and impl-review satisfy machine gates but cannot close a workstream. Closing requires:

1. Every task done with evidence.
2. Implementation review gate passed (`impl_review_status: approved`) on code workstreams.
3. User-confirmed smoke (`passed`) or explicit waiver (`waived-by-user`).
4. `integration_next` set to `merge`, `pr`, `keep-branch`, or `prune`.
5. Any worktree disposition executed or explicitly deferred with `keep-branch`.
6. The `project.md` workstream row refreshed (`Worktree` / `Branch` / `State`). For anything learned that reaches sibling lines, run the promotion order in [reference.md](reference.md): mechanize first, else one `## Stable Facts` line or one `## Gotcha Index` pointer. Decisions stay line-local.
7. Every project-level fact or index conclusion this line invalidated is updated in place to the new current truth, with the reason recorded in `## Key Decisions`. A line may not close while leaving a contradiction behind.

Until then keep Handoff open with `smoke_status: pending` and, when applicable, `worktree_status: smoke_pending`.

After impl-review is approved, proactively inspect the worktree rather than waiting for a status question. If completion, smoke, or disposition is not explicit, ask the user whether to:

1. finish the current worktree (then provide smoke evidence and choose `merge`, `pr`, `keep-branch`, or `prune`);
2. continue with another task in the current worktree; or
3. create a new worktree/workstream before further mutations.

This prompt is required in normal and auto mode. Auto mode may not guess the answer or close the line on the user's behalf.

## After merge

When the user reports the MR/PR is merged (or forge shows `merged`):

1. Run the post-merge local reclaim steps in [reference.md](reference.md) (including the “branch held by another worktree” path).
2. Set Handoff `commit_status: merged` and `integration_next` to the disposition that matches reality (`merge` if already merged into the target, else `keep-branch`).
3. Keep `smoke_status: pending` until the user confirms smoke or uses an explicit close/waiver phrase.
4. Do not leave the primary checkout on a deleted source branch tip.
