---
feature: mechanical-path-fixer
serves: docs/specs/visual-knowledge.md
design: (see decision below; no new design doc — straightforward implementation)
status: done
date: 2026-04-19
---
# Plan: Mechanical Image Path Fixer

## Context

After 7+ shipped versions of prompts, validators, and protocol hardening, LLM
agents still emit KB-root-relative image paths (`raw/assets/foo.jpg`) that
break in Obsidian. Every "make the instructions clearer" fix has failed
because the correction loop requires the LLM to read, understand, and obey —
which after 7 iterations is proven unreliable.

Solution: remove the LLM from the correction loop entirely. A Python helper
rewrites KB-root-relative paths to page-relative paths mechanically. Invoked
(a) by compile Step 10.5 right after write, and (b) as a pre-flight hook
inside `verify.py` when called in `--file` mode on a wiki page. Both
triggers are idempotent.

## Tasks

- [x] T1: Add `fix-image-paths.py` helper → `src/sprue/engine/scripts/fix-image-paths.py`
- [x] T2: Wire pre-flight hook in `verify.py` (depends: T1)
- [x] T3: Document auto-normalization on Step 11 in `compile.md` (depends: T1)
- [x] T4: Unit test for the rewriter → `tests/test_fix_image_paths.py` (8 tests)
- [x] T5: E2E test — full `sprue verify --file` flow (tested against scratch KB + real cats-kb ragamuffin page, 5 paths fixed silently)
- [x] T6: (omitted — README count unchanged since this plan joins existing plans)

## Acceptance Criteria

- [x] AC1: `fix-image-paths.py --help` works; rewrites a seed page correctly
- [x] AC2: `sprue verify --file wiki/page.md` on a KB-root-relative page auto-rewrites, then passes
- [x] AC3: Running the fixer twice on the same page produces the same result (idempotent)
- [x] AC4: All existing tests still pass (45/45 passing, 8 new)
- [x] AC5: `sprue verify` doesn't regress on platform repo

## Non-goals

- This plan does NOT introduce a write-gate or filesystem interceptor. The
  LLM continues to write directly to disk. Only the rewrite is machine-owned.
- This plan does NOT address fabricated image refs, wrong filenames, or
  other classes of image bugs. Those remain covered by `check-images.py` and
  `check-triage-done.py` as safety nets.
- This plan does NOT migrate to wikilinks, move assets, or change the
  markdown image syntax. Obsidian/GitHub/VS Code portability is preserved.
