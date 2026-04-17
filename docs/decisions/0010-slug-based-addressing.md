---
status: accepted
date: 2025-05-20
---
# ADR-0010: Slug-Based Addressing

## Context
Content was addressed by filesystem path, which coupled page identity to directory structure. When the emergent directory system reorganized pages, every reference (cross-links, ledger entries, compilation records) broke. The fix-compilations script patched things post-reorg, but the root cause was that identity and location were conflated. Ledgers and indexes needed a stable identifier that survived moves.

## Decision
Migrate content addressing from filesystem paths to slugs — stable, human-readable identifiers derived from page titles. Ledgers, cross-links, and compilation records all reference slugs instead of paths. The slug→raw reverse index is derived (computed from current state), not maintained as a separate data structure. Local-search-first resolution rules govern how slugs map to files, preferring the current directory before searching globally.

## Alternatives Considered
- **UUIDs as stable identifiers** — rejected because they're not human-readable and make manual debugging painful
- **Keep paths but add redirect maps after moves** — rejected because it accumulates technical debt with every reorganization

## Consequences
Pages can move between directories without breaking any references — reorganization became a zero-cost operation. The trade-off is that slug uniqueness must be enforced (no two pages can share a slug), and slug derivation rules must be deterministic across all agents.
