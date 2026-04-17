# Compile Protocol

*Requires `AGENTS.md` and `sprue/engine.md` in context (loaded via bootstrap).*

**Trigger:** "compile", "process", "build pages", or `status` showing uncompiled items.

## Role

Transform raw content into wiki knowledge. Read uncompiled raw files, apply a compilation strategy, write wiki pages with full frontmatter and section contracts, tag, link, verify, and index.

---

## Step 1: Derive the compile queue

Read `instance/state/compilations.yaml`. Scan all `raw/**/*.md` files. A raw file needs compiling if:
- No entry in `compilations.yaml` matches its path AND content hash
- It's not listed in `raw/.skip` (user-dropped items)

Present the queue:

```
⚙️  Compile queue: N sources

 #  Source                          Type      Words   Imported
 1  jepsen-kafka-3-a3f8c2          article   4,200   2h ago
 2  cell-architectures-7b2e1f       article   2,800   1h ago
 3  raft-revisited-c4d901           paper     8,100   45m ago
```

If the user specified items (`compile 1,3` or `compile raw/specific-file.md`), filter to those.

If the queue is empty: `✅ Nothing to compile. All raw files are up to date.`

---

## Step 2: Read pipeline configuration

Read `sprue/schemas/pipeline.yaml` (if it exists). Apply profile if specified (`--profile <name>`). Apply any CLI overrides. Report effective config:

```
⚙️  Compiling N sources (profile: <name>, depth: <depth>, strategy: <strategy>)
```

If no config exists, use defaults: `strategy: wiki_page`, `depth: standard`, `diagrams: true`.

---

## Step 3: Classify (batch-aware)

Read ALL pending raw files first. For each, determine:
- What wiki pages it should produce (new page, update existing, or skip)
- Whether multiple raw files cover the same topic (merge into one page)

Apply the same classification tiers as the original ingest protocol:

### ✅ Auto — execute without asking
Named technology/tool/service, well-known pattern, clear fit, enough substance.

### ❓ Ask — present for approval
Outside current domains, unclear page vs section, uncertain quality, significant overlap.

### ⚠️ Conflict — always present, always wait
Source contradicts existing wiki content. State both positions.

### ⏭️ Skip — already covered, no new info

Present the plan:

```
[1/5] <Source title A>
      ✅ Auto: update wiki/<dir>/<existing-page>.md (add new findings)
      ✅ Auto: create wiki/<dir>/<new-page>.md

[2/5] <Source title B>
      ✅ Auto: create wiki/<dir>/<new-page-2>.md

[3/5] <Source title C — overlaps existing>
      ❓ Ask: create wiki/<dir>/<duplicate-candidate>.md? (source-summary — mostly confirms existing [[existing-page]])
      ✅ Auto: update wiki/<dir>/<existing-page>.md (add specific numbers)
```

If everything is ✅ Auto, proceed without pausing.
If there are ❓ or ⚠️ items, pause for approval. Accept: `go`, `y`, `3,5`, `all except 4`, `abort`.

---

## Step 4: Execute

For each approved item, in order:

### New pages (🆕 Create)

