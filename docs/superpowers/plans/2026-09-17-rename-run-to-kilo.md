# Rename run → kilo Implementation Plan

> **For agentic workers:** Prefer **inline execution** for this plan (mechanical mass rename across one repo; subagent split risks inconsistent mid-states). Use `superpowers:executing-plans` / direct implementation. Checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebrand product/skill/repo surfaces from `run` to `kilo` per `docs/superpowers/specs/2026-09-17-rename-run-to-kilo-design.md`.

**Architecture:** Pure rename of skill package + docs + install entrypoints. Protocol behavior unchanged. Add a one-release read-compat layer: prefer `.kilo-state` / `KILO_*`, fall back to `.run-state` / `RUN_*` on read; write only `.kilo-state` / `KILO_*`.

**Tech Stack:** Markdown skill package, bash `install.sh`, GitHub repo rename via `gh`, SVG mark assets.

---

## File map

| Path | Action |
| --- | --- |
| `skills/run/` → `skills/kilo/` | `git mv`; rewrite `$run`/`.run-state`/`RUN_*` |
| `install.sh` | Install skill `kilo` |
| `README.md`, `README_CN.md` | Brand, URLs, diagrams, migration blurb |
| `docs/design.md` | Current product name |
| `docs/images/run-mark.svg` → `kilo-mark.svg` | New **K** mark |
| `docs/images/run-readme-*.{svg,png}` → `kilo-readme-*` | Rename + caption fixes in SVG |
| `templates/*.md`, `examples/**` | Product-name strings only |
| `docs/plans/*run*` | Leave filenames; add one-line “product now kilo” at top if they teach current behavior |
| `.gitignore` | Ignore `.kilo-state` |
| `.shimocli-tmp/` | **Out of scope** (local junk) |

### Canonical string map (apply in order)

1. `kl7sn/run` → `kl7sn/kilo`
2. `skills/run` → `skills/kilo`
3. `.run-state` → `.kilo-state` (then add compat sentences where resolution is defined)
4. `RUN_WORKSPACE` → `KILO_WORKSPACE`
5. `RUN_LANG` → `KILO_LANG`
6. `$run` → `$kilo`
7. `/run` → `/kilo` (after URL/path replacements so `github.com/kl7sn/kilo` is already correct)
8. Skill frontmatter `name: run` → `name: kilo`
9. Image basenames `run-` → `kilo-`
10. Status examples `[/run ·` → `[/kilo ·` / `[$run ·` → `[$kilo ·`

Do **not** replace the English verb “run” inside unrelated sentences (e.g. “run verification”) unless it is clearly the product name. Prefer targeted `$run`/`/run`/path replacements over blind `\brun\b`.

---

### Task 1: Move skill directory

**Files:**
- Move: `skills/run/` → `skills/kilo/`

- [ ] **Step 1: git mv**

```bash
git mv skills/run skills/kilo
```

Expected: `skills/kilo/SKILL.md` and `skills/kilo/protocols/*.md` exist; `skills/run` gone.

- [ ] **Step 2: Commit**

```bash
git commit -m "refactor(kilo): move skills/run to skills/kilo"
```

---

### Task 2: Rewrite skill protocol text + compat

**Files:**
- Modify: `skills/kilo/SKILL.md`
- Modify: `skills/kilo/protocols/workspace.md`
- Modify: `skills/kilo/protocols/recover.md`
- Modify: `skills/kilo/protocols/execute.md`
- Modify: `skills/kilo/protocols/auto.md`
- Modify: `skills/kilo/protocols/reference.md`

- [ ] **Step 1: Apply canonical string map** to all files under `skills/kilo/`.

- [ ] **Step 2: Frontmatter** in `SKILL.md`:

```yaml
---
name: kilo
description: "Use when a coding task needs a durable project/workstream binding, explicit phase routing, task accounting, recovery, verification gates, or unattended execution through the $kilo protocol."
---
```

Title: `# $kilo — durable engineering workflow`

Codex section: always show `$kilo` / `$kilo <subcommand>`; do not expose legacy `/run` or `$run` as commands.

- [ ] **Step 3: Resolution compat** in `SKILL.md` critical rule + `protocols/workspace.md`:

Replace fail-closed rule with:

1. Repo `.kilo-state` `workspace:` (highest).
2. Else legacy repo `.run-state` `workspace:` (read-only compat).
3. Non-empty `KILO_WORKSPACE`, else legacy `RUN_WORKSPACE`.
4. Otherwise hard-stop. Never silently use `~/run-workspace`.

On any successful session write after bind/init/new/lang: persist **`.kilo-state`** (do not require deleting `.run-state`).

Language resolve: Handoff → `.kilo-state` → legacy `.run-state` → `KILO_LANG` → `RUN_LANG` → `en`.

- [ ] **Step 4: Grep gate**

```bash
rg -n '\$run|/run|\.run-state|RUN_WORKSPACE|RUN_LANG|skills/run|name: run|kl7sn/run' skills/kilo
```

Expected: only intentional legacy-compat mentions of `.run-state` / `RUN_*` (and maybe `~/run-workspace` as forbidden path). No `$run` or `/run` command forms.

- [ ] **Step 5: Commit**

```bash
git commit -m "refactor(kilo): rebrand skill protocol to \$kilo and .kilo-state"
```

---

### Task 3: install.sh + gitignore

