---
status: accepted
date: 2025-10-01
---
# ADR-0019: LLM Retrieval Optimization

## Context
LLM agents operating the KB retrieve wiki content through naive file reads, consuming context window budget inefficiently. As the wiki grows, retrieval strategy directly impacts agent effectiveness — reading irrelevant content wastes tokens while missing relevant content produces poor answers.

## Decision
A four-phase optimization plan governs how LLMs retrieve and use wiki content, progressing from naive full-file retrieval through structured access patterns with metadata-guided selection. Each phase builds on the previous, allowing incremental adoption.

## Alternatives Considered
- **Embedding-based RAG from the start** — requires infrastructure the platform does not assume; premature optimization for smaller KBs
- **No retrieval strategy** — works for small wikis but degrades rapidly past a few hundred pages

## Consequences
Retrieval efficiency improves incrementally without requiring infrastructure changes upfront. The phased approach lets each KB instance adopt optimizations as it grows. The plan adds architectural direction without imposing immediate implementation burden.
