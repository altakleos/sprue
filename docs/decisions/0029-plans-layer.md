---
status: accepted
date: 2026-04-16
---
# ADR-0029: Plans Layer — Task Breakdowns as Permanent Records

## Context
The six-layer stack (Specs → Design → ADRs → Protocols → Config → Validators) had no home for task plans. During the SDD pipeline, the PLAN phase produces an ordered task breakdown that implementing agents read before writing code. Without a persistent artifact, plans lived only in conversation context — lost between sessions, invisible to other agents, and unreviewable.

## Decision
Add `docs/plans/` as a permanent artifact layer for task breakdowns. Plans are written AFTER design and BEFORE implementation. They are committed to the feature branch as the first commit and kept as permanent records after the feature ships.

## Alternatives Considered
- **Plans as commit messages** — rejected because commits happen AFTER implementation, not before. A plan must exist before code is written.
- **Plans in agent handoff (.yolo-sisyphus/)** — rejected because handoff files are ephemeral, gitignored, and invisible to other agents or future contributors.
- **Plans embedded in design docs** — rejected because design docs describe mechanisms (HOW something works), not task sequences (WHAT to do in what order). Mixing them conflates architecture with execution.

## Consequences
The stack grows from six to seven layers. Plans provide a reviewable pre-implementation artifact that agents read for context. The cost is one more directory to maintain, but plans are lightweight (task lists, not prose) and their value as historical records justifies retention.
