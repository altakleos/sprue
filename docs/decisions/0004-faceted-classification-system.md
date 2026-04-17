---
status: accepted
date: 2025-03-15
---
# ADR-0004: Faceted Classification System

## Context
Classification went through three failed approaches. Flat tags produced 965 values with 60% singletons — useless for navigation. Domain-based taxonomy (6 directories) forced cross-cutting concerns into single buckets. Renaming facets and vocabulary caused repeated churn. The system needed a stable, multi-dimensional classification that could evolve without restructuring.

## Decision
Adopt a three-facet classification system: topics (what it's about), domain (which field), and aspects (cross-cutting concerns like security, performance). Facets are fully config-driven with enforced creation thresholds to prevent tag explosion. A two-tier automation model governs classification: high-confidence assignments auto-execute, ambiguous ones ask the human. Facet vocabulary, descriptions, and per-facet limits are all overridable in instance config.

## Alternatives Considered
- **Flat tags with deduplication** — rejected because even deduplicated tags lack the dimensional structure needed for meaningful filtering
- **Hierarchical taxonomy with fixed categories** — rejected because rigid hierarchies break when content spans multiple domains

## Consequences
Faceted classification made navigation and filtering dramatically better — pages became discoverable along multiple axes. The cost is configuration complexity: instances must define meaningful facet vocabularies, and creation thresholds require tuning to balance expressiveness against sprawl.

## Specs

- [Emergent Classification](../specs/emergent-classification.md)
