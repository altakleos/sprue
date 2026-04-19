---
feature: Visual Knowledge
serves:
  - docs/specs/visual-knowledge.md
design:
  - docs/design/visual-knowledge-model.md
decisions:
  - docs/decisions/0044-image-capture-pipeline.md
  - docs/decisions/0045-image-annotations-schema.md
  - docs/decisions/0046-multimodal-capability-flag.md
status: in-progress
date: 2026-04-19
---
# Plan: Visual Knowledge

Implement image capture, classification, and citation across the Sprue engine so that images from source material become first-class knowledge sources — captured at import, understood at compile, and cited with the same provenance model as text.

## Success Criteria

```json
{
  "functional": [
    "import protocol downloads images to raw/assets/ and records assets in imports.yaml",
    "compile protocol classifies images and extracts claims via cite-then-claim",
    "image-derived claims carry source_media and extraction_confidence in the verification ledger"
  ],
  "observable": [
    "compiled wiki pages include contextually placed images with [^src-N] provenance markers",
    "text-only mode produces usable classifications from alt text, filename, and surrounding prose"
  ],
  "pass_fail": [
    "check-images.py validates image references (file exists, alt text present), exit 0/1",
    "image-annotations.yaml is generated during compile with per-image classification and claims",
    "query-provenance.py returns source_media and extraction_confidence for image-sourced claims"
  ]
}
```

## Tasks

### Phase 0 — Spec, Design, Decisions (DONE)

- [x] T0.1: Write Visual Knowledge spec → `docs/specs/visual-knowledge.md` ✔
- [x] T0.2: Write Visual Knowledge Model design doc → `docs/design/visual-knowledge-model.md` ✔
- [x] T0.3: Write ADR-0044 (capture pipeline) → `docs/decisions/0044-image-capture-pipeline.md` ✔
- [x] T0.4: Write ADR-0045 (annotations schema) → `docs/decisions/0045-image-annotations-schema.md` ✔
- [x] T0.5: Write ADR-0046 (multimodal capability flag) → `docs/decisions/0046-multimodal-capability-flag.md` ✔

### Phase 1 — Config & Scaffold (DONE)

- [x] T1.1: Add `config.images.*` section to defaults.yaml → `src/sprue/engine/defaults.yaml` ✔
  - Keys: `enabled`, `multimodal_available`, `capture.*`, `classify.*`, `compile.*`
- [x] T1.2: Add `raw/assets/` to sprue init scaffold → `src/sprue/cli/init.py` ✔
  - Add to `_INSTANCE_DIRS`

### Phase 2 — Import Pipeline (DONE)

- [x] T2.1: Create image extraction helper → `src/sprue/engine/scripts/extract-images.py` ✔
  - Scan raw markdown for `![alt](url)` patterns
  - Apply filtering heuristics (SVG size, dimensions, tracking domains)
  - Return candidate image list
- [x] T2.2: Create image download helper → `src/sprue/engine/scripts/download-image.py` ✔
  - HTTP fetch with timeout, content-type validation, size limit, one retry
  - Return local path and metadata (size, hash, dimensions)
  - Exit 0 on success, 1 on skip (warning to stderr)
- [x] T2.3: Update import protocol with image capture sub-step → `src/sprue/engine/protocols/import.md` ✔
  - After fetch, scan for images via extract-images.py
  - For each, invoke download-image.py
  - Rewrite raw markdown URLs to local paths; preserve original URL in HTML comment
  - Append `assets` list to imports.yaml entry
- [ ] T2.4: Write test raw source for e2e → tested in Phase 5 (T5.1)

### Phase 3 — Compile Pipeline (DONE)

- [x] T3.1: Create image annotation prompt template → `src/sprue/engine/prompts/classify-image.md` ✔
  - Guide LLM through classification (8 categories) and description
  - Both multimodal and text-only tracks
- [x] T3.2: Update compile protocol with Step 4a (image triage) → `src/sprue/engine/protocols/compile.md` ✔
  - Read imports.yaml for raw source's assets
  - Invoke classify-image prompt per image
  - Persist annotations to `instance/state/image-annotations.yaml` keyed by content_hash
  - Skip if annotation for content_hash already exists (dedup on re-compile)
- [x] T3.3: Update cite-then-claim for image sources → `src/sprue/engine/prompts/compile-attributed.md` ✔
  - Image annotations become citable excerpts
  - Claims get `source_media` and `extraction_confidence` in ledger entries
- [x] T3.4: Update page type placement rules → `src/sprue/engine/prompts/wiki_page.md` ✔
  - Entity pages: subject-photo after TL;DR as hero image
  - Inline placement for diagrams/charts near supporting claims
  - Density guardrails (max per page, min words per image)

### Phase 4 — Validators & Provenance

- [ ] T4.1: Create check-images.py validator → `src/sprue/engine/scripts/check-images.py`
  - Validate image references: file exists in `raw/assets/`, alt text present
  - Follow check-sources.py pattern; `--quiet` and `--json` flags, exit 0/1
- [ ] T4.2: Register check-images in rules.yaml template → `src/sprue/templates/memory/rules.yaml`
- [ ] T4.3: Extend verify protocol for image fields → `src/sprue/engine/protocols/verify.md`
  - Recognize `source_media` and `extraction_confidence`
  - Apply confidence-gated corroboration (low requires Tier 2/3, blocks promotion)
- [ ] T4.4: Extend query-provenance.py and build-index.py — no code changes needed
  - Fields appear automatically via ledger schema

### Phase 5 — E2E Test & Documentation

- [ ] T5.1: End-to-end test with temporary KB instance
  - `sprue init` test KB, import article with images
  - Verify `raw/assets/` populated and imports.yaml has `assets` field
  - Compile page, verify image-annotations.yaml and wiki page includes images
  - Query provenance for an image-derived claim
- [ ] T5.2: Update AGENTS.md repo map counts → `AGENTS.md`

## Non-Goals

- Video, audio, or interactive media
- Image editing, resizing, format conversion
- AI image generation
- PDF image extraction
- OCR for scanned documents
- Image search or reverse image lookup
- Image health drift detection (liveness only in v1; perceptual hashing deferred)
- Retroactive backfill of existing wiki pages

## Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Image downloads bloat `raw/assets/` | Medium | High | Config limits (`max_bytes`, `max_per_source`); filter heuristics skip decorative content |
| Multimodal LLM hallucinates image content | High | Medium | `extraction_confidence` field; low-confidence claims block promotion per ADR-0042 pattern |
| Text-only degradation produces poor annotations | Medium | High | Alt text + filename + surrounding prose sufficient for ~80% of images; `unknown` classification for the rest |
| Raw immutability tension with URL rewriting | Medium | Low | ADR-0044 explicitly resolves this; rewriting is part of capture, not post-capture modification |

## Dependency Graph

```
Phase 0 → Phase 1 → Phase 2 (import) → Phase 3 (compile) → Phase 4 (validators)
                                                           → Phase 5 (e2e)
```
