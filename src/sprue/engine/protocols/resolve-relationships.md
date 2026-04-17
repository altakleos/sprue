# Resolve Relationships Protocol

*Requires `AGENTS.md` and `sprue/engine.md` in context (loaded via bootstrap).*

**Trigger:** "resolve relationships", "triage rel-links", "fix broken rel-links".

## Role

Triage broken wikilinks in `## Relationships` sections of entity pages. For each broken link, decide **RENAME** / **IMPORT** / **UNWRAP** / **UNCERTAIN** using `instance/identity.md` as direction. Execute renames and unwraps as page edits; route imports into the expand queue (`instance/state/expansions.yaml`); surface uncertain cases to the human.

**Key difference from `maintain lint`**: lint auto-fixes prose wikilinks with obvious renames and unwraps everything else. This protocol is judgment-heavy: every target gets per-case LLM reasoning against KB identity before a decision is proposed.

---

## Inputs

- `instance/identity.md` — scope direction. Read first; it determines what "in-scope" means.
- `instance/entity-types.yaml` — relationship-type vocabulary. `Requires`, `Managed by` are load-bearing (never UNWRAP). `Competes with`, `Alternative to`, `Integrates with`, `Implements`, `Extends`, `Part of`, `Deprecated by` are informational (UNWRAP permitted).
- `wiki/.index/manifest.yaml` — for rename-candidate matching.
- `python3 sprue/scripts/check-entity-types.py --json` — canonical input list. Exit 0 regardless of warning count; this is reporting, not a gate.

---

## Phase 1 — Discover

```
python3 sprue/scripts/check-entity-types.py --json
```

Parse. Collect records where `kind == "BROKEN_REL_LINK"`. If zero, report "no broken relationships" and exit.

Group records by `target` (unique target slug). Each group carries a list of `sources` (source page slugs) and `rel_types`. This turns N broken links into M ≤ N decisions.

Emit:
```
🔍 Discovered N broken rel-links across M unique targets.
```

---

## Phase 2 — Classify (LLM judgment, one pass per target)

For each unique target:

1. **Rename check.** Search `manifest.yaml` for a near-match slug (substring, Levenshtein ≤ 2, or known alias). If a candidate exists AND refers to the same thing (LLM semantic check using the target name + source page context), classify **RENAME** with high confidence.

2. **Direction read.** If no rename applies, read each source page's `## Relationships` section and relevant surrounding context. Read `instance/identity.md`.

3. **Decision.** Apply judgment:
   - **IMPORT** — target is clearly in-scope for the KB identity (major platform, load-bearing peer of a documented entity, foundational concept). OR any incoming `rel_type` is load-bearing (`Requires`, `Managed by`) — load-bearing relationships must resolve.
   - **UNWRAP** — target is out-of-scope (specific SaaS the identity doesn't cover, one-off mention, subsumed by an existing broader page). All incoming `rel_types` must be informational.
   - **UNCERTAIN** — decision needs context the LLM lacks (author's current tooling, seasonal priorities, ambiguous identity fit).

4. **Confidence and rationale.** Score 0.0–1.0. Write a one-line rationale grounded in identity + source context.

**Heuristics** (guidance, not gates):
- Major hyperscalers, top-tier OSS peers of documented entities, foundational concepts → default IMPORT unless identity excludes.
- Specific SaaS/products of a category the KB doesn't document broadly → default UNWRAP.
- `demand ≥ 2` distinct sources → tilt toward IMPORT (multiple entities independently identified the gap). Not a threshold; a tilt.
- Never UNWRAP a load-bearing `rel_type` — the relationship claim cannot be honored without the target.

---

## Phase 3 — Propose

Present one table:

```
📋 Broken relationships to resolve (N unique targets, M total links):

 #  Target              Demand  Rel Types           Decision    Conf   Rationale
 1  [[calico]]          1       Competes with       IMPORT      0.85   Major K8s CNI peer of cilium
 2  [[gpt-4]]           1       Competes with       UNWRAP      0.90   Specific model, KB has no LLM spine
 3  [[memcached]]       1       Alternative to      RENAME      0.95   → [[memcached-vs-redis]]
 4  [[vmware]]          1       Competes with       UNCERTAIN   0.55   Staff SDE may or may not touch VMware
 ...

Summary: R renames, I imports, U unwraps, X uncertain (of M total).
```

---

## Phase 4 — Approve

STOP. Wait for human input. Accept:
- `all` — execute all RENAME + IMPORT + UNWRAP rows (UNCERTAIN still defers)
- `1,3,5` or `1-10` — specific rows
- `all except 4,7` — exclusion
- `approve imports` / `approve renames` / `approve unwraps` — by bucket
- `reclassify N as X` — override a row before executing
- `none` — abort, no changes

---

## Phase 5 — Execute

Process approved rows:

- **RENAME**: for each source page in the row's `sources`, edit the page and replace `[[old_target]]` with `[[new_target]]` **inside the `## Relationships` section only**. Touch no other content.

- **UNWRAP**: for each source page in the row's `sources`, edit the page and replace `[[target]]` with a plain-text display form (target slug titlecased, spaces for hyphens — e.g., `[[gpt-4]]` → `GPT-4`, `[[delta-lake]]` → `Delta Lake`). Preserve the bullet entirely; do not delete the relationship line. If the bullet had only this target as its sole link AND the relationship becomes content-free, leave the display text in place — it still conveys the assertion.

- **IMPORT**: append ONE entry per target to `instance/state/expansions.yaml`:
  ```yaml
  - queued_at: <ISO8601>
    target: <slug>
    source: rel-link
    sources: [<source-page-slugs>]
    rel_types: [<rel-types>]
    rationale: "<Phase 2 one-liner>"
    disposition: pending
  ```
  Do NOT invoke `sprue/protocols/import.md` inline. The queue is the hand-off to `expand`.

- **UNCERTAIN**: no side effects. List them in the completion report for conversation follow-up.

After all edits, for every touched page run `bash sprue/verify.sh --file <path>` to confirm no regressions.

---

## Phase 6 — Log

Append one entry to `memory/log.jsonl`:

```
{"ts":"<ISO8601>","op":"resolve-relationships","summary":"R renames, I imports queued, U unwraps, X uncertain","pages_touched":N}
```

If the batch affected 5+ pages OR queued 5+ imports, also append a short line to `memory/evolution-log.md` for audit.

---

## Constraints

- **Never UNWRAP a load-bearing `rel_type`** (`Requires`, `Managed by`). If the LLM's only sensible classification for a load-bearing rel is UNWRAP, that's a signal the relationship itself is wrong — classify as UNCERTAIN and surface.
- **Never edit pages outside the `## Relationships` section** during this operation.
- **Never import inline.** Imports always flow through `instance/state/expansions.yaml` → `expand`.
- **If `--json` parse fails**, abort Phase 1 and surface the error. Do not fall back to parsing non-quiet text output.
- **One invocation, one batch.** Do not persist classifications between invocations; each run classifies from current wiki state.
