---
status: draft
date: 2026-04-16
---
# Source Authority Pipeline

## Intent

Every factual claim in the KB is traceable to a specific human-produced source — not just at the page level, but at the claim level. Source health is monitored. The provenance chain from original URL to captured source to wiki page to individual claim is complete and machine-queryable. The system knows, for any given fact, exactly where it came from, when it was last checked, and whether the source is still alive.

## Invariants

- Per-claim source attribution — each verifiable claim links to the source excerpt that supports it, not just the page that contains it.
- Structured sources field in page metadata linking to raw files and authoritative URLs. Source attribution is machine-readable, not just inline narrative citations.
- Honest provenance — pages genuinely synthesized from training knowledge are marked `synthesized`, not uniformly `sourced`. The distinction is enforced, not aspirational.
- Source health monitoring — authoritative URLs in the sources registry are checked for liveness and content drift. Stale or dead sources are flagged for re-import or replacement.
- The provenance chain is machine-queryable: given a claim, the system can return its source tier, URL, verification date, and the source excerpt that supports it.
- Source quality is ranked — official documentation, RFCs, and academic papers outrank blog posts, which outrank training knowledge. The ranking is explicit and consistent across all operations.

## Rationale

The existing source-grounded-knowledge spec establishes the principle that every fact traces to a human-produced source. This spec completes the chain: closing the gap between design intent (per-claim traceability) and current reality (page-level provenance with narrative-only citations).

Without per-claim tracking, the system cannot answer "where did this specific fact come from?" — only "what raw file was this page compiled from?" That coarser granularity is insufficient for targeted re-verification, for resolving contradictions between sources, and for building trust with consumers who need to audit individual claims.

Source health monitoring prevents the silent accumulation of dead links and outdated references. A source registry that points to URLs last checked months ago offers false confidence. Active monitoring keeps the authority chain honest.

## Design

- [Source Authority Model](../design/source-authority-model.md) — tiered source escalation and authority hierarchy

## Decisions

*This spec is deferred, but foundational provenance work has begun:*

- Compile protocol updated with provenance decision rule and `sources` field (2026-04-16)
- `provenance` added to manifest index for agent-queryable filtering (2026-04-16)
- Advisory validation rule prepared for when `sources` field is backfilled across existing pages
