# $run auto protocol

`$run auto` sets Handoff `auto_mode: true` and keeps ready tasks flowing in one bound workstream. It never bypasses workspace accounting, verification, hard stops, Acceptance freeze, implementation review, or integration gates.

## Design gates

When explore→plan, a settled scheme choice, or a substantially revised design artifact would normally wait for human confirmation:

1. Set the status tail to `design-review: pending`.
2. Dispatch a read-only reviewer; the reviewer must not edit workspace state.
3. Require this result:

```yaml
verdict: approve | revise | escalate
issues: []
blocking_reasons: []
summary: "one line"
```

4. Record the verdict, design path, and summary in `context.md`.
5. `approve` → continue to plan/execute; `revise` → author fixes and re-review (maximum two cycles); `escalate` → full-stop.

Never ask the user to “confirm” or “continue” to unlock an ordinary design gate in auto mode.

On design `approve`, write or refresh `## Acceptance` from the approved success criteria and set `status: frozen` (auto may freeze without a human echo). Proceed to execute only after Acceptance is frozen on code workstreams.

## Implementation review gates

When all tasks are `done` (or an explicit `$run review` is in flight):

1. Set `impl-review: pending` / `re_review` on the status tail.
2. Dispatch the read-only implementation reviewer per [execute.md](execute.md) (Acceptance + ReviewThread + git attachments).
3. Parent appends the reviewer round to `## ReviewThread`.
4. `verdict: approve` with no blocking open findings → `impl_review_status: approved`, then the normal integration/smoke hard-stop (auto must not guess disposition).
5. `revise` → parent writes implementer triage, opens/reopens tasks, fixes, re-reviews (maximum two cycles after the first finding round), then escalate.
6. `escalate`, or any `deferred`/`disagreed` needing human authority → full-stop with `ask_user` populated; do not enter smoke.

Auto mode must not ask the user to paste review text between agents; Thread is the transport.

## True forks and hard stops

Escalate only when the decision changes target user, business goal, non-goals, capability, irreversible release/data/compliance policy, or requires new authority. Also stop for unresolved workspace, bind ambiguity, illegal multi-doing, state contradiction, impossible verification, Acceptance not frozen on code lines, unresolved ReviewThread human asks, or irreversible git/production operations.

## Status and exit

Use `auto=on` in every advancing status line while enabled. “Exit auto” or an explicit plain `$run` exit sets `auto_mode: false`. Full-stop requires a task blocker, Handoff refresh, and resume hint.
