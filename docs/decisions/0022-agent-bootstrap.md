---
status: accepted
date: 2026-01-25
---
# ADR-0022: Agent Bootstrap — AGENTS.md Import Chain

## Context
LLM agents need a reliable entry point to understand the KB's structure, commands, and constraints before operating. Without a standardized bootstrap, each agent session starts with ad-hoc exploration, wasting context window budget and risking incorrect assumptions about platform behavior.

## Decision
Agent bootstrap uses AGENTS.md as the canonical entry point, which imports platform and instance configuration through a defined chain. This establishes a single, predictable contract for any LLM agent operating the KB, regardless of the underlying model.

## Alternatives Considered
- **Inline all instructions in a single file** — becomes unwieldy as the platform grows; no separation between platform and instance concerns
- **Let agents discover structure organically** — unreliable; different agents make different assumptions, leading to inconsistent behavior

## Consequences
Any LLM agent can operate the KB by reading one file. The import chain keeps platform and instance instructions separated but composable. Changes to the bootstrap contract require updating AGENTS.md, which is a visible, reviewable change.

## Design

- [Prose-as-Code Execution Model](../design/prose-as-code.md)
