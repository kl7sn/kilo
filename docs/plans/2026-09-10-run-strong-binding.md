# Strong Binding Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `$run` enforce session ↔ workstream ↔ primary worktree 1:1 binding, mandatory new-session bind, strict non-continuation gates, and missing-worktree hard stops.

**Architecture:** Protocol-only updates under `skills/run/` plus templates/README. No new CLI. Worktree for this line: `.worktrees/05.03-strong-binding` on `feat/05.03-strong-binding`. `~/.cursor/skills/run` already symlinks to repo `skills/run` (edit in worktree, sync back via merge/PR).

**Tech Stack:** Markdown protocols, Handoff enums, git worktrees.

**Design:** `docs/plans/2026-09-10-run-strong-binding-design.md`

---

### Task 1: Land protocol rewrite base on the feature branch

**Files:**
- Modify (already copied into worktree): `skills/run/SKILL.md`, `skills/run/protocols/*`, templates, README*
- Worktree: `.worktrees/05.03-strong-binding`

**Step 1: Confirm worktree has the protocol split**

Run:
```bash
cd /Users/duminxiang/cosmos/go/src/github.com/kl7sn/run/.worktrees/05.03-strong-binding
ls skills/run/protocols/
test -f skills/run/SKILL.md && wc -l skills/run/SKILL.md
```

Expected: `auto.md execute.md recover.md reference.md review.md workspace.md` present; SKILL.md is the short progressive-disclosure entry (not the pre-split monolith).

**Step 2: Commit the base if still uncommitted**

```bash
cd /Users/duminxiang/cosmos/go/src/github.com/kl7sn/run/.worktrees/05.03-strong-binding
git add skills/run README.md README_CN.md templates
git commit -m "$(cat <<'EOF'
chore(run): import protocol-split base onto strong-binding branch

EOF
)"
```

Expected: commit succeeds on `feat/05.03-strong-binding`.

**Step 3: Update workstream Handoff worktree fields**

In Obsidian workstream `05.03-strong-binding/context.md` set:
- `worktree_path: /Users/duminxiang/cosmos/go/src/github.com/kl7sn/run/.worktrees/05.03-strong-binding`
- `worktree_branch: feat/05.03-strong-binding`
- `worktree_status: active`
- Mark T01 done after plan file exists (this plan).

---

### Task 2: Critical rules + startup route in SKILL.md

**Files:**
- Modify: `skills/run/SKILL.md`

**Step 1: Add/replace Critical rules for strong binding**

Ensure these rules exist (merge with existing 1–13; renumber if needed):

- One session ↔ one workstream ↔ one primary worktree.
- New session without matching `session_id` → hard stop; require `$run bind` or `$run new`; never auto-bind the sole active line.
- Strict workstream-fit: non-continuation requests set `binding_decision: pending` before adding tasks.
- Bidirectional worktree audit; `missing` is a hard stop (recreate / adopt / close+new).
- Code mutations only in the primary worktree; never fall back to main checkout when `missing`.

**Step 2: Update Startup route**

Insert near the top of startup:

1. Resolve workspace.
2. If no `session_id` match → emit new-session bind prompt and **stop** (before recover advance).
3. After bind, run bidirectional worktree audit before fit check / task mapping.
4. Strict fit before mapping/adding tasks.

**Step 3: Update Status line / Integration prompt section**

Reference the three standard prompts in `reference.md` (new-session, non-continuation, missing). Keep integration-gate prompt as-is.

**Step 4: Commit**

```bash
git add skills/run/SKILL.md
git commit -m "$(cat <<'EOF'
feat(run): enforce session/workstream/worktree strong binding in SKILL

EOF
)"
```

---

### Task 3: recover.md — session gate + bidirectional audit

**Files:**
- Modify: `skills/run/protocols/recover.md`

**Step 1: Rewrite Recover order**

Required order:

1. Read `.run-state`; resolve workspace.
2. **Session bind gate:** no matching `session_id` → prompt bind/new; stop.
3. Sync top-level binding; read homepage / tasks / Handoff.
4. Closed-line check.
5. `git worktree list --porcelain` + compare Handoff + `.run-state` → orphan and **missing**.
6. Dirty/commit inspection.
7. Strict workstream-fit (non-continuation → pending).
8. Map/add task only after binding decision resolved.
9. Mutation preflight + recovery checkpoint.

**Step 2: Expand Orphan section; add Missing section**

Missing definition + three options + field updates:
- `worktree_status: missing`
- `binding_decision: pending`
- `blocker: worktree-missing`
- No mutation until resolved
- Surface stranded-commit hints when useful

