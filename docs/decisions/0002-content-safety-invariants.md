---
status: accepted
date: 2024-10-01
---
# ADR-0002: Content Safety Invariants

## Context
An LLM agent with filesystem access can create, modify, and delete pages autonomously. Early operations revealed three failure modes: the agent deleted pages it deemed low-quality (losing human-curated content), created pages as side effects of other commands (polluting the wiki), and was too conservative about creating pages when explicitly asked (requiring repeated prompting). These needed non-negotiable guardrails.

## Decision
Establish three content safety invariants that govern all agent behavior. First, never delete pages without explicit human approval. Second, bias toward page creation when the user's intent is clear, using an explicit word-count threshold to decide standalone page vs. section merge. Third, no side-effect page creation — pages are only created through explicit pipeline commands (compile, expand), never as a byproduct of queries or maintenance.

## Alternatives Considered
- **Soft guidelines instead of invariants** — rejected because the agent optimized around soft rules, treating them as suggestions
- **Require human approval for all writes** — rejected because it would make the agent too slow for routine compilation work

## Consequences
These three rules became the platform's behavioral constitution — every protocol and command respects them. The trade-off is reduced agent autonomy: legitimate cleanup (removing truly obsolete pages) requires human intervention even when the agent correctly identifies the need.

## Specs

- [Content Safety](../specs/content-safety.md)
