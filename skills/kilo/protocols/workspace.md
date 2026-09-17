# $kilo workspace and binding protocol

## Resolution

Resolve before any write:

1. Repo `.kilo-state` `workspace:` (highest priority).
2. Else legacy repo `.run-state` `workspace:` (read compat during migration).
3. Non-empty `KILO_WORKSPACE`, else legacy `RUN_WORKSPACE`.
4. Otherwise hard-stop with explicit setup instructions.

The root is a normal Markdown folder. Never silently create or select `~/run-workspace`; it is valid only when explicitly configured. Keep paths with spaces exact and absolute when persisting.

After `$kilo init`, `$kilo new`, or `$kilo bind`, persist the resolved absolute bound folder in the repo **`.kilo-state`** top-level `workspace` and matching `projects[]` entry (always write `.kilo-state`; do not require deleting a legacy `.run-state`).

## Layout and numbering

```text
<workspace>/Projects/NN-project/
├── project.md
└── NN.MM-workstream/
    ├── workstream.md
    ├── tasks.md
    ├── context.md
    ├── review.md (Acceptance + review rounds; created at first draft)
    └── spec.md (optional)
```

Projects use `NN-slug`; workstreams use `NN.MM-slug`. Allocate the next number under the parent. New homepages must use `project.md` / `workstream.md`. Legacy unnumbered folders remain readable; do not rename without authorization.

## `$kilo init`

Resolve the workspace first. Create only `Projects/<projectId>/project.md`; do not create workstream task files. If the project exists, guide `$kilo new` or `$kilo bind`. Persist the absolute project binding, set `lang`, and stop by default.

## `$kilo new`

Resolve the parent project from an active workstream, project homepage, or explicit user target. Allocate `NN.MM-slug`, create the homepage plus empty `tasks.md` and `context.md`, append the parent workstreams row (notes plus `Worktree` / `Branch` / `State`), and bind the session to the new workstream. Do not pre-create `review.md`; it appears with the first Acceptance draft. Carry the parent `project.md` `## Stable Facts` and `## Gotcha Index` into explore rather than rediscovering them. Do not auto-execute by default. Before allocating a worktree, surface active/smoke-pending sibling worktrees.

For code repos: allocate the primary worktree, write `worktree_path` / `worktree_branch` into Handoff (and the matching `.kilo-state` entry), and set `worktree_status: active`. Record `worktree_status: none` only for pure-docs lines that never touch code. When the creating turn states a pass bar or spec path, seed `review.md` `## Acceptance` as `draft` (`version: 1`) from that turn only (do not mine prior chat). After bind/new completes, run the bidirectional worktree audit (orphan + missing) from [recover.md](recover.md) before recover advance or mutation.

## `$kilo bind`

Match `session_id` → may resume that binding after the bidirectional worktree audit. No session match → always interactive `$kilo bind` / `$kilo new`, even if exactly one active workstream exists; never auto-bind the sole active line. With two or more candidates for an interactive bind, list them and require an explicit choice; never silently rebind. A project homepage is browse-only unless it has ready/doing tasks. After bind completes, the same orphan/missing audit still applies before further advance.

## Language

Resolve `lang` from open Handoff, `.kilo-state`, legacy `.run-state`, `KILO_LANG`, legacy `RUN_LANG`, then `en`. `$kilo lang en|zh` updates the repo default and an open Handoff; historical entries are not bulk-translated. Keep machine literals and parser headings stable.

When writing **user-facing Chinese** (prompts, status explanations, README-style notes, Handoff prose): use everyday words only. **Do not invent shorthand** (关线、先冻后干、状态单写). Call the Markdown files **状态文档**. Prefer `kaola-writing` when polishing Chinese prose.