**Step 3: New-session prompt pointer**

Point to `reference.md` new-session template.

**Step 4: Commit**

```bash
git add skills/run/protocols/recover.md
git commit -m "$(cat <<'EOF'
feat(run): add session bind gate and missing worktree triage to recover

EOF
)"
```

---

### Task 4: workspace.md — kill sole-active auto-bind; register worktree on new/bind

**Files:**
- Modify: `skills/run/protocols/workspace.md`

**Step 1: Change `$run bind` policy**

Replace “Auto-bind only when the session id matches or there is one unique target” with:

- Match `session_id` → may resume that binding after worktree audit.
- **No session match → always interactive** `$run bind` / `$run new`, even if exactly one active workstream exists.

**Step 2: Change `$run new`**

Require creating/registering the primary worktree (or recording `worktree_status: none` only for pure-docs lines that never touch code). For code repos: allocate worktree, write Handoff path/branch, set `active`.

**Step 3: Commit**

```bash
git add skills/run/protocols/workspace.md
git commit -m "$(cat <<'EOF'
feat(run): require explicit bind on new sessions and register primary worktree

EOF
)"
```

---

### Task 5: execute.md — strict fit + worktree must be active

**Files:**
- Modify: `skills/run/protocols/execute.md`

**Step 1: Before mutation-accounting preflight, add gates**

1. Primary worktree must not be `missing`; if code task and `worktree_status` is `none`, stop to create/register one.
2. Strict fit: non-continuation → do not add task / mutate.

**Step 2: Define continuation check**

Document the strict continuation criteria from the design.

**Step 3: Commit**

```bash
git add skills/run/protocols/execute.md
git commit -m "$(cat <<'EOF'
feat(run): gate execute on strict fit and active primary worktree

EOF
)"
```

---

### Task 6: reference.md — enums + prompt templates + hard blocks

**Files:**
- Modify: `skills/run/protocols/reference.md`

**Step 1: Extend enums**

```text
worktree_status: none | active | missing | smoke_pending | ready_to_merge | pruned
```

Keep `binding_decision` as today; document that `pending` blocks add-task and mutation for fit, missing, and new-session cases.

**Step 2: Add three prompt templates (zh)**

Copy from design section 3:

- New session unbound
- Non-continuation
- Missing worktree

**Step 3: Hard blocks**

Add: new-session unbound, worktree-missing, sole-active silent bind (forbidden), mutation outside primary worktree.

**Step 4: Commit**

```bash
git add skills/run/protocols/reference.md
git commit -m "$(cat <<'EOF'
feat(run): document missing worktree enum and strong-binding prompts

EOF
)"
```

---

### Task 7: Templates + README

**Files:**
- Modify: `templates/context.md`, `templates/context.zh.md`
- Modify: `README.md`, `README_CN.md`

**Step 1: Templates**

Add to Handoff example:
- `binding_decision: continue-current`
- Comment or example value showing `worktree_status` may be `missing`

**Step 2: README / README_CN**

Add a short subsection under workflow/critical behavior:

- One session, one workstream, one primary worktree
- New sessions must bind
- Missing worktree hard-stop

**Step 3: Commit**

```bash
git add templates/context.md templates/context.zh.md README.md README_CN.md
git commit -m "$(cat <<'EOF'
docs(run): document strong binding in templates and README

EOF
)"
```

---

### Task 8: Acceptance self-check

**Files:**
- Verify only (no code required)

**Step 1: Grep invariants**

```bash
cd /Users/duminxiang/cosmos/go/src/github.com/kl7sn/run/.worktrees/05.03-strong-binding
rg -n "missing|session_id|binding_decision|sole active|strict" skills/run README.md README_CN.md templates/context.md templates/context.zh.md
```

Expected: hits in SKILL, recover, workspace, execute, reference, READMEs, templates.

**Step 2: Negative check — sole-active auto-bind removed**

```bash
rg -n "one unique target|sole active|Auto-bind only when" skills/run/protocols/workspace.md
```

Expected: old auto-bind-on-unique-target wording gone or explicitly forbidden.

**Step 3: Update workstream tasks/Handoff**

Mark T02–T03 done with evidence lines; leave integration gate for human smoke (T04).

**Step 4: Final commit if any fixups**

```bash
git status -sb
# commit fixups if needed
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-09-10-run-strong-binding.md`.

**Two execution options:**

1. **Subagent-Driven (this session)** — fresh subagent per task, review between tasks
2. **Parallel Session (separate)** — open a new session in `.worktrees/05.03-strong-binding` with executing-plans

Which approach?
