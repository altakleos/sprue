---
status: accepted
date: 2026-04-16
---
# ADR-0027: Sources Field in Frontmatter

## Context
The platform's source-grounded-knowledge spec requires every fact to trace to a human-produced source. The raw→wiki mapping existed in state ledgers (`instance/state/compilations.yaml`) and derived indexes (`wiki/.index/by-slug-raws.yaml`), but wiki pages themselves carried no structured source metadata. A page marked `provenance: sourced` had no machine-readable link to which raw file(s) it was compiled from or what URL those raw files came from. Source attribution existed only as narrative inline citations in page bodies — useful for humans reading the page, but not queryable or verifiable by automation.

Additionally, the compile protocol was silent on provenance: the word "provenance" did not appear in compile.md. All 535 content pages were uniformly labeled `provenance: sourced` with zero marked `synthesized`, making the distinction meaningless.

## Decision
Add a `sources` field to the frontmatter schema. For `provenance: sourced` pages, compile populates this field with a list of raw file paths and their original source URLs, looked up from `instance/state/imports.yaml`. For `provenance: synthesized` pages, the field is omitted or empty.

Add provenance to the manifest index (`build-index.py`) so agents can query pages by provenance state.

Add an explicit provenance decision rule to the compile protocol: compile from a raw file → `sourced`; create with no raw source → `synthesized`. The compile protocol now enforces the distinction rather than defaulting to uniform labeling.

An advisory validation rule (commented in `memory/rules.yaml`, to be enabled after backfill) will enforce that sourced pages have at least one entry in `sources` and that synthesized pages cannot have `confidence: high`.

## Alternatives Considered
- **Per-claim source attribution** — rejected for this phase as too ambitious. The source-authority-pipeline spec (draft) envisions per-claim tracking, but the infrastructure needed (structured claim→source mappings, query API) is extensive. Page-level sources are the pragmatic first step.
- **Store sources only in state ledgers, not frontmatter** — rejected because pages should be self-documenting. A reader (human or agent) looking at a page should be able to see its sources without cross-referencing external files. The ledger remains the source of truth; frontmatter is a denormalized convenience.
- **Immediate full enforcement** — rejected because 535 existing pages lack the `sources` field. Full enforcement would break CI until a backfill maintenance pass runs. Advisory-then-enforce is the pragmatic path.

## Consequences
New pages compiled from raw sources carry a machine-readable provenance chain: page → `sources` field → raw file path + URL. This closes the gap between the source-grounded-knowledge spec's intent and the implementation. Existing pages need a backfill maintenance pass to add `sources` fields — until then, the advisory rule surfaces the gap without blocking CI. The manifest now supports provenance-based filtering, enabling agents to prioritize sourced pages over synthesized ones for verification.

## Config Impact
New frontmatter field: `sources` (list of `{raw, url}` objects)
New manifest field: `provenance` (string: sourced | synthesized | unknown)

## Specs

- [Source-Grounded Knowledge](../specs/source-grounded-knowledge.md)
