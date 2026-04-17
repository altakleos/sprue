---
status: accepted
date: 2026-04-01
---
# ADR-0024: Inbox Drop Zone

## Context
Users encounter interesting material throughout their day but lack a low-friction way to capture it for later processing. Requiring immediate classification or formatting creates enough friction to discourage capture, leading to lost knowledge.

## Decision
The inbox/ directory serves as a local-only drop zone for unsorted material. Files dropped here require no metadata, classification, or formatting. The import pipeline picks up inbox items and routes them through the standard ingestion flow when the operator is ready.

## Alternatives Considered
- **Direct import only** — requires immediate classification; high friction discourages capture of serendipitous finds
- **External capture tools (bookmarks, notes apps)** — fragments the knowledge pipeline; material never enters the KB without a separate transfer step

## Consequences
Knowledge capture becomes a zero-friction operation — just drop a file. The inbox is local-only (gitignored), so it does not pollute the repository. Operators must periodically process the inbox to prevent unbounded accumulation.
