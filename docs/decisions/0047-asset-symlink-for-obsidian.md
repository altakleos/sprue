---
status: accepted
date: 2026-04-19
---
# ADR-0047: Asset Visibility via `wiki/assets` Symlink

## Context

Raw source assets (images captured during import) live at `raw/assets/` —
immutable, outside the Obsidian vault which is rooted at `wiki/`. Obsidian
refuses to render paths that resolve outside its vault root, so references
like `../raw/assets/foo.jpg` produce "file could not be found" even though
the file exists on disk.

The only way to make `raw/assets/` visible from inside the vault without
duplicating files or violating `raw/` immutability is a symlink from
`wiki/assets` → `../raw/assets`.

Empirical check: on macOS with current Obsidian, the symlink works out of
the box with no user configuration. Wiki pages that reference
`![](assets/foo.jpg)` render correctly in Obsidian, GitHub web, and VS Code
preview.

## Decision

Create a symlink `wiki/assets` → `../raw/assets` at KB scaffold time and
rewrite wiki page image references to route through the vault-root symlink.
No file duplication. `raw/` stays immutable.

Canonical path form is **page-relative to the vault root**:
- `wiki/<slug>.md` → `![](assets/foo.jpg)`
- `wiki/<dir>/<slug>.md` → `![](../assets/foo.jpg)`
- `wiki/<dir1>/<dir2>/<slug>.md` → `![](../../assets/foo.jpg)`

These all resolve to `wiki/assets/foo.jpg` (inside the vault), which the
symlink in turn resolves to `raw/assets/foo.jpg` outside. The mechanical
fixer (`fix-image-paths.py`) computes the page's depth and prepends the
correct prefix automatically; agents do not need to know the rule.

## Alternatives Considered

- **Copy-on-compile** — Copy each referenced asset from `raw/assets/` to
  `wiki/.assets/`. Rejected: duplication of large binaries on every
  compile; must be kept in sync; bloats the git history if tracked.
- **Move Obsidian vault to KB root** — User opens Obsidian at the KB root
  instead of `wiki/`. Rejected: exposes `raw/`, `memory/`, `inbox/`,
  `state/` to Obsidian's sidebar; clutters the user experience; breaks
  existing KBs whose vault is rooted at `wiki/`.
- **Obsidian wikilinks `![[raw/assets/foo.jpg]]`** — Vault-root resolution.
  Rejected previously in the working-group review: still outside the
  vault, breaks GitHub/VS Code portability.

## Consequences

- `wiki/assets` is a special symlink, not a regular directory. Must be
  preserved across `init`, `upgrade`, and manual KB reorganization.
- Page image refs are now page-local: `![](assets/foo.jpg)`. This is
  depth-invariant — pages at any nesting level under `wiki/` reference
  the same path form.
- The mechanical fixer (`fix-image-paths.py`, introduced in v0.1.30a1)
  rewrites to the new form; prior outputs (`../raw/assets/...`) are
  auto-migrated.
- git stores symlinks as symbolic-link objects, not file content — no
  duplication in history.
- Windows users may need developer mode or admin rights to CREATE the
  symlink (one-time, at `sprue init`); READING the symlink (everyone
  using the KB) works universally.

## Config Impact

No new config keys. The symlink location is a platform invariant, not a
tunable.
