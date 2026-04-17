---
status: accepted
date: 2026-01-10
---
# ADR-0021: Configurable Enhance Agents

## Context
The expand pipeline enriches wiki content, but different KB instances need different enrichment strategies. A tech KB might add code examples and API references, while a cooking KB might add nutritional data. Hardcoding enrichment logic in the platform engine prevents instance-specific customization.

## Decision
The expand pipeline supports pluggable enhance agents defined in instance configuration. Each agent specifies its enrichment strategy and target content types, allowing instance owners to tailor content expansion without modifying platform code.

## Alternatives Considered
- **Hardcoded enrichment in the engine** — forces all instances into the same enrichment strategy; violates sprue/instance separation
- **Free-form prompt overrides** — too unstructured; no way to compose or sequence multiple enrichment passes

## Consequences
Instances can define domain-specific enrichment without forking the platform. Enhance agents compose naturally for multi-pass enrichment. Agent authors must follow the plugin contract, adding a small learning curve for instance customizers.
