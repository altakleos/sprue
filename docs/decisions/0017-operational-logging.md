---
status: accepted
date: 2025-08-01
---
# ADR-0017: Operational Logging — JSONL and Summary Fields

## Context
Early operational logs used markdown format, which was human-readable but difficult to parse programmatically. As the platform added automated verification and maintenance, tooling needed structured access to log entries. Log files also grew unbounded.

## Decision
Operational logs use JSONL format for machine readability and structured querying. Each log entry includes a summary field for quick scanning. Log rotation caps file size, keeping the operational footprint bounded and git-friendly.

## Alternatives Considered
- **Markdown logs** — readable but unparseable by tooling; no structured field access
- **SQLite or database logging** — overkill for a file-based platform; adds a runtime dependency

## Consequences
Tooling can filter and aggregate log entries programmatically. Summary fields enable quick triage without reading full entries. Log rotation prevents repository bloat. Human readability requires a formatting step, a minor tradeoff.

## Design

- [Append-Only State Model](../design/append-only-state.md)
