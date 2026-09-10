# $run review protocol

`$run review` is meta-maintenance. It scans bounded Markdown artifacts, writes a report under the resolved project, and runs `up` unless `scan-only` is requested. It does not advance tasks, reopen lines, alter `.run-state`, or edit code repos.

## Scope and window

Scope priority: explicit project/workstream → `all`/workspace → current project from `.run-state` → ask when unbound. Default time window is the previous local calendar day, or since the latest report for that scope. Scan only `Projects/<project>/**/{tasks,context,workstream,project}.md`, relevant `.run-state projects[]`, and optional `git worktree list` corroboration.

## Findings

Check R01–R10: auto design-gate leaks, premature close, sibling-line churn, Handoff/task conflicts, illegal multi-doing, protocol corrections, orphan worktrees, index drift, unaccounted engineering work, and incomplete design reviews. Severity is high for R02/R04/R05/R09, medium for R01/R03/R07/R10, low for R06/R08 unless repeated.

Unknown worktree ownership is deferred, not pruned. Recommend `$run review all` or explicit triage when scope is too narrow.

## Reports and maintenance

Write `Projects/<project>/_run-review/YYYY-MM-DD-review.md` (or the scoped equivalent). Include scope, window, workspace, repos, summary, findings, touched workstreams, Skill backlog, and Maintenance applied. In the default second phase, patch the minimum durable skill rules, sync Cursor/Codex/Claude/Agents roots, and list deferred items. Never auto-commit, push, merge, or release.
