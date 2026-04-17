---
status: accepted
date: 2026-02-10
---
# ADR-0023: Reset Command — Soft/Standard/Hard Levels

## Context
Agent state accumulates over time — learned rules, cached indexes, compiled artifacts. When state becomes corrupted or stale, operators need a way to clear it without manually identifying which files to delete. A single "reset everything" command is too destructive for routine use.

## Decision
The reset command provides three escalation levels: soft (clears memory and cached state only), standard (also rebuilds indexes and derived data), and hard (full rebuild including recompilation of all wiki content). Each level is a strict superset of the previous.

## Alternatives Considered
- **Single reset level** — too coarse; operators either lose everything or nothing, with no middle ground
- **Per-artifact reset flags** — too granular; operators must understand internal state structure to use effectively

## Consequences
Operators can recover from most state issues with soft reset, reserving hard reset for serious corruption. The three-level model is easy to remember and document. Hard reset can be time-consuming on large KBs, so operators should understand the cost before invoking it.

## Specs

- [Content Safety](../specs/content-safety.md)
