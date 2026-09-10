# Design: $run session ↔ workstream ↔ worktree strong binding

**Date:** 2026-09-10  
**Status:** approved  
**Workstream:** `05-run/05.03-strong-binding`  
**Approach:** A — hard invariants + dual gates (session bind + strict task fit)

## Problem

1. Without an explicit close/new decision, agents keep appending tasks to one workstream.
2. Tasks can remain on a workstream while the registered code worktree is gone, leaving unmerged or “lost” commits.
3. New sessions can silently inherit a binding, which weakens accountability.

## Goals

- Enforce **one session ↔ one workstream ↔ one primary code worktree**.
- New sessions **must** `$run bind` or `$run new` before recover/execute.
- Non-continuation requests **must** stop for continue / close+new / bind.
- Bidirectional worktree audit: **orphan** (git has, state lacks) and **missing** (state has, git lacks).
- `missing` is a hard stop: recreate / adopt path / close then `$run new`.

## Non-goals

- No new `run` binary or auto-selection of workstreams.
- No silent prune or silent worktree recreate.
- No soft thresholds (“N tasks done → suggest close”).
- Subagent isolation worktrees remain allowed; they are not the primary binding.

## Invariants

| Binding | Rule |
|---|---|
| session → workstream | One open workstream per session. No session_id match → hard stop; never auto-bind the sole active line. |
| workstream → worktree | At most one primary `worktree_path` + `worktree_branch`. |
| task landing | Code mutations only inside that primary worktree. Never fall back to the main checkout when status is `missing`. |

### Continuation (strict)

A request may proceed without a binding decision only if it:

- clearly targets the current `doing` or a specific `ready` task (including `Txx`), or
- explicitly says continue / finish the current task when exactly one sensible target exists.

Everything else (including “顺便”, “再加一个”) requires an explicit decision.

## Recover audit

On recover / bind / new / integration:

1. `git worktree list --porcelain`
2. Compare to Handoff `worktree_path` / `worktree_branch`
3. Compare to `.run-state projects[]` for the same repo

| Finding | Definition | Action |
|---|---|---|
| orphan | Present in git, absent from Handoff and matching `.run-state` | Hard stop: adopt/register / keep-for-later / prune (explicit auth) |
| missing | Recorded in Handoff, absent from git worktree list | Hard stop: recreate / adopt existing path / close then `$run new` |

On `missing`: set `worktree_status: missing`, `binding_decision: pending`, `blocker: worktree-missing`. Surface branch tips / reflog hints when commits may be stranded.

New session with no `session_id` binding: emit bind/new prompt only; do not advance into execute.

## Task-fit gate

Before adding a task row or starting mutations:

1. If not a continuation → `binding_decision: pending`
2. Emit the standard three-way prompt
3. Until resolved: no new task rows, no code mutations

`$run auto` treats these gates as hard stops (no guessing).

## Enums and prompts

Extend `worktree_status` with `missing`.

Keep `binding_decision: pending | continue-current | bind-existing | new-workstream`.

Standard prompts (zh):

- New session unbound
- Non-continuation / pile-up risk
- Missing worktree

(Exact copy lives in `skills/run/protocols/reference.md` after implementation.)

## File touchpoints

| File | Change |
|---|---|
| `skills/run/SKILL.md` | Critical rules + startup route for 1:1 binding, mandatory session bind, strict fit, missing hard-stop |
| `skills/run/protocols/recover.md` | Bidirectional audit, session bind gate, missing triage |
| `skills/run/protocols/execute.md` | Strict fit before add-task; require primary worktree `active` before mutation |
| `skills/run/protocols/reference.md` | `missing` enum, prompt templates, hard blocks |
| `skills/run/protocols/workspace.md` | `$run bind`/`new` must register and verify worktree; no sole-active auto-bind |
| `templates/context.md`, `templates/context.zh.md` | Handoff examples for `missing` / `binding_decision` |
| `README.md`, `README_CN.md` | Short note on strong binding + strict gates |

## Acceptance

- Protocol text forbids silent sole-active bind on a new session.
- Protocol defines and hard-stops `missing` worktree with the three options above.
- Protocol requires an explicit decision before adding non-continuation tasks.
- Templates and READMEs mention the invariants.
- `~/.cursor/skills/run` remains the repo symlink; no duplicate skill copy.
