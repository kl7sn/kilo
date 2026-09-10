# $run workspace and binding protocol

## Resolution

Resolve before any write:

1. Repo `.run-state` `workspace:` (highest priority).
2. Non-empty `RUN_WORKSPACE`.
3. Otherwise hard-stop with explicit setup instructions.

The root is a normal Markdown folder. Never silently create or select `~/run-workspace`; it is valid only when explicitly configured. Keep paths with spaces exact and absolute when persisting.

After `$run init`, `$run new`, or `$run bind`, persist the resolved absolute bound folder in the repo `.run-state` top-level `workspace` and matching `projects[]` entry.

## Layout and numbering

```text
<workspace>/Projects/NN-project/
├── project.md
└── NN.MM-workstream/
    ├── workstream.md
    ├── tasks.md
    ├── context.md
    └── spec.md (optional)
```

Projects use `NN-slug`; workstreams use `NN.MM-slug`. Allocate the next number under the parent. New homepages must use `project.md` / `workstream.md`. Legacy unnumbered folders remain readable; do not rename without authorization.

## `$run init`

Resolve the workspace first. Create only `Projects/<projectId>/project.md`; do not create workstream task files. If the project exists, guide `$run new` or `$run bind`. Persist the absolute project binding, set `lang`, and stop by default.

## `$run new`

Resolve the parent project from an active workstream, project homepage, or explicit user target. Allocate `NN.MM-slug`, create the homepage plus empty `tasks.md` and `context.md`, append the parent workstreams link, and bind the session to the new workstream. Do not auto-execute by default. Before allocating a worktree, surface active/smoke-pending sibling worktrees.

## `$run bind`

Auto-bind only when the session id matches or there is one unique target. With two or more candidates, list them and require an interactive choice; never silently rebind. A project homepage is browse-only unless it has ready/doing tasks.

## Language

Resolve `lang` from open Handoff, `.run-state`, `RUN_LANG`, then `en`. `$run lang en|zh` updates the repo default and an open Handoff; historical entries are not bulk-translated. Keep machine literals and parser headings stable.
