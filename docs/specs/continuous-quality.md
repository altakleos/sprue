---
status: accepted
date: 2026-04-16
---
# Continuous Quality

## Intent

Content quality is continuously monitored, measured, and maintained. The platform tracks content freshness, detects degradation, and supports automated repair. Quality is visible and actionable — an operational state with defined transitions, not a subjective judgment. The system never claims confidence it has not earned through independent verification.

## Invariants

- Confidence is an operational state, not a self-assessment. The agent never self-assigns high confidence for its own content. New agent-authored content starts at medium (default) or low (speculative).
- High confidence is earned only through independent verification against authoritative sources. This is a state transition, not a label — it requires source-backed fact-checking of every hard factual claim.
- Content degrades over time at domain-appropriate rates. Fast-moving subjects (APIs, framework versions) decay faster than stable subjects (algorithms, mathematical fundamentals).
- Risk tiers weight decay. Wrong information in critical areas (security, infrastructure) is treated as more urgent than wrong information in conceptual areas.
- Verification is source-backed. No verdict is issued without a specific source excerpt supporting it. When all source tiers are exhausted, the claim is marked unverifiable rather than guessed at.
- Summaries capture page intent accurately, enabling effective retrieval and triage without reading the full page.
- Quality degradation is detected automatically and queued for remediation. The operator does not need to manually audit pages for staleness.

## Rationale

An earlier calibration found ~70% of LLM-self-assigned high-confidence pages had factual errors on verifiable claims. The confidence invariant exists because of this empirical finding — not as a philosophical position, but as a measured response to observed failure rates. Without it, the KB would present unverified content as trustworthy.

Content decay is inevitable in any knowledge system. Technology evolves, defaults change, APIs are deprecated. A static wiki accumulates errors silently. The decay model makes staleness visible and actionable: pages are scored by risk and freshness, enabling prioritized verification rather than random audits.

The combination of earned confidence, domain-aware decay, and source-backed verification creates a quality flywheel: degraded content is detected, verified content earns trust, and the operator can focus attention where it matters most.

## Design

- [Confidence State Machine](../design/confidence-state-machine.md) — operational confidence driven by verification, decay tiers

## Decisions

- [ADR-0009: Verification Pipeline](../decisions/0009-verification-pipeline.md) — adversarial writer/critic/judge model with source-backed fact-checking
- [ADR-0015: Content Quality Model](../decisions/0015-content-quality-model.md) — confidence levels, decay tiers, self-healing
- [ADR-0025: Schema Versioning](../decisions/0025-schema-versioning.md) — tracking frontmatter evolution for incremental migration
