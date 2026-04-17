---
feature: shared-utils-refactor
serves: docs/specs/platform-reusability.md
design:
status: done
date: 2026-04-17
---
# Plan: Shared Utilities Refactor (`lib.py`)

Extract duplicated helpers (`parse_frontmatter`, `find_wiki_pages`, `SKIP_DIRS`) from 9 engine scripts into a single `sprue/engine/scripts/lib.py` module. Eliminate the silent `SKIP_DIRS` drift that causes different scripts to see different page sets.

## Success Criteria

```json
{
  "functional": [
    "sprue verify continues to produce identical validator output post-refactor",
    "Every existing pytest test passes without modification",
    "SKIP_DIRS is defined exactly once and all scripts see the same skip set"
  ],
  "observable": [
    "grep -rn 'def parse_frontmatter' src/sprue/engine/scripts/ returns 1 match (lib.py)",
    "grep -rn 'def find_wiki_pages\\|def find_pages' src/sprue/engine/scripts/ returns 1 match",
    "grep -rn 'SKIP_DIRS\\s*=' src/sprue/engine/scripts/ returns 1 match"
  ],
  "pass_fail": [
    "pytest -v passes (no regression)",
    "sprue verify exits 0 on a freshly-initialized instance",
    "Scripts removed from the migration list contain zero local definitions of the extracted helpers"
  ]
}
```

## Tasks

### Phase A — Audit and Design

- [x] T1: Audit exact duplication — see `.yolo-sisyphus/handoff/lib-audit.md`
- [x] T2: Identify canonical signatures — see audit file. Scope-defining findings:
  - **3 `parse_frontmatter` variants**: 2 return tuple `(dict, str)`, 1 returns `dict or None`. Only migrate the 2 tuple-returning variants (build-index.py, verify-content.py).
  - **5 `find_wiki_pages` variants**: 3 return `list[Path]` (content pages), 1 returns `set[str]` (slugs for wikilinks), 1 is manifest-based (verify-content.py). Only migrate the 3 matching variants.
  - **9 `SKIP_DIRS` definitions, 3 variants**: 7 scripts use the full set `{.obsidian, .index, domains, sources}`, 2 scripts omit `sources`. This is the silent drift bug.
  - **3 `relationship_types` normalization sites**: substantially similar, safe to extract.

### Phase B — Extract (conservative scope)

- [ ] T3: Create `src/sprue/engine/scripts/lib.py` exporting: `SKIP_DIRS`, `SKIP_FILES` (union), `parse_frontmatter` (tuple-returning variant), `find_wiki_pages` (list[Path] variant), `normalize_relationship_types` → `src/sprue/engine/scripts/lib.py` (depends: T1, T2)
- [ ] T4: `SKIP_DIRS` union = `{.obsidian, .index, domains, sources}`; `SKIP_FILES` union = `{overview.md, index.md}` → lib.py
- [ ] T5: Add docstrings explaining why some scripts retain local variants (divergent signatures) → lib.py

### Phase C — Migrate (focused)

- [ ] T6: Migrate `SKIP_DIRS`/`SKIP_FILES` in all 9 scripts to `from lib import SKIP_DIRS, SKIP_FILES` — this is the drift fix, highest value → 9 files (depends: T3, T4)
- [ ] T7: Migrate `parse_frontmatter` in build-index.py and verify-content.py only → 2 files (depends: T3)
- [ ] T8: Migrate `find_wiki_pages` in build-index.py, build-embeddings.py, check-tags.py only → 3 files (depends: T3)
- [ ] T9: Migrate `normalize_relationship_types` in build-index.py, check-entity-types.py, check-config.py → 3 files (depends: T3)

### Phase D — Verify

- [ ] T10: Add `tests/test_lib.py` covering each exported function + edge cases → new test file (depends: T3)
- [ ] T11: Regression gate — `pytest -v` and `sprue verify` on fresh instance; `bash src/sprue/engine/verify.sh` in source repo → manual verification (depends: T6–T9)

### Out of Scope (was originally planned, now deferred)

- **check-tags.py `parse_frontmatter`**: returns `None` instead of tuple — call sites assume non-tuple; migrating requires non-trivial refactor; deferred.
- **check-wikilinks.py `find_pages`**: returns `set[str]` of slugs, not paths — fundamentally different function; leave local.
- **verify-content.py `find_pages`**: manifest-based with filter params — different purpose; leave local.
- **check-frontmatter.py, check-fences.py**: use inline `os.walk`, not a named function — SKIP_DIRS migration (T6) catches them; function extraction not warranted.

## Acceptance Criteria

- [ ] AC1: `src/sprue/engine/scripts/lib.py` exists and exports `parse_frontmatter`, `find_wiki_pages`, `SKIP_DIRS`, `SKIP_FILES`, `normalize_relationship_types` — **spec: reusability via shared utilities**
- [ ] AC2: `grep -c "def parse_frontmatter" src/sprue/engine/scripts/*.py` returns `1` (lib.py only) — **single source of truth**
- [ ] AC3: `grep -c "SKIP_DIRS\s*=" src/sprue/engine/scripts/*.py` returns `1` — **no drift**
- [ ] AC4: `pytest -v` — all pre-existing tests still pass, no test modifications needed — **no regression**
- [ ] AC5: `tests/test_lib.py` has coverage for all 5 extracted exports — **new helpers are tested**
- [ ] AC6: `sprue verify` on a fresh instance exits 0 — **CLI integration intact**
- [ ] AC7: `bash src/sprue/engine/verify.sh` exits 0 in the source repo — **source-repo mode intact**

## Testing

Tests live in `tests/test_lib.py`. Use pytest fixtures from `conftest.py`.

- Synthetic wiki pages via `tmp_path` fixture (no real KB needed for lib tests)
- For `relationship_types` normalization: test both list-of-dicts and dict-of-dicts input forms (both exist in the wild per the audit)

## Non-Goals

- **Not refactoring individual scripts' other logic.** Only path-constant replacement + import addition.
- **Not fixing SKIP_DIRS semantics.** Using the union preserves conservative skip behavior; semantic review is a separate concern.
- **Not touching config.py or engine_root.py.** Those are their own resolvers.
- **Not removing the deprecated verify-content.py.** Still referenced by fix-protocol.md per earlier decision.
- **Not bumping package version.** This is an internal refactor with no user-facing API change.

## Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Signature mismatch between existing scripts causes subtle behavior change | Medium — scripts silently produce different output | Medium | T2 explicitly audits each signature and documents the chosen canonical form. Regression gate in T10 catches observable differences. |
| `sys.path` import trick breaks when running scripts via `sprue verify` (subprocess cwd) | Medium — would break CLI | Low | The existing pattern `sys.path.insert(0, str(Path(__file__).resolve().parent))` already works for `config.py`; lib.py follows the same pattern. |
| Migration introduces a bug that tests don't catch | Medium | Low-Medium | Keep commits small (one phase per commit); bisect-friendly |
| SKIP_DIRS union accidentally skips a real directory | Low — only `sources` is the variant; already a valid skip | Very Low | Compare union against each variant; document in lib.py |

## Dependency Graph

```
T1 → T2 → T3 → T4, T5
              ↓
T3 + T9 (tests in parallel with T6–T8)
T3 → T6, T7, T8 → T10
```

Phase A is sequential. Phase B depends on Phase A. Phase C can batch multiple scripts per commit (4+4+1 per plan). Phase D gates merge.
