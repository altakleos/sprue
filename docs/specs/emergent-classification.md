---
status: accepted
date: 2026-04-16
---
# Emergent Classification

## Intent

The platform classifies content along multiple independent dimensions without predefined category lists. Structure, vocabulary, and taxonomy emerge from the content itself. The system resists premature structure while providing meaningful navigation and filtering as content grows. Classification adapts to the domain — a technology KB and a cooking KB develop different vocabularies organically, without requiring different engines.

## Invariants

- Facet vocabularies are emergent — the set of existing pages IS the approved-values list. No separate registry of allowed values is maintained.
- Some classification dimensions resist vocabulary growth (conservative: broad categories that should be few and stable) while others embrace it (liberal: specific topics that naturally multiply).
- Navigational groupings emerge from content clustering, not from predefined taxonomy. No empty categories exist — structure is created only when content exists to populate it.
- Classification dimensions are independent axes. A page's navigational placement does not constrain its metadata values, and vice versa.
- Content types (the form knowledge takes: concept, entity, pattern, recipe) are distinct from classification metadata (what the content is about). Form and subject are orthogonal.
- Entity types (what kind of thing the subject is: message-broker, relational-database) are a third independent axis, describing the ontological nature of the subject — not the page's form or topic.
- Auxiliary data structures (synonym maps, placement signals, alias registries) are derived from content at compilation time, not manually curated.

## Rationale

Three prior approaches to classification failed. Flat tags produced 965 values with 60% singletons — useless for navigation. Domain-based taxonomy with predefined directories forced cross-cutting concerns into single buckets. Renaming facets and vocabulary caused repeated churn. The emergent approach solved all three: vocabulary grows naturally, cross-cutting content carries multiple values, and churn is eliminated because no predefined structure needs updating.

The independence of axes (facets, directories, entity types) prevents the combinatorial explosion that occurs when classification dimensions are coupled. A page about Kafka can be in the `messaging/` directory, tagged with domains `[messaging, data]`, and typed as `message-broker` — all independently.

## Decisions

- [ADR-0004: Faceted Classification System](../decisions/0004-faceted-classification-system.md) — three-facet model with creation thresholds
- [ADR-0005: Content Type System](../decisions/0005-content-type-system.md) — nine content types with section contracts
- [ADR-0008: Emergent Directory Structure](../decisions/0008-emergent-directory-structure.md) — directories as shelves, not areas
- [ADR-0011: Entity Ontology](../decisions/0011-entity-ontology.md) — typed relationships and entity registry
- [ADR-0014: Emergent Data Structures](../decisions/0014-emergent-data-structures.md) — synonyms, signals, and guards derived from content

## Design

- [Confidence State Machine](../design/confidence-state-machine.md) — classification confidence tracking
- [Append-Only State Model](../design/append-only-state.md) — facet state management
