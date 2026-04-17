---
status: accepted
date: 2026-04-16
---
# ADR-0028: Provenance Enforcement Model

## Context
With the sources field added to frontmatter (ADR-0027), the platform needed a validation strategy. The challenge: 535 existing pages lack the `sources` field. A validation rule requiring it would immediately flag all existing pages as violations, breaking the CI pipeline until a backfill maintenance pass completes — a pass that could take significant effort across hundreds of pages.

The platform uses `memory/rules.yaml` for executable verification rules run by `verify.py`. Every rule that produces output is counted as a failure. There is no built-in "advisory" or "warning" severity — rules are binary pass/fail.

## Decision
Adopt an advisory-then-enforce model for provenance validation. The rule is written and added to `memory/rules.yaml` as a commented block with clear documentation that it should be uncommented after the backfill maintenance pass. The compile protocol enforces provenance and sources for all NEW pages going forward. Existing pages are addressed in a separate maintenance pass.

This creates two enforcement boundaries:
1. **Compile-time** (immediate): the protocol requires provenance decision and sources field for every new page. Violations are caught by `bash sprue/verify.sh --file <path>` during compile step 10.
2. **Whole-wiki** (deferred): the commented rule in `rules.yaml` will enforce consistency across all pages once backfill is complete.

## Alternatives Considered
- **Immediate full enforcement** — rejected because it would break CI for all 535 existing pages. The cost of backfilling sources across the entire wiki before enabling the rule is too high for a single pass.
- **New-pages-only scoping** — rejected because it creates a permanent two-tier system where old pages are never validated. The advisory model is temporary — it becomes full enforcement after backfill.
- **No validation rule at all** — rejected because the provenance distinction would remain aspirational without structural enforcement. The commented rule documents the intended end state and creates accountability for completing the backfill.

## Consequences
New pages are immediately validated for provenance consistency at compile time. The whole-wiki rule is deferred but documented, creating a clear TODO for the backfill maintenance pass. The `memory/rules.yaml` file now contains a commented advisory section — a new pattern for the platform that may be reused for other graduated rollouts. Once backfill is complete, uncommenting the rule closes the loop and provenance becomes a fully enforced invariant.
