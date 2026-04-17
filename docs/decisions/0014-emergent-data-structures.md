---
status: accepted
date: 2025-06-15
---
# ADR-0014: Emergent Data Structures — Synonyms, Signals, Guards

## Context
The platform accumulates several auxiliary data structures: synonym maps, never-link terms, universal aliases, and placement signals. Early designs maintained these manually, creating curation burden and staleness. The question was whether to treat them as configured artifacts or let them emerge from content patterns.

## Decision
Auxiliary data structures emerge from content rather than being manually curated. Synonym maps, never-link terms, and placement signals are derived at compile time from wiki content patterns. A type-purity placement guard with instance-configurable allowlists prevents content from being misclassified into the wrong content type during compilation.

## Alternatives Considered
- **Manually curated lookup tables** — high maintenance burden; stale within weeks as content evolves
- **Fully automated with no guards** — misclassification errors compound silently without purity checks

## Consequences
Auxiliary structures stay fresh automatically as content changes. The type-purity guard catches misclassification early. Instance owners must maintain allowlists when introducing new content type combinations, adding a small configuration surface.

## Config Impact
`compilation.type_purity.allowlist` — instance-level overrides for permitted type placements

## Specs

- [Emergent Classification](../specs/emergent-classification.md)
