# Page Granularity Rules

Governs when to create a new page vs add a section, and when to split or merge existing pages. Applies during **compile**, **maintain**, and **enhance** operations.

*Requires `.sprue/engine.md` in context (loaded via bootstrap).* Read `.sprue/defaults.yaml` → `page_types:` for each type's `size_profile`. Read `instance/config.yaml` `size_profiles` for the limits.

---

## Governing Principle

**A page earns its existence by being independently useful.** If you can't open a page cold and get value from it without immediately clicking to another page, it shouldn't exist standalone.

Tiebreaker: **"Would I merge this back in six months?"** If probably yes, write a section now.

---

## Hard Rules

| Rule | Threshold | Action |
|---|---|---|
| Minimum page size | `size_profiles.<profile>.min_words` | Never create a page below this. Inline as a section. |
| Maximum page size | `size_profiles.<profile>.max_words` | Must split (standard/expansive) or tighten prose (compact). For compact types, word count excludes code blocks and tables. |
| Compact types never split | Types with `size_profile: compact` in `.sprue/defaults.yaml` → `page_types:` | If too long, tighten prose or reclassify the page type. Do not split. |
| Inbound links | ≥1 wikilink from another page | Every page must be reachable. |
| Link maintenance | All operations | Splits and merges must update all inbound wikilinks. |

---

## Split Criteria

**Require 2+ signals firing simultaneously** (except the hard ceiling from `max_words`). **Skip entirely for compact types.**

| Signal | Threshold | How to Check |
|---|---|---|
| Word count | Exceeds `split_threshold` for the page's `size_profile` | Count body text excluding frontmatter and code blocks |
| H2 section count | Above `config.granularity.max_h2_split_signal` | Count `##` headings |
| Independent section references | `config.granularity.min_sections_with_external_links`+ H2 sections attracting links from other pages, OR `config.granularity.min_section_references`+ `[[page#section]]` references | Check for `#` in inbound wikilinks |
| Different page type | A section would be a different `type` than its parent | e.g., parent is `entity`, section is `concept` |

### The Reusability Test

The strongest split signal: **if a concept is referenced from `config.granularity.reusability_context_threshold`+ unrelated contexts, it deserves its own page.**

Examples:
- Consistent hashing → referenced from distributed-cache, database-scaling, load-balancing → standalone page (tech)
- Maillard reaction → referenced from searing, roasting, bread-baking → standalone page (cooking)
- Compound interest → referenced from savings, mortgages, retirement planning → standalone page (finance)

Counter-examples (stays as a section):
- Goroutines without Go, ownership without Rust (tech)
- Proofing without sourdough, margin calls without short selling (cooking, finance)
- The concept doesn't exist independently of the parent
- Splitting would create a page under `min_words`

### Type Reclassification

If a page consistently exceeds its profile's limits, consider whether the page type is still correct before splitting. A `recipe` that keeps accumulating context might really be a `pattern`. A `reference` that grows narrative might be a `concept`. Reclassifying changes the `size_profile`, which changes the thresholds.

---

## Merge Criteria

**Require 2+ signals firing simultaneously.**

**Never merge:** hub/index pages, pages tagged `entry-point` or `stub`, comparison pages, or pages whose `size_profile` is `compact` (short by design).

| Signal | Threshold | How to Check |
|---|---|---|
| Word count | Below `size_profiles.min_creation_words` (and not a compact type) | Count body text |
| Co-link ratio | Above `config.granularity.co_link_merge_ratio` — pages are almost always linked together | Check inbound link patterns |
| Weak inbound links | Zero links, or only reached via one parent page | Grep for `[[page-name]]` across wiki |

---

## Decision Flowcharts

### A. Compile (new content)

```
Is this a named subject?
├── NO → Inline as a section in the nearest parent page. Done.
└── YES → Does an existing page already cover this?
    ├── YES → Would adding this exceed the page's split_threshold?
    │   ├── NO → Expand the existing page. Done.
    │   └── YES → Does the new content pass the reusability test?
    │       ├── YES → New page.
    │       └── NO → Expand anyway, tighten prose. Flag for review if exceeds max_words.
    └── NO → Can you write size_profiles.min_creation_words+ words of non-obvious content at the depth from instance/identity.md?
        ├── NO → Inline as a section in the nearest parent. Done.
        └── YES → New page. Ensure ≥1 inbound wikilink.
```

### B. Maintain (periodic health check)

```
For each page:
1. Check cooldown (skip if tagged granularity-reviewed within instance/config.yaml maintenance.granularity_cooldown_days)
2. If compact type → skip split evaluation entirely
3. Run SPLIT check: count signals from split criteria. 2+ signals OR exceeds max_words → propose split
4. Run MERGE check: count signals from merge criteria. 2+ signals → propose merge
5. Apply reader-benefit test: "Does this change help someone find/use knowledge?" NO → skip
6. Tag page: granularity-reviewed: YYYY-MM-DD
```

During enhance: if the target page now exceeds its `split_threshold`, run the maintain split check (B, step 3).

---

## Busywork Prevention

- **Hysteresis bands.** Soft thresholds need a second signal to trigger action. A page 1 word over `split_threshold` with no other signals stays as-is.
- **Cooldown.** Pages reviewed for granularity are skipped for `maintenance.granularity_cooldown_days` (see `instance/config.yaml`).
- **Batch processing.** During maintain, collect all split/merge proposals first, present as a table, execute after approval. Don't cascade — one split shouldn't trigger re-evaluation of the resulting pages in the same session. Tag resulting pages as `granularity-reviewed`.
