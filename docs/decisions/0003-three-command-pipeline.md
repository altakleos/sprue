---
status: accepted
date: 2025-01-20
---
# ADR-0003: Three-Command Pipeline — Import/Compile/Expand

## Context
The content pipeline started as a single "discover and write" prompt, then split into multiple specialized commands that overlapped and confused users. Source approval happened implicitly, compilation mixed with gap-filling, and the enhance step's output had no structured handoff to expansion. The pipeline needed a clean decomposition with clear boundaries between stages.

## Decision
Crystallize the content pipeline into three commands with strict responsibilities. Import handles source approval and ingestion into raw/. Compile transforms raw material into wiki pages, re-emerging directory structure from the manifest. Expand discovers knowledge gaps, researches them, and feeds new sources back into import. The enhance→expand handoff uses enhancements.yaml as a structured gap registry.

## Alternatives Considered
- **Single monolithic ingest command** — rejected because it conflated source vetting with compilation, making failures hard to diagnose
- **Five-command pipeline with separate enhance and verify stages** — rejected because the extra granularity added cognitive overhead without proportional benefit

## Consequences
Three commands are easy to remember and compose. Each stage has a single input and output, making debugging straightforward. The trade-off is that multi-step workflows (ingest a URL end-to-end) require chaining commands, though the agent handles this transparently in semi-auto mode.

## Design

- [Three-Command Pipeline](../design/three-command-pipeline.md)
