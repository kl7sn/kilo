# $run auto protocol

`$run auto` sets Handoff `auto_mode: true` and keeps ready tasks flowing in one bound workstream. It never bypasses workspace accounting, verification, hard stops, or integration gates.

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

## True forks and hard stops

Escalate only when the decision changes target user, business goal, non-goals, capability, irreversible release/data/compliance policy, or requires new authority. Also stop for unresolved workspace, bind ambiguity, illegal multi-doing, state contradiction, impossible verification, or irreversible git/production operations.

## Status and exit

Use `auto=on` in every advancing status line while enabled. “Exit auto” or an explicit plain `$run` exit sets `auto_mode: false`. Full-stop requires a task blocker, Handoff refresh, and resume hint.
