---
status: accepted
date: 2026-04-16
---
# ADR-0030: Rename platform/ to sprue/, Split Contributor Docs to docs/

## Context

The platform was being prepared for extraction as a standalone pip package called Sprue. Two problems existed: (1) the directory name `platform/` was generic and didn't match the product name, creating a mapping gap between the source repo and the installed package; (2) contributor-facing artifacts (ADRs, specs, design docs, plans) were mixed into `platform/` alongside runtime files (protocols, scripts, config), meaning `sprue init` would need exclusion logic to avoid copying contributor docs into user instances.

## Decision

Rename `platform/` to `sprue/` and move contributor docs to a top-level `docs/` directory. The directory boundary becomes the shipping boundary: everything in `sprue/` ships to users, everything in `docs/` stays in the source repo. No exclusion logic needed.

The structure:
- `sprue/` — engine runtime (protocols, scripts, defaults.yaml, prompts, engine.md)
- `docs/` — contributor knowledge (decisions/, specs/, design/, plans/, development-process.md)

## Alternatives Considered

- **Keep `platform/` name, add exclusion list** — rejected because exclusion lists are fragile and grow as contributor docs expand
- **Rename to `src/`** — rejected because the content is a mix of markdown, Python, and YAML, not a standard Python source tree
- **Rename to `engine/`** — rejected because the directory contains more than the engine (scripts, prompts, schemas)

## Consequences

`sprue init` can copy the entire `sprue/` directory without filtering. The product name appears consistently: `sprue/` in source, `.sprue/` in instances, `sprue` on PyPI. 72 files required path reference updates. All 19 verification rules pass after migration.

## Config Impact

`sprue/defaults.yaml` — path unchanged relative to engine root. `sprue/scripts/config.py` — ROOT resolution unchanged (same directory depth).
