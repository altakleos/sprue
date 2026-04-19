---
status: superseded
superseded-by: 0043
date: 2026-04-16
---
# ADR-0026: Spec-Driven Development Process

## Context
The platform was developed organically. Ideas emerged during development and decisions were captured retroactively in ADRs. This produced 25 ADRs, 15 protocol files, and a comprehensive engine.md — but no documentation of how these layers relate, no formal specs, and no design docs. ADRs sat at the top of the documentation stack, serving as both decision records and implicit product specifications.

Analysis revealed three insights: (1) the platform needed a layer above ADRs that captures product intent before design begins; (2) protocol files are not documentation but executable prose code interpreted by the LLM runtime — a distinction that was implicit but never formalized; (3) Python scripts function as the test suite, not as "tooling."

## Decision
Adopt a six-layer development stack: Specs (product intent, implementation-agnostic) → Design Docs (technical architecture, high-level) → ADRs (decisions with context and alternatives) → Protocols (prose code, LLM-executable) → Config (tunables) → Validators (executable assertions). Specs come before ADRs — they define the intent that ADRs record decisions about. This inverts the previous model where ADRs were the starting point.

The development process is documented in `docs/development-process.md`. Specs live in `docs/specs/`. Design docs live in `docs/design/`. The existing `docs/decisions/`, `sprue/protocols/`, `sprue/defaults.yaml`, and `sprue/scripts/` continue unchanged.

The prose-as-code execution model is formally recognized: protocol files are code executed by the LLM runtime, not documentation. Python scripts are validators and deterministic subroutines, not tooling.

## Alternatives Considered
- **Adopt GitHub Spec Kit or AWS Kiro** — rejected because these tools assume spec → traditional code. The platform uses prose-as-code where the "code" is already human-readable markdown. Standard SDD tools would add a redundant layer.
- **Continue organic development with ADRs only** — rejected because ADRs capture decisions (the "which" and "why") but not product intent (the "what") or technical architecture (the "how" at a high level). The gap between ADRs and protocols left intent implicit and architecture undocumented.
- **Write specs retroactively for everything** — rejected as too expensive. Instead, existing intent was extracted into 5 accepted specs from engine.md and ADRs, with 3 draft specs for future strategies. New work follows spec-first going forward.

## Consequences
New features follow a spec-first workflow: write a spec (if product intent is new), then a design doc (if architecture is new), then ADRs as decisions crystallize, then protocol changes. Small changes skip directly to protocol or config. The ceremony scales with the change's impact. The development process document serves as the reference for contributors — it explains the stack, work flows, and when to write each artifact type.

## Config Impact
New directories: `docs/specs/`, `docs/design/`
New file: `docs/development-process.md`
