---
status: accepted
date: 2025-07-01
---
# ADR-0015: Content Quality Model — Confidence, Decay, and Self-Healing

## Context
Wiki pages degrade over time as technology evolves and sources become outdated. The platform needed a quality model that tracks content freshness, flags degradation, and supports automated repair. Early summaries were mechanical extractions that failed to capture page intent.

## Decision
Content quality is governed by confidence levels with decay tiers stored in frontmatter. LLM-generated summaries replaced mechanical first-paragraph extraction, producing contextually accurate descriptions. A self-healing system detects degraded pages via confidence decay and queues them for recompilation.

## Alternatives Considered
- **Manual quality reviews** — does not scale past a few hundred pages; relies on operator discipline
- **Time-based expiry without confidence tiers** — too coarse; high-quality evergreen content would be needlessly recompiled

## Consequences
Content quality is continuously monitored without operator intervention. The compile pipeline writes pages at medium confidence; the verify pipeline promotes them. Decay tiers add frontmatter complexity but make quality visible and actionable.

## Specs

- [Continuous Quality](../specs/continuous-quality.md)

## Design

- [Confidence State Machine](../design/confidence-state-machine.md)
