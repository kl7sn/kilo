# /kilo workspace and binding protocol

## Resolution

Resolve before any write:

1. Repo `.kilo-state` `workspace:` (highest priority).
2. Else legacy repo `.run-state` `workspace:` (read compat during migration).
3. Non-empty `KILO_WORKSPACE`, else legacy `RUN_WORKSPACE`.
4. Otherwise hard-stop with explicit setup instructions.

The root is a normal Markdown folder. Never silently create or select `~/run-workspace`; it is valid only when explicitly configured. Keep paths with spaces exact and absolute when persisting.

After `/kilo init`, `/kilo new`, `/kilo bind`, or `/kilo adopt`, persist the resolved absolute bound folder in the repo **`.kilo-state`** top-level `workspace` and matching `projects[]` entry (always write `.kilo-state`; do not require deleting a legacy `.run-state`). `/kilo adopt` also writes `worktree_path` / `worktree_branch` on that entry.

## Layout and numbering

```text
<workspace>/Projects/NN-project/
├── project.md
└── NN.MM-line/
    ├── line.md
    ├── tasks.md
    ├── context.md
    ├── review.md (Acceptance + review rounds; created at first draft)
    └── spec.md (optional)
```

Projects use `NN-slug`; lines use `NN.MM-slug`. Allocate the next number under the parent. New homepages must use `project.md` / `line.md`. Legacy unnumbered folders remain readable; do not rename without authorization.

### Line / workstream read-compat

The middle layer is **line**. Write new files and fields as `line.md`, `type: line`, Handoff `line:`, `binding_decision: new-line`.

Still **read** (do not require a bulk rename of existing vaults):

- homepage `workstream.md` if `line.md` is absent
- `type: workstream` as `type: line`
- Handoff `workstream:` as `line:`
- `binding_decision: new-workstream` as `new-line`

On the next successful Handoff write for that binding, persist the new keys (`line:`, `new-line`) without deleting the old file until the user asks.

## `/kilo init`

Resolve the workspace first. Create only `Projects/<projectId>/project.md`; do not create line task files. If the project exists, guide `/kilo new` or `/kilo bind`. Persist the absolute project binding, set `lang`, and stop by default.

## `/kilo new`

Resolve the parent project from an active line, project homepage, or explicit user target. Allocate `NN.MM-slug`, create the homepage plus empty `tasks.md` and `context.md`, append the parent lines row (notes plus `Worktree` / `Branch` / `State`), and bind the session to the new line. Do not pre-create `review.md`; it appears with the first Acceptance draft. Carry the parent `project.md` `## Stable Facts` and `## Gotcha Index` into explore rather than rediscovering them. Do not auto-execute by default. Before allocating a worktree, surface active/smoke-pending sibling worktrees.

For code repos: allocate the primary worktree, write `worktree_path` / `worktree_branch` into Handoff (and the matching `.kilo-state` entry), and set `worktree_status: active`. Record `worktree_status: none` only for pure-docs lines that never touch code. When the creating turn states a pass bar or spec path, seed `review.md` `## Acceptance` as `draft` (`version: 1`) from that turn only (do not mine prior chat). After bind/new completes, run the bidirectional worktree audit (orphan + missing) from [recover.md](recover.md) before recover advance or mutation.

## `/kilo bind`

Match `session_id` → may resume that binding after the bidirectional worktree audit. No session match → always interactive `/kilo bind` / `/kilo new`, even if exactly one active line exists; never auto-bind the sole active line. With two or more candidates for an interactive bind, list them and require an explicit choice; never silently rebind. A project homepage is browse-only unless it has ready/doing tasks. After bind completes, the same orphan/missing audit still applies before further advance.

## `/kilo adopt`

Register an **existing** git worktree of this repo as the **current line's primary**. Does not create directories, does not `git worktree add`, does not rebind the session, does not prune the old path.

```text
/kilo adopt <path>
```

Explicit subcommand, before phase detection. `<path>` is required; resolve to an absolute path before comparing.

A line may have many worktrees over its life, but only **one primary at a time**. After the previous tree is `pruned` or `missing` (merged and removed), adopt attaches the next tree to the **same** line. Do not `/kilo new` for that.

### Preconditions (all required)

1. This session is bound to an open line. Unbound → new-session bind prompt; do not adopt.
2. Handoff `worktree_status` ∈ `{missing, none, pruned}`.
3. `<path>` appears in this repo's `git worktree list --porcelain` (exact match on the resolved absolute path).
4. No **other** line in this repo's `.kilo-state` treats that path as its **current primary**. Current primary means that entry's `worktree_status` ∈ `{active, smoke_pending, ready_to_merge}` and its `worktree_path` resolves to `<path>`. A stale path on `pruned` / `missing` / `none` is not a current primary.

### Effects (success)

Adopt is a **new** primary. Previous-tree smoke/disposition must not close this line.

1. Handoff: `worktree_path` = absolute path; `worktree_branch` = that worktree's current branch; `worktree_status` = `active`; `worktree_git_status` from that directory; `commit_status` = `uncommitted`; `smoke_status` = `pending`; `integration_next` = `none`; `blocker` = none; `binding_decision` = continue-current.
2. `.kilo-state` current `projects[]` entry `worktree_path` / `worktree_branch` match Handoff.
3. Parent `project.md` row: Worktree / Branch / State=`active`.
4. Execution log: path@branch, previous status, and that smoke/integration/commit were reset.
5. Bidirectional worktree audit. The adopted path is no longer an orphan for this line.

No git object changes, no checkout, no branch delete.

### Failures (stop, no state writes)

| Condition | Action |
| --- | --- |
| Unbound session | New-session bind prompt |
| Missing `<path>` | Usage `/kilo adopt <path>`; stop |
| status `active` / `smoke_pending` / `ready_to_merge` | Refuse: already has a primary. Dispose it to pruned/missing/none before swapping |
| path not in this repo's `git worktree list` | Refuse: register existing git dirs only |
| path is another line's current primary | Refuse: do not steal |
| `missing` and the agent uses the main checkout without `/kilo adopt` | Still forbidden. Only an explicit `/kilo adopt <main-checkout-path>` may register the main checkout |

After success, run the orphan/missing audit from [recover.md](recover.md) before recover advance or mutation.

## Language

Resolve `lang` from open Handoff, `.kilo-state`, legacy `.run-state`, `KILO_LANG`, legacy `RUN_LANG`, then `en`. `/kilo lang en|zh` updates the repo default and an open Handoff; historical entries are not bulk-translated. Keep machine literals and parser headings stable.

When writing **user-facing Chinese** (prompts, status explanations, README-style notes, Handoff prose): use everyday words only. **Do not invent shorthand** (关线、先冻后干、状态单写). Call the Markdown files **状态文档**. Prefer `kaola-writing` when polishing Chinese prose.
