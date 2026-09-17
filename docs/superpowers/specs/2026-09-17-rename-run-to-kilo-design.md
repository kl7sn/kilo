# Design: Rename `run` → `kilo`

Date: 2026-09-17  
Status: approved-for-spec (pending human review of this file)

## Goal

Rebrand the product from `run` to **`kilo`**: short, easy to pronounce (like Orca), precision-tool vibe, clean break from `run` / `r` / slash-as-mark.

## Decisions (locked)

| Item | Choice |
| --- | --- |
| Product / skill display name | `kilo` |
| User commands | `/kilo` … (Cursor / Claude); `$kilo` … (Codex prompts) |
| GitHub repository | Rename `kl7sn/run` → **`kl7sn/kilo`** |
| Session index file | **`.kilo-state`** (replace `.run-state`) |
| Env vars | **`KILO_WORKSPACE`**, **`KILO_LANG`** (replace `RUN_*`) |
| Default vault fallback path | Do **not** reintroduce silent `~/run-workspace`; if any docs mention it historically, say it was never the default after fail-closed resolution |
| Obsidian Markdown schemas | **Unchanged** (`project.md`, `tasks.md`, `context.md`, `review.md`, headings, machine literals) |
| Historical Git tags / releases | Keep `v0.1.0` / `v0.2.0` on old history; new narrative starts at next release as `kilo` (README one-liner: formerly `run`) |

## Compatibility (one transition window)

Required so in-flight workspaces do not break on upgrade:

1. **Read path:** If `.kilo-state` is missing and `.run-state` exists at the git root, treat `.run-state` as the session index (same YAML schema). Prefer writing back to **`.kilo-state`** on the next successful state write; optionally remove or leave `.run-state` (prefer: write `.kilo-state`, leave a one-line note in docs that old file can be deleted after verify).
2. **Env path:** Resolve workspace/lang as: `.kilo-state` fields → `KILO_*` → legacy `RUN_*` → fail closed (same as today, no silent home default).
3. **Commands:** Do **not** keep `/run` or `$run` as permanent aliases after the rename ships. Migration note in README/release only. (Rationale: clean break was an explicit naming goal.)
4. **skills.sh / local installs:** Document uninstall/re-add: `npx skills add kl7sn/kilo -g` after repo rename; old `kl7sn/run` package path stops being the install source once the GitHub rename completes.

## Surface area to change

### In-repo (code + docs)

- Move `skills/run/` → `skills/kilo/` (including `protocols/`).
- Rewrite all user-facing protocol text: status line, command tables, examples, templates that mention `$run` / `/run` / `.run-state` / `RUN_*`.
- `install.sh`: install skill name `kilo`; symlink targets under agent skill dirs.
- `README.md` / `README_CN.md`: hero name, badges, install URLs, diagrams captions.
- `docs/design.md`: product name; leave historical plan filenames under `docs/plans/*run*` as-is (add a one-line pointer that the product is now `kilo`), or rename only if cheap—**prefer leave plan filenames**, update prose inside only where it teaches current behavior.
- Images:
  - Replace mark: black squircle + white **K** lettermark (not slash; slash was `/run` residue).
  - Rename assets from `run-*` → `kilo-*` and fix README references.
- Examples under `examples/`: status/prose that cites the product name; do not rewrite unrelated demo content.
- `.gitignore`: ignore `.kilo-state` if we ever start committing local state by mistake; do **not** commit local `.run-state` / `.kilo-state`.

### GitHub / distribution

- Rename repository via GitHub: `kl7sn/run` → `kl7sn/kilo` (GitHub redirect from old URL should remain; still update all docs to the new URL).
- Update release notes / next tag to say product is `kilo`.
- skills.sh listing follows the GitHub repo path after rename.

### Out of repo (operator checklist, not automated in this repo)

- Local skill softlinks under `~/.agents|cursor|codex|claude/skills` pointing at `run` must be reinstall/relinked to `kilo`.
- Any Obsidian notes or personal docs that say `/run` are user-owned; not migrated by this change.

## Non-goals

- No protocol behavior change in this rename (gates, binding, Acceptance, review.md layout stay as in v0.2.0).
- No new features.
- No rewrite of closed historical workstreams’ prose inside vaults.
- No permanent dual brand (`run` + `kilo`) in the skill text after ship.

## Mark / brand

- Display: lowercase **`kilo`** in README hero (same Orca-style centered layout).
- Icon: B&W rounded square, white **K** (system-semibold or custom geometric), optically centered—same craft bar as the slash mark iteration, not orange, not play-button.
- Avoid inventing Chinese slogans; CN docs keep **状态文档** wording rules (`kaola-writing`).

## Success criteria

1. Fresh clone: `npx skills add kl7sn/kilo -g` installs skill `kilo`; agents invoke `/kilo` / `$kilo`.
2. Bound repo with only legacy `.run-state` still recovers; next write creates `.kilo-state`.
3. No remaining user-facing `/run`, `$run`, `.run-state` (except migration notes), `RUN_WORKSPACE`, or `skills/run` paths in current docs/skill entry.
4. GitHub canonical URL is `https://github.com/kl7sn/kilo`.

## Rollout order

1. Land rename commit(s) on `main` while repo is still `kl7sn/run` **or** immediately after rename—either works if install URLs are updated in the same change set as the GitHub rename.
2. Rename GitHub repository to `kl7sn/kilo`.
3. Verify `npx skills add kl7sn/kilo -g` and README links.
4. Publish next release notes under product name `kilo` (changelog: rename + compatibility).

## Open questions

None locked as blocking. Optional later: whether to delete `.run-state` automatically after successful `.kilo-state` write (default **no**—leave file; document manual delete).
