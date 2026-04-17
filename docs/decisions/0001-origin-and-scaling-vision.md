---
status: accepted
date: 2024-09-15
---
# ADR-0001: Origin and Scaling Vision

## Context
The KB started as a 96-page flat wiki — all pages in a single directory with no taxonomy, no automation, and no scaling strategy. At that size, flat structure worked, but growth was already creating findability problems. Without a roadmap, each new page made the system slightly harder to navigate, and there was no shared understanding of when structural changes should trigger.

## Decision
Adopt a four-phase scaling roadmap that defines structural milestones tied to page count thresholds. Phase 1 (flat wiki) carries through ~100 pages, Phase 2 introduces directory organization, Phase 3 adds faceted classification, and Phase 4 targets retrieval optimization. This gives the platform predictable evolution points rather than reactive restructuring.

## Alternatives Considered
- **Impose full taxonomy upfront** — rejected because premature structure creates empty categories and maintenance burden at small scale
- **Scale reactively without a plan** — rejected because ad-hoc restructuring leads to inconsistent organization and repeated rework

## Consequences
The roadmap gave every subsequent ADR a shared frame of reference — decisions could be justified by which phase they served. However, the phases proved to be rough guides rather than hard gates; real evolution was messier than the plan predicted, and several phase boundaries blurred together.
