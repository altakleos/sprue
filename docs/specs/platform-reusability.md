---
status: accepted
date: 2026-04-16
---
# Platform Reusability

## Intent

The platform separates the reusable engine from domain-specific identity. Any knowledge domain — technology, cooking, law, medicine — can use the same engine by providing only an identity statement and configuration overrides. The engine contains no domain-specific assumptions. Instance customization is minimal and intention-revealing.

## Invariants

- The engine is domain-agnostic. Protocols, scripts, and default configuration reference "the KB" — never a specific domain, audience, or subject area.
- Instance identity is a single prose statement that drives audience, voice, depth, and scope. Everything domain-specific flows from this statement.
- Instance configuration overrides only what differs from platform defaults. Unmentioned values inherit the platform default. This keeps overrides small and readable.
- Configuration uses three tiers with clear boundaries: platform invariants (structural rules that no instance should change), tunables (numeric thresholds with sensible defaults), and identity (prose that shapes voice and scope).
- Platform upgrades can ship new defaults without touching instance configuration. The deep-merge model ensures backward compatibility for instances that override only a subset of values.
- Scope policy lives in instance identity, not in the engine. The engine provides mechanisms; the instance decides what is in-scope.

## Rationale

The KB started as a personal tool with identity assumptions baked into every layer — engine docs referenced a specific audience, protocols assumed a specific domain, and scripts contained instance-specific paths. When the idea of reusing the engine for other domains emerged, these couplings made it impossible. The sprue/instance split was the solution: decouple the engine (reusable) from the identity (specific). This makes the platform a genuine product rather than a personal tool.

The three-tier configuration model prevents the common failure mode where platform upgrades conflict with user customization. By separating what cannot change (invariants), what can change (tunables), and what must change (identity), each tier evolves independently.

## Decisions

- [ADR-0006: Configuration Layering](../decisions/0006-configuration-layering.md) — platform defaults + instance overrides with deep-merge semantics
- [ADR-0007: Platform/Instance Architecture](../decisions/0007-platform-instance-architecture.md) — reusable engine decoupled from domain identity

## Design

- [Three-Command Pipeline](../design/three-command-pipeline.md) — pipeline boundary ownership enables reusability
- [Prose-as-Code Execution Model](../design/prose-as-code.md) — domain-agnostic execution model
