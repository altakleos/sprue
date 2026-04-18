---
status: draft
date: 2026-04-18
---
# Verified Knowledge Service

## Intent

The platform exposes its verified, source-backed knowledge as a queryable service. External agents and systems can ask questions and receive answers that include explicit confidence levels, source tiers, verification dates, and decay status. Every answer tells the consumer WHERE the knowledge came from and HOW fresh it is. In a landscape where most AI tools retrieve knowledge without provenance, this service offers a fundamentally different trust contract.

## Invariants

- Confidence-aware responses — every answer includes its confidence level, source tier, and last-verified date. Consumers can filter or weight answers by trust level.
- Source-tier transparency — consumers know whether the answer came from an authoritative source, a raw import, web search, or training knowledge. The tier is explicit, not hidden.
- Decay-aware freshness — answers include the content's decay tier and age since last verification, enabling consumers to judge timeliness. A fast-decay answer verified 6 months ago is flagged differently from a glacial-decay answer verified 6 months ago.
- No silent confidence — the service never presents unverified content as verified. Absence of verification is explicitly communicated. A page at medium confidence is returned as medium, not silently promoted.
- Query interface is read-only — the service retrieves and presents knowledge but never modifies wiki content, state, or indexes.
- Answers are traceable — every response can be traced back to specific wiki pages, which trace to raw sources, which trace to original URLs. Page-level provenance (sourced/synthesized marking, sources field, tiered verification) provides the baseline trust chain. Per-claim provenance enhances traceability when available but is not required for core guarantees.

## Rationale

The platform already has the verification infrastructure, confidence model, and source authority hierarchy. These exist as internal quality mechanisms — they improve the wiki but are invisible to external consumers. This spec extends the trust architecture from an internal quality tool to an external service guarantee.

The value proposition is unique: no other knowledge tool can say "this answer is backed by RFC 8446, verified adversarially on this date, with a 365-day half-life and critical risk tier." RAG systems return chunks without provenance. Wikis return pages without freshness. This service returns knowledge with a full trust profile.

The read-only constraint ensures the service cannot corrupt the KB. It is a window into verified knowledge, not a write path.

## Dependencies

- [Source-Grounded Knowledge](source-grounded-knowledge.md) (accepted) — provides page-level provenance (sourced/synthesized marking, sources field, tiered verification) required for traceability guarantees.
- Enhanced by [Source Authority Pipeline](source-authority-pipeline.md) (draft) — per-claim provenance strengthens traceability but is not a prerequisite for this spec's core invariants.

## Design

- [Source Authority Model](../design/source-authority-model.md) — tiered source escalation and authority hierarchy
- [Confidence State Machine](../design/confidence-state-machine.md) — operational confidence driven by verification, decay tiers

## Decisions

- Per-claim provenance (source-authority-pipeline spec) enhances traceability but is not required for this spec's core guarantees. Page-level provenance from source-grounded-knowledge (accepted) is sufficient for the baseline trust contract.
- *ADRs will be created when design and implementation begin.*
