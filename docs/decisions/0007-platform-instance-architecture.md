---
status: accepted
date: 2025-05-15
---
# ADR-0007: Platform/Instance Architecture — Reusable Engine

## Context
The KB was built as a personal tool with identity assumptions baked into every layer — engine docs referenced "Staff SDE," protocols assumed tech content, and scripts contained instance-specific paths. When the idea of reusing the engine for other domains (cooking, legal) emerged, these couplings made it impossible. The system needed a clean separation between the reusable engine and the specific instance.

## Decision
Decouple the platform from the instance through a physical directory restructure: sprue/ contains the domain-agnostic engine (engine.md, protocols, scripts, defaults, prompts), and instance/ contains identity (identity.md) and config overrides (config.yaml). Scope policy lives in instance identity, not the engine. All engine protocols and documentation are written to be identity-agnostic — they reference "the KB" rather than any specific domain.

## Alternatives Considered
- **Template-based approach with variable substitution** — rejected because it adds build complexity and makes the engine harder to read directly
- **Plugin architecture with domain adapters** — rejected as over-engineered for the current need; config layering achieves domain customization without code

## Consequences
The platform became a genuine product — any domain can use it by providing identity.md and config.yaml. The trade-off is that engine docs must be carefully written to avoid identity leakage, and contributors must think about whether a change belongs in sprue/ or instance/.

## Specs

- [Platform Reusability](../specs/platform-reusability.md)
