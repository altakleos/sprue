---
feature: Per-Claim Source Provenance
serves:
  - docs/specs/source-authority-pipeline.md
  - docs/specs/source-grounded-knowledge.md
  - docs/specs/continuous-quality.md
design:
  - docs/design/source-authority-model.md
  - docs/design/confidence-state-machine.md
decisions:
  - docs/decisions/0040-cite-then-claim-compilation.md
  - docs/decisions/0041-per-claim-ledger-schema.md
  - docs/decisions/0042-source-health-priority-boost.md
status: in-progress
date: 2026-04-18
---
# Plan: Per-Claim Source Provenance

Implement per-claim source attribution across the Sprue engine, enabling every verifiable claim in a wiki page to trace to a specific source excerpt. Phases 0–1 are complete (specs, design, ADRs, config, protocol extensions). Phases 2–5 cover query infrastructure, validators, health monitoring, and integration.

## Success Criteria

```json
{
  "functional": [
    "verify protocol produces per-claim ledger entries with source_tier, source_url, excerpt, and claim_text fields",
    "compile protocol generates attributed pages via cite-then-claim constrained generation",
    "provenance chain is queryable in both directions: claim→source and source→claims"
  ],
  "observable": [
    "newly compiled sourced pages have >80% claim attribution coverage",
    "inline [^src-N] markers appear in verified pages linking claims to ledger entries"
  ],
  "pass_fail": [
    "check-claims-coverage.py passes (advisory or enforced per config)",
    "query-provenance.py returns results for any [^src-N]-marked claim",
    "by-source-url.yaml index is generated during index rebuild"
  ]
}
```

## Tasks

### Phase 0 — Specs & Design (DONE)

- [x] T0.1: Restructure source-authority-pipeline spec (6→3 guarantees) → `docs/specs/source-authority-pipeline.md` ✔
- [x] T0.2: Absorb implemented invariants into parent spec → `docs/specs/source-grounded-knowledge.md` ✔
- [x] T0.3: Relocate health monitoring to continuous-quality → `docs/specs/continuous-quality.md` ✔
- [x] T0.4: Fix circular draft dependency → `docs/specs/verified-knowledge-service.md` ✔
- [x] T0.5: Extend source-authority-model design doc (+3 sections) → `docs/design/source-authority-model.md` ✔
- [x] T0.6: Extend confidence-state-machine design doc (+health monitoring) → `docs/design/confidence-state-machine.md` ✔
- [x] T0.7: Write ADR-0040 (cite-then-claim) → `docs/decisions/0040-cite-then-claim-compilation.md` ✔
- [x] T0.8: Write ADR-0041 (per-claim ledger schema) → `docs/decisions/0041-per-claim-ledger-schema.md` ✔
- [x] T0.9: Write ADR-0042 (health priority boost) → `docs/decisions/0042-source-health-priority-boost.md` ✔

### Phase 1 — Config & Protocol Extensions (DONE)

- [x] T1.1: Add source_authority config section → `src/sprue/engine/defaults.yaml` ✔
- [x] T1.2: Extend verify protocol with per-claim fields → `src/sprue/engine/protocols/verify.md` ✔
- [x] T1.3: Add cite-then-claim to compile protocol → `src/sprue/engine/protocols/compile.md` ✔
- [x] T1.4: Wire ADR references in design docs → `docs/design/source-authority-model.md`, `docs/design/confidence-state-machine.md` ✔

### Phase 2 — Query & Index Infrastructure (DONE)

- [x] T2.1: Create query-provenance.py script → `src/sprue/engine/scripts/query-provenance.py` ✔
  - Claim→source query: input (page slug, claim ID), output (tier, URL, excerpt, date)
  - Source→pages reverse lookup: input (source URL), output (page slugs with claim IDs)
  - `--json` output flag
- [x] T2.2: Extend build-index.py to generate by-source-url.yaml → `src/sprue/engine/scripts/build-index.py` ✔
  - Reverse index from source URLs to citing pages
  - Generated during index rebuild
- [x] T2.3: Create compile-attributed.md prompt template → `src/sprue/engine/prompts/compile-attributed.md` ✔
  - Guides cite-then-claim constrained generation
  - Select excerpt → generate claim → insert marker → repeat

### Phase 3 — Validators (DONE)

- [x] T3.1: Create check-claims-coverage.py validator → `src/sprue/engine/scripts/check-claims-coverage.py` ✔
  - Checks % of verifiable claims with `[^src-N]` markers
  - Advisory when `config.source_authority.enforce_claims` is false
  - Fails when enforce_claims is true and coverage < `config.source_authority.enforce_coverage_threshold`
- [x] T3.2: Register check-claims-coverage in rules.yaml template → `src/sprue/templates/memory/rules.yaml` ✔

### Phase 4 — Source Health Monitoring (TODO, independent track)

- [ ] T4.1: Create check-source-health.py script → `src/sprue/engine/scripts/check-source-health.py`
  - URL liveness checks (HTTP status)
  - Content drift detection (excerpt substring matching)
  - Writes to `state/source-health.yaml`
  - Opt-in via `config.source_authority.health_check.enabled`
- [ ] T4.2: Update maintain protocol with health check sub-task → `src/sprue/engine/protocols/maintain.md` (depends: T4.1)

### Phase 5 — Integration & Verification (TODO)

- [ ] T5.1: Update query protocol with provenance-check plan → `src/sprue/engine/protocols/query.md` (depends: T2.1)
  - Add provenance-check query plan pattern
  - Surface source quality in query responses
- [ ] T5.2: End-to-end test: compile sourced page → verify → query provenance (depends: T2.1, T3.1)
- [ ] T5.3: Update AGENTS.md next ADR number and repo map counts → `AGENTS.md` (depends: T5.2)

## Non-Goals

- **Mass backfill of existing pages.** Normal verify cadence handles attribution incrementally.
- **Semantic content drift detection.** v1 uses substring matching; NLP-based drift is deferred.
- **External API for provenance queries.** Internal script only (`query-provenance.py`).
- **Source quality ranking in query responses.** Deferred — minor gap, not blocking.

## Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Cite-then-claim increases compile token cost 20–30% | Medium | High | Advisory coverage threshold; synthesized pages unaffected |
| Per-claim ledger bloats verifications.yaml | Low | Medium | ~2KB/page/verification; split to per-page files at 5MB |
| Excerpt substring matching produces false drift alerts | Medium | Medium | Conservative `drift_threshold` default (0.3); opt-in health checks |
| LLM fails to follow cite-then-claim pattern consistently | Medium | Medium | >80% target (not 100%); verify-time fallback tracks coverage |

## Dependency Graph

```
Phase 0 → Phase 1 → Phase 2 (scripts/templates) → Phase 5 (integration)
                   → Phase 3 (validators)        ↗
         Phase 0 → Phase 4 (health monitoring, independent)
```
