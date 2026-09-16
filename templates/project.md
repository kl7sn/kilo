---
title: "{{title}}"
type: project
parent: ""
project: "{{project}}"
status: active
blocked: false
summary: ""
repos: []
lang: "{{lang}}"
updated: "{{date}}"
tags:
  - project
---

# {{title}}

Project container for `$run`. Create with `$run init`.

## Workstreams

| Workstream | Notes | Worktree | Branch | State |
| --- | --- | --- | --- | --- |
| | | | | |

> Link example: `[[01.01-hello/workstream]]`
> `State` uses the Handoff enum: `none|active|missing|smoke_pending|ready_to_merge|pruned`

## Repos

| ID | path |
| --- | --- |
| | |

## Stable Facts

<!-- Long-lived, verifiable facts every workstream needs: build/run commands, directory
     conventions, quirks of external systems. One line each. Delete on expiry.
     Not for transient traps — those stay in the workstream context.md. -->

## Gotcha Index

<!-- Pointers, not copies. One line per topic:
     - <topic>: <one-line conclusion> → [[01.03-slug/context]]
     Add an entry only when the trap cannot be mechanized as a test/lint/type rule. -->
