---
status: accepted
date: 2026-04-15
---
# ADR-0025: Schema Versioning and Status Reporting

## Context
As the platform evolves, frontmatter schemas change — new fields are added, old ones are renamed or removed. Without version tracking, it is impossible to know which pages conform to the current schema. Operators also lacked visibility into pending work like unprocessed inbox items.

## Decision
Schema versions are tracked in page frontmatter, enabling migration tooling to identify and upgrade pages with outdated schemas. The status command reports inbox count alongside wiki health metrics, giving operators a single view of content state and pending work.

## Alternatives Considered
- **No schema versioning** — forces manual audits to find outdated pages; migrations become guesswork
- **Separate status dashboard** — adds infrastructure; the CLI status command is sufficient for a file-based platform

## Consequences
Schema migrations can target specific versions, making upgrades incremental and safe. Status output gives operators actionable visibility without external tooling. Schema version bumps require updating the migration logic, adding a small maintenance cost per schema change.

## Config Impact
`schema.version` — current frontmatter schema version; used by migration tooling to detect outdated pages

## Specs

- [Continuous Quality](../specs/continuous-quality.md)
