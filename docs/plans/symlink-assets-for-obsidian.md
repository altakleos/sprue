---
feature: symlink-assets-for-obsidian
serves: docs/specs/visual-knowledge.md
design: docs/decisions/0047-asset-symlink-for-obsidian.md
status: done
date: 2026-04-19
---
# Plan: Symlink Assets for Obsidian

## Context

Obsidian refuses to render images outside its vault. The vault is `wiki/`,
images live at `raw/assets/`. Symlink `wiki/assets → ../raw/assets` makes
them visible inside the vault without duplication. See ADR-0047.

## Tasks

- [x] T1: Create `wiki/assets` symlink at `sprue init`
- [x] T2: Create `wiki/assets` symlink at `sprue upgrade` (existing KBs)
- [x] T3: Updated `fix-image-paths.py`: depth-aware rewrite to `../` × (depth) + `assets/<file>` form; handles `raw/assets/`, `../raw/assets/`, `../../raw/assets/`, and deeper legacy prefixes
- [x] T4: Updated `check-images.py`: flags `parent_escape_legacy` as a distinct issue (even when the file exists) since Obsidian rejects paths outside its vault
- [x] T5: Updated `wiki_page.md` and `compile-attributed.md` prompts to the new canonical form
- [x] T6: Updated `compile.md` Step 11 note to reference the broader fixer scope
- [x] T7: 10 unit tests for the rewriter (depth 1/2/3, idempotency, remote URLs, non-asset paths, canonical form untouched, mixed pages, non-wiki skip)
- [x] T8: E2E verified: scratch KB with depth-1 and depth-2 pages both rewrite correctly and resolve through the symlink to the same immutable file. cats-kb ragamuffin page fixed in place.

## Acceptance Criteria

- [x] AC1: `sprue init new-kb` produces `new-kb/wiki/assets → ../raw/assets`
- [x] AC2: `sprue upgrade` on an existing KB without the symlink creates it (reports "Created wiki/assets → ../raw/assets symlink (for Obsidian)")
- [x] AC3: `fix-image-paths.py` on any legacy form rewrites to the canonical form
- [x] AC4: `check-images.py` flags `../raw/assets/` as wrong; accepts `assets/foo.jpg` when it resolves through the symlink
- [x] AC5: `sprue verify --file` auto-fixes and passes on a page using any legacy form
- [x] AC6: 46/46 tests pass (10 for the rewriter)
