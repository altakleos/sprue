---
status: accepted
date: 2025-04-01
---
# ADR-0008: Emergent Directory Structure

## Context
Early directory organization was top-down: 6 domain directories were configured in advance, each with curated descriptions. This created empty directories waiting for content and forced pages into predetermined buckets. When the faceted classification system replaced domain-based taxonomy, the configured directories became redundant. A 337-page migration validated that directories could be derived from content patterns rather than prescribed.

## Decision
Directories are shelves, not areas — they emerge from content clustering rather than being configured upfront. Remove directory definitions from config entirely. Drop curated descriptions in favor of emergent signals (the pages themselves describe what a directory contains). Creation thresholds use prose principles ("create a new directory when a topic cluster exceeds N pages") rather than numeric config values, keeping the heuristic human-readable.

## Alternatives Considered
- **Keep configured directories with auto-creation for overflow** — rejected because it preserves the false authority of pre-defined categories
- **Flat structure with facet-only navigation** — rejected because directories provide useful spatial grouping for browsing, even if facets handle filtering

## Consequences
The wiki self-organizes as content grows — no empty directories, no forced categorization. The Phase 1 migration (337 page moves) proved the approach works at scale. The trade-off is that directory names are less predictable, and the agent must make judgment calls about when to create new directories.

## Specs

- [Emergent Classification](../specs/emergent-classification.md)