1. Read the raw file's entry from `instance/state/imports.yaml` (title and content_type for context)
2. Read the raw file content in full
3. Classify: determine domain, topic, page type, and wiki placement (this is COMPILE's primary classification job — IMPORT only detected format)
4. Read `sprue/prompts/<strategy>.md` for the compilation prompt template (or use default wiki_page strategy)
5. Read the wiki manifest for context (existing pages, topic values, domain values)
6. **Assign facets** — read `sprue/defaults.yaml` → `facets:` for the list of facets, their descriptions, and guardrails. For each facet:
   a. Extract all existing values for that facet from the manifest — this IS the vocabulary.
   b. Check `instance/config.yaml` overrides — if your candidate has an editorial override, use it.
   c. Compare your candidate against existing manifest values: resolve abbreviations, normalize variants (plurals, hyphenation) to match existing forms.
   d. Respect per-facet granularity from `sprue/defaults.yaml` → `facets:` — conservative facets (those with `creation_threshold`) strongly prefer reusing existing values. Liberal facets allow free creation with deduplication.

7. **Place the page in a wiki directory:**
   a. Read `wiki/.index/manifest.yaml`. Group existing pages by `dir` to understand what each directory contains — the pages ARE the scope. The set of directories is whatever the manifest currently shows; do not assume a fixed list.
   b. Pick the directory matching the page's PRIMARY topic (the first `domain` value, then a `topic` keyword if more specific). Cross-domain concepts go to the directory whose existing pages are most about cross-cutting concepts in this KB; if none such exists yet, the closest topical fit wins.
   c. Create a new directory (or subdirectory) only when ALL of these hold:
      - The candidate cluster has a clear identity — a single named entity, or a single page-type, that distinguishes it from sibling content.
      - Without the new directory, the parent's manifest is hard to scan when placing future pages (a sub-cluster would dominate searches against the parent).
      - The cluster will keep growing — you can name `config.entity.new_dir_adjacency_min`+ adjacent pages that would naturally land there next.

      When in doubt, stay flat. Sparse directories cost more navigation than slightly-oversized flat ones. The same criteria apply recursively for subdirectories.
   d. The directory is a shelf, not a classification — facets carry the fine-grained tagging.
8. Generate the wiki page following sprue/engine.md conventions:
   - Full frontmatter per `sprue/engine.md` schema. Assign:
     - `type`, facet fields from `sprue/defaults.yaml` → `facets:`, `decay_tier`, `risk_tier`, `summary`, `author: llm` per type contract and content.
     - `confidence: medium` (default) for LLM-authored pages. Use `confidence: low` only when the page itself is explicitly speculative or opinion-based. **Never `high`** — `high` is reserved for pages that `sprue/protocols/verify.md` has fact-checked against authoritative sources. Writing `high` at compile time is a protocol violation (see `sprue/engine.md` Confidence Invariant); it is caught by `memory/rules.yaml` but should not be written in the first place.
     - `last_verified: null` — compile does not verify; only `sprue/protocols/verify.md` sets this.
     - **Provenance**: set `provenance: sourced` when compiling FROM a raw file. Set `provenance: synthesized` when creating a page with no raw source (e.g., via expand gap-filling or enhance with no imported material). If the page merges raw sources with LLM synthesis, use `sourced` — the raw source anchors the provenance; LLM synthesis is the compilation, not the origin.
     - **Sources**: for `provenance: sourced` pages, populate a `sources` list in frontmatter linking the page to its raw file(s) and original URLs. Look up the raw file path from the compile queue item and the source URL from `instance/state/imports.yaml`:
       ```yaml
       sources:
         - raw: raw/articles/kafka-complete-guide-clynt-2026-04-12-7f934cb2.md
           url: https://clynt.com/blog/kafka-complete-guide
       ```
       For `provenance: synthesized` pages, omit the `sources` field or write `sources: []`.
   - Section structure per page type contract (read `sprue/defaults.yaml` → `page_types:`)
   - For `entity` type pages: populate `## Attributes` and `## Relationships`:
     - **Attributes**: "Kind" is required (must match `instance/entity-types.yaml` registry, human-readable form). Add `config.entity.min_attributes`–`config.entity.max_attributes` other attributes as applicable: Default Port, Language, License, Managed Offerings, etc. Omit attributes that are unknown or not applicable. Format: `- **Key**: Value`
     - **Relationships**: Read `instance/entity-types.yaml` `relationship_types` for allowed types. Use display names (e.g., "Competes with", "Integrates with"). Use `[[wikilinks]]` for targets that have wiki pages. Include `config.entity.min_relationships`–`config.entity.max_relationships` relationship types per entity. Format: `- **Display Name**: [[target1]], [[target2]]`
     - **Entity type registration**: If this entity's topic slug is not in `instance/entity-types.yaml` → `entities`, append the new entry. Read existing entity types to stay consistent (reuse existing types when possible, only create a new type when no existing type fits).
   - Depth and voice per `instance/identity.md`
   - Outbound `[[wikilinks]]` to existing pages
   - Mermaid diagram if the topic involves a flow/lifecycle/decision (and `diagrams: true` in config)
9. Write to `wiki/<directory>/<slug>.md`
10. Run `bash sprue/verify.sh --file <path>`. Fix violations before proceeding.
11. Run cross-link single-page mode: scan existing pages for inbound links to the new page (per `sprue/protocols/cross-link.md` rules)

### Existing pages (🔄 Update)

Follow the surgical merge protocol:
1. Read the existing page in full
2. Identify the delta — what the raw source adds
3. Add new content to the appropriate section using `str_replace`
4. NEVER remove, rephrase, or reorganize existing content
5. Run `bash sprue/verify.sh --file <path>`

### Conflicts (⚠️)

Add callout block, set `confidence: low`, wait for human review.

---

## Step 5: Update state and index

After EACH page is written successfully, append to `instance/state/compilations.yaml`:
```yaml
- raw: <raw-file-path>
  raw_hash: sha256:<hash8>
  facets:
    # One entry per facet defined in sprue/defaults.yaml → facets:
    domain: [<values>]
    topic: [<values>]
    aspect: [<values>]
  wiki: [<slugs>]   # bare slugs, not paths — filesystem location is resolved at use via `find wiki -name "<slug>.md"`
  compiled_at: "<ISO8601>"
  profile: <profile-name-or-default>
```

After every 3-5 pages, update `wiki/overview.md` and `memory/log.jsonl`.

After the last page of a run, re-run `python3 sprue/scripts/build-index.py` so the derived indexes (including `wiki/.index/by-slug-raws.yaml`, consumed by verify Phase 2a and prioritize.py) reflect the newly added slugs. The ledger at `instance/state/compilations.yaml` is append-only truth; the index is regenerable.

---

## Step 6: Completion report

```
✅ Compile complete
   Created: N pages
   Updated: M pages
   Skipped: K (outside KB scope)
   Conflicts flagged: J
   Cross-links added: X outbound, Y inbound
   Queue: 0 uncompiled
```

If items were skipped, show the hint:
```
   → `drop skipped` to clear skipped items from the queue
```

`drop skipped` adds all skipped raw files to `raw/.skip` so they don't reappear on the next compile. The raw files stay in `raw/` — immutable, untouched.

List each page with its path and type.

---

## Profiles

Profiles control compilation behavior. They attach to COMPILE, not IMPORT.

```
compile --profile quick       # shallow summary, no linking, no verify
compile --profile research    # deep extraction, diagrams, thorough
compile --profile reference   # source-summary page only
compile --profile claims      # extract verifiable claims
compile --profile code        # code examples only
```

Read `sprue/schemas/pipeline.yaml` for profile definitions. Read `sprue/protocols/pipeline-config.md` for the full guide.

Different sources in the same batch can use different profiles:
```
compile 1,2 --profile quick
compile 3,4 --profile research
```

---

## Recompilation

To recompile a previously compiled raw file:

```
compile --recompile wiki/<dir>/<page>.md
```

This traces back to the original raw source via `wiki/.index/by-slug-raws.yaml` (the derived slug → raw index, generated by `sprue/scripts/build-index.py`), re-reads the raw file(s), and re-runs compilation with the specified profile. The existing wiki page is replaced.

---

## Rules

- Read `memory/rules.yaml` and `memory/corrections.md` before any write
- Never modify `raw/`, `notebook/`, or `inbox/`
- Follow `sprue/protocols/granularity.md` for new-page vs section decisions
- Follow `instance/identity.md` for depth, tone, and scope (what to extract, what to strip)
- Log every change to `memory/log.jsonl`
