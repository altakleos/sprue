---
status: draft
date: 2026-04-18
---
# Per-Claim Source Provenance

## Intent

Every verifiable factual claim in a wiki page is traceable to a specific source excerpt — not just the page it was compiled from. The provenance chain from claim to source is machine-queryable in both directions. Attribution is produced at write time through constrained generation, not retrofitted after the fact.

## Invariants

- **G1 — Per-Claim Source Attribution.** Every verifiable factual claim in a wiki page carries an inline citation marker linking to a verification ledger entry that records: the source tier used, the source URL, the source excerpt, and the verification date. Pages without per-claim markers are valid but report incomplete attribution coverage.

- **G2 — Machine-Queryable Provenance Chain.** Given a page slug and claim text, the verification ledger returns the full provenance chain: source tier, source URL, source excerpt, and verification date. Given a source URL, the manifest index returns all pages citing that source. These two query directions (claim→source and source→pages) are the minimum queryable interface.

- **G3 — Cite-Then-Claim Generation.** During compilation from raw sources, the LLM alternates between selecting a source excerpt and generating a claim grounded in it. This constrained generation pattern ensures attribution is produced at write time, not retrofitted.

## Acceptance Criteria

**G1 — Per-Claim Source Attribution:**
- (a) Verified pages contain inline `[^src-N]` markers in the body text.
- (b) Each marker has a corresponding entry in the verification ledger.
- (c) Each ledger entry records the 4 required fields: source tier, source URL, source excerpt, and verification date.

**G2 — Machine-Queryable Provenance Chain:**
- (a) Claim→source query returns results for any marked claim given page slug and claim ID.
- (b) Source→pages reverse lookup returns all pages citing a given source URL.

**G3 — Cite-Then-Claim Generation:**
- (a) Newly compiled pages from raw sources achieve >80% claim attribution coverage.

## Dependencies

- **Depends on:** [Source-Grounded Knowledge](source-grounded-knowledge.md) (accepted) — base provenance model, tiered authority, raw immutability.
- **Enhances:** [Verified Knowledge Service](verified-knowledge-service.md) (draft) — per-claim provenance enriches query responses but does not block that spec.

## Migration

Fully additive. No mass backfill required. Existing pages without markers remain valid. The normal verify cadence enriches pages incrementally — each verification run assigns claim IDs and inserts markers. Advisory validators become enforced after 80% coverage across verified pages.

## Rationale

The parent spec (source-grounded-knowledge) establishes that every fact traces to a human-produced source. But page-level provenance only answers "what raw file was this page compiled from?" — not "where did this specific fact come from?" That coarser granularity is insufficient for targeted re-verification, for resolving contradictions between sources, and for building trust with consumers who need to audit individual claims.

Per-claim provenance is the one genuinely new capability this spec introduces. It closes the gap between the platform's design intent (claim-level traceability) and its current reality (page-level attribution with narrative-only citations).

## Design

- [Source Authority Model](../design/source-authority-model.md) — tiered source escalation, authority hierarchy, citation schema

## Decisions

- Structured `sources` field and `provenance` tracking moved to parent spec ([source-grounded-knowledge](source-grounded-knowledge.md)) — those are base-level guarantees, not per-claim concerns.
- Source health monitoring (liveness checks, content drift) relocated to [continuous-quality](continuous-quality.md) — health is an operational quality concern, not a provenance concern.
- Source quality ranking (tier ordering) moved to parent spec — ranking is a platform-wide authority model, not specific to per-claim attribution.
- Scope narrowed from 6 guarantees covering 3 unrelated capabilities to 3 guarantees focused on per-claim provenance as the single new capability.
- Compile protocol updated with provenance decision rule and `sources` field (2026-04-16).
- `provenance` added to manifest index for agent-queryable filtering (2026-04-16).
