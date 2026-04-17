---
status: accepted
date: 2026-04-16
---
# ADR-0031: Product Name — Sprue

## Context

The platform needed a product name for distribution as a standalone package. The name needed to be short (4-7 chars), memorable, available across PyPI/GitHub/npm, and carry a metaphor that fits the product's function (transforming raw material into structured output).

## Decision

Name the product **Sprue** — the channel through which raw material flows into a mold. The metaphor maps precisely: raw sources flow through the sprue (the engine) and emerge as shaped wiki pages. The name is 5 characters, one syllable, easy to spell, and has zero conflicts on PyPI, GitHub, or npm.

## Alternatives Considered

- **Kiln** — best metaphor (raw → fired output) but conflicts with Kiln AI (4.8k GitHub stars, same AI/LLM space)
- **Retort** — distillation vessel, good metaphor but less well-known word
- **Codex** — perfect meaning but namespace destroyed by OpenAI Codex
- **Lore** — accumulated knowledge, but PyPI taken (Uber ML framework)

## Consequences

Clean namespace across all registries. The name works as CLI (`sprue init`, `sprue compile`), package (`pip install sprue`), and directory (`.sprue/` in instances). The metaphor requires a one-sentence explanation for users unfamiliar with the term.
