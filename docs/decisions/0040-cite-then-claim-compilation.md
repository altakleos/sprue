---
status: accepted
date: 2026-04-18
---

# ADR-0040: Cite-Then-Claim Generation at Compile Time

## Context

The compile protocol currently generates wiki pages from raw sources without per-claim attribution. Claims are written first, then verified retrospectively by the verify protocol. The source-authority-pipeline spec (now Per-Claim Source Provenance) requires that attribution is produced at write time, not retrofitted.

Industry research (ReClaim 2024) shows that constrained generation — alternating between selecting a source excerpt and generating a claim grounded in it — achieves 90% citation accuracy, far exceeding post-hoc attribution (~74% baseline).

The verify protocol already extracts claims and sources them individually, but only in adversarial mode and only retrospectively. Extending this to compile time is architecturally different: it changes the compilation model from "write then verify" to "cite then write".

## Decision

During compilation of sourced pages (pages with available raw files), the LLM alternates between selecting a source excerpt and generating a claim grounded in that excerpt. Each grounded claim receives an inline footnote marker (`[^src-N]`) linking to a verification ledger entry.

This applies only to sourced pages compiled from raw files. Synthesized pages (no raw source) are compiled without markers — their claims are attributed retrospectively during verification. The cite-then-claim pattern is implemented as a compile protocol extension (Step 4), not a replacement. Existing compilation behavior is preserved for synthesized content.

A new prompt template (`compile-attributed.md`) guides the constrained generation pattern. Coverage target: >80% of verifiable claims in newly compiled sourced pages should have attribution markers. This is advisory initially, enforced via config (`config.source_authority.enforce_coverage_threshold`).

## Alternatives Considered

- **Post-hoc attribution only (status quo)** — rejected because retrospective attribution is less accurate (~74% vs ~90%) and requires a separate verify pass to produce what could be generated at write time.
- **Mandatory 100% coverage** — rejected because some claims synthesize across multiple source sections and can't be attributed to a single excerpt. The 80% target acknowledges this reality.
- **Separate attribution pass after compilation** — rejected because it requires re-reading the page and sources, doubling context usage. Inline attribution during generation is more token-efficient.
- **Marker insertion by verify protocol only** — rejected because it means newly compiled pages ship without attribution until their first verification. Cite-then-claim ensures attribution from day one for sourced content.

## Consequences

Compile protocol becomes more complex for sourced pages. The LLM must manage both content generation and source tracking in a single pass. Token cost per sourced page increases (~20–30%) due to the constrained generation pattern.

Two attribution tracks now coexist: write-time (compile, new sourced pages) and verify-time (verify, existing pages and synthesized content). Both produce the same marker format and ledger entries. The verification ledger (`verifications.yaml`) gains entries at compile time, not just verify time. This is consistent with the append-only state model.

Existing KBs are unaffected — the feature activates only when raw sources are available and the compile protocol is invoked.

## Specs

- [Per-Claim Source Provenance](../specs/source-authority-pipeline.md) — G3 (cite-then-claim generation)
- [Source-Grounded Knowledge](../specs/source-grounded-knowledge.md) — provenance completeness invariant

## Design

- [Source Authority Model](../design/source-authority-model.md) — cite-then-claim generation subsection
