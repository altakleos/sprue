---
status: accepted
date: 2026-04-16
---
# Source-Grounded Knowledge

## Intent

The platform compiles knowledge from real, human-produced sources. Every factual claim traces to an external source. Content generated from training knowledge is explicitly marked as synthesized. The system prefers authoritative sources (official documentation, RFCs, academic papers) over secondary sources (blog posts, forums) over training knowledge (last resort). The raw source archive preserves what was captured; the wiki represents what the platform understood from it.

## Invariants

- Raw source files are immutable after capture — the original human-produced content is preserved unchanged.
- Every wiki page records its provenance: `sourced` (compiled from a raw file) or `synthesized` (generated from training knowledge).
- Verification checks claims against a tiered authority ladder: raw source, then authoritative documentation, then web search, then training knowledge.
- Training knowledge alone cannot confirm hard factual claims (version numbers, defaults, limits, behavioral assertions). When all other tiers are exhausted, the claim is marked unverifiable — not guessed.
- Authoritative documentation takes precedence when sources conflict. The raw file may have been wrong when imported; the authoritative doc represents current truth.
- Source capture and content interpretation are separate operations. Capture preserves the original unchanged. Interpretation happens later, at compilation time, when context is available.

## Rationale

Knowledge systems built on training knowledge inherit the model's blind spots, hallucinations, and training cutoff limitations. Grounding every fact in a human-produced source creates a verifiable chain of trust: the reader can trace any claim back to its origin. When a fact is wrong, the source chain reveals whether the error was in the original (update the source) or in the interpretation (fix the compilation). Without provenance tracking, errors are invisible and unfixable.

The tiered authority model ensures that the most reliable source is always tried first, and that the system is honest about when it falls back to less reliable tiers.

## Design

- [Source Authority Model](../design/source-authority-model.md) — tiered source escalation and authority hierarchy

## Decisions

- [ADR-0002: Content Safety Invariants](../decisions/0002-content-safety-invariants.md) — raw immutability as a safety principle
- [ADR-0003: Three-Command Pipeline](../decisions/0003-three-command-pipeline.md) — separation of capture (import) from interpretation (compile)
- [ADR-0009: Verification Pipeline](../decisions/0009-verification-pipeline.md) — source-backed fact-checking with tiered escalation
