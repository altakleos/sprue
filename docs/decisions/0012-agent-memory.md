---
status: accepted
date: 2025-05-10
---
# ADR-0012: Agent Memory — Rules, Corrections, and Learning

## Context
The LLM agent repeated the same mistakes across sessions — misclassifying pages, applying wrong size limits, ignoring instance-specific conventions. Corrections given in one conversation were lost in the next. Early attempts stored rules in learned-rules.md as freeform text, but the agent would rewrite rules at runtime, sometimes weakening or contradicting them. Path-scoped rules broke when directories reorganized.

## Decision
Adopt a structured rule schema (rules.yaml) with frontmatter-type gates replacing path-scoped rules. Each rule has a trigger condition, the correction, and metadata about when it was learned. Rules are read-only at runtime — the agent reads them but never rewrites them; only the human or a dedicated memory-update command can modify rules. The memory correction loop uses probe presence checks to verify the agent has internalized a correction before marking it resolved.

## Alternatives Considered
- **Freeform markdown rules file** — rejected because the agent treated it as editable prose and would soften or remove rules it disagreed with
- **Embedding corrections into system prompts** — rejected because prompt space is limited and corrections accumulate over time

## Consequences
The agent's behavior became consistent across sessions — learned corrections persist and are enforced structurally. The trade-off is that rules require manual curation; stale rules that no longer apply must be explicitly removed rather than naturally fading.

## Design

- [Agent Memory and Learning](../design/agent-memory.md)
