---
status: accepted
date: 2025-04-20
---
# ADR-0011: Entity Ontology — Types, Relationships, and Resolution

## Context
Wiki pages referenced other concepts freely through wikilinks, but there was no formal model for what kinds of entities existed or how they related. A page about "Kubernetes" might link to "containers" and "orchestration" with no distinction between "implements," "relates-to," or "is-a" relationships. Without typed relationships, the knowledge graph was flat — useful for navigation but not for reasoning about the domain structure.

## Decision
Introduce a formal entity type registry with typed relationships. Entity types (concept, tool, pattern, etc.) define expected attributes and relationship cardinalities. Relationship types (implements, extends, competes-with, etc.) have explicit format handling rules governing how they render in pages. The resolve-relationships protocol governs how entity links are maintained — when a page is compiled, its relationships are validated against the type registry.

## Alternatives Considered
- **Freeform relationship labels per page** — rejected because inconsistent labels ("uses" vs "depends-on" vs "requires") prevent meaningful graph queries
- **Full RDF/OWL ontology** — rejected as far too heavy for an LLM-operated system; the type registry provides enough structure without formal logic

## Consequences
The knowledge graph gained semantic depth — queries can now traverse typed relationships ("what tools implement this pattern?"). The cost is ontology maintenance: new entity types and relationship types must be defined before they can be used, adding friction to novel content.

## Specs

- [Emergent Classification](../specs/emergent-classification.md)