**Files:**
- Modify: `install.sh`
- Modify: `.gitignore`

- [ ] **Step 1: install.sh** — symlink `kilo`:

```bash
# Contributor helper: symlink skills/kilo into agent dirs.
# End users should prefer: npx skills add kl7sn/kilo -g
...
  install_skill kilo "$base/kilo"
...
    echo "Installs skills/kilo as a symlink into the agent skills directory."
```

- [ ] **Step 2: .gitignore** — add:

```
.kilo-state
.run-state
```

- [ ] **Step 3: Commit**

```bash
git commit -m "chore(kilo): install skill name kilo; ignore state files"
```

---

### Task 4: Templates + examples + design notes

**Files:**
- Modify: `templates/context.md`, `templates/context.zh.md`, `templates/project.md`, `templates/project.zh.md`, `templates/workstream.md`, `templates/workstream.zh.md` (and any other template hits)
- Modify: `examples/01-demo/**` product-name strings
- Modify: `docs/design.md`
- Modify: `docs/plans/2026-09-10-run-strong-binding.md`, `docs/plans/2026-09-10-run-strong-binding-design.md` — prepend note only

- [ ] **Step 1: Apply map** to templates/examples/design (product surfaces only).

- [ ] **Step 2: Prepend to each historical plan file:**

```markdown
> **Note:** Product renamed to `kilo` (2026-09-17). This plan’s filenames keep `run` for history.
```

- [ ] **Step 3: Commit**

```bash
git commit -m "docs(kilo): update templates, examples, and design notes"
```

---

### Task 5: Brand mark + diagram assets

**Files:**
- Create: `docs/images/kilo-mark.svg`
- Delete/rename: `docs/images/run-mark.svg`
- Rename: `run-readme-main-flow.svg|png`, `run-readme-two-places.png` → `kilo-readme-*`
- Modify SVG title/aria text from `run` → `kilo` where present

- [ ] **Step 1: Ship mark** — black `#111` squircle `rx=28`, white geometric **K** (filled path or SF semibold export), `aria-label="kilo"`.

- [ ] **Step 2: Rename diagram assets** with `git mv`.

- [ ] **Step 3: Commit**

```bash
git commit -m "docs(kilo): add K mark and rename diagram assets"
```

---

### Task 6: README EN/CN

**Files:**
- Modify: `README.md`, `README_CN.md`

- [ ] **Step 1: Full brand pass** — hero `kilo`, install `kl7sn/kilo`, commands `/kilo`, state `.kilo-state`, env `KILO_*`, image paths `docs/images/kilo-*`.

- [ ] **Step 2: Migration blurb** (both languages), short:

English sketch:

```markdown
## Migration from run

Formerly published as `run` (`kl7sn/run`). Session file is now `.kilo-state` (`.run-state` still read). Env: `KILO_WORKSPACE` / `KILO_LANG` (legacy `RUN_*` still read). Reinstall: `npx skills add kl7sn/kilo -g`.
```

- [ ] **Step 3: Grep gate** on READMEs — no `kl7sn/run`, `skills/run`, `$run`, `/run` except inside migration “formerly” sentence if needed.

- [ ] **Step 4: Commit**

```bash
git commit -m "docs(kilo): rebrand bilingual README and migration notes"
```

---

### Task 7: Repo-wide verification

- [ ] **Step 1: Final grep** (exclude `docs/superpowers/specs`, `docs/plans`, `.shimocli-tmp`, `.git`):

```bash
rg -n 'kl7sn/run|skills/run|\$run|(?<![a-zA-Z])/run(?![a-zA-Z-])|\.run-state|RUN_WORKSPACE|RUN_LANG|run-mark|name: run' \
  --glob '!.shimocli-tmp/**' --glob '!.git/**' .
```

Triage remaining hits: allowed = migration notes, compat read paths, historical plan note, this plan/spec.

- [ ] **Step 2: Smoke install locally**

```bash
./install.sh agents
ls -la ~/.agents/skills/kilo
```

Expected: symlink to repo `skills/kilo`.

- [ ] **Step 3: Commit any leftover fixes** if grep found stragglers.

---

### Task 8: Push + GitHub rename + release note touch

- [ ] **Step 1: Push `main`**

```bash
git push origin main
```

- [ ] **Step 2: Rename GitHub repo**

```bash
gh repo rename kilo --yes
```

Expected: canonical `https://github.com/kl7sn/kilo`. Old `kl7sn/run` redirects.

- [ ] **Step 3: Update remote if needed**

```bash
git remote -v
# if still .../run.git, set-url to .../kilo.git
git remote set-url origin git@github.com:kl7sn/kilo.git
```

- [ ] **Step 4: Optional — edit latest release or draft next notes** mentioning rename (user may publish `v0.3.0` later).

---

## Spec coverage check

| Spec item | Task |
| --- | --- |
| Name/commands `$kilo`/`/kilo` | 2, 6 |
| Repo `kl7sn/kilo` | 6, 8 |
| `.kilo-state` + read `.run-state` | 2, 3, 6 |
| `KILO_*` + read `RUN_*` | 2, 6 |
| No permanent `/run` alias | 2 |
| Obsidian schemas unchanged | (no task — leave templates structure) |
| K mark | 5 |
| README migration | 6 |
| install.sh | 3 |
| Historical plans keep filenames | 4 |
