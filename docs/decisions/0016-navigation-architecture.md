---
status: accepted
date: 2025-07-15
---
# ADR-0016: Navigation Architecture — Hub and Sub-Indexes

## Context
As the wiki grew past 200 pages, a single flat index became unwieldy for both humans and LLMs. Readers needed a stable entry point that did not grow linearly with content, plus domain-specific views with meaningful ordering.

## Decision
A constant-size hub page links to domain sub-indexes, each importance-sorted with "start here" guidance for newcomers. The overview page is auto-generated from content metadata, replacing the manually maintained index.md that frequently drifted from actual content.

## Alternatives Considered
- **Single growing index** — becomes unusable past ~100 entries; LLM context window waste
- **Alphabetical sub-indexes** — easy to generate but unhelpful for discovery; importance sorting serves readers better

## Consequences
The hub stays small regardless of wiki size, making it LLM-friendly. Sub-indexes provide curated entry points per domain. Auto-generation eliminates index drift. Adding a new domain requires creating a sub-index template, a minor one-time cost.
