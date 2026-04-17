# Maintenance Protocol

*Requires `AGENTS.md` and `.sprue/engine.md` in context (loaded via bootstrap).*

**Usage:** Run with a parameter: `lint` | `verify` | `rebuild-index` | `upgrade` | `reorganize` | `full`

---

## lint

### Verification Sweep (runs first)

Run `bash .sprue/verify.sh` from the repo root. This executes every `verify:` command in
`memory/rules.yaml` and reports pass/fail for each rule.

Present results before other lint findings. Fix auto-fixable violations immediately.
Present non-auto-fixable violations for approval. Then proceed with the rest of lint.

### Auto-fix (execute immediately, report after)

- **Broken wikilinks** — redirect to existing page if obvious match (e.g., `[[redis]]`→`[[valkey]]`, `[[cdk]]`→`[[aws-cdk]]`), otherwise unwrap to plain text
- **Malformed frontmatter** — add missing required fields with sensible defaults
- **Empty tags** — populate from page content and directory
- **Tag inconsistencies** — normalize to canonical form using overrides from config.yaml

### Needs approval (present report, wait)

- **Contradictions** — claims in one page that conflict with another (quote both)
- **Orphan pages** — zero inbound `[[wikilinks]]` (exclude index.md, log/, overview.md). Present list — human decides whether to add links or leave as-is.
- **Missing pages** — concepts mentioned `config.cross_link.missing_page_mention_threshold`+ times without their own page. Flag for a separate import + compile, don't create during maintenance.

### Report-only (no action)

- **Stale pages** — `confidence: low` or not modified in git for longer than `instance/config.yaml` `maintenance.stale_months`
- **Unverified critical pages** — `risk_tier: critical` with `last_verified: null`, sorted by risk tier

Format: auto-fixes first (already done), then approval items as numbered list, then report-only stats. Log all auto-fixes to `memory/log.jsonl`.

---

## rebuild-index

**Fully autonomous. No approval needed.**

1. Read every `wiki/**/*.md` file
2. Regenerate `wiki/index.md`:
   - Group pages by directory (infrastructure, data, platform, development, security, architecture)
   - Within each directory, list subdirectories separately
   - Each entry: `- [[page-name]] — summary from frontmatter`
   - Stats block at top: total pages, breakdown by directory, count of unverified critical pages
3. Run `python3 .sprue/scripts/build-index.py` to regenerate machine-readable indexes (manifest.yaml, by-tag.yaml, by-type.yaml)
4. Run `python3 .sprue/scripts/build-embeddings.py` to regenerate semantic search embeddings
5. Log the rebuild to `memory/log.jsonl`

---

## verify

**Delegates to the standalone verify operation.** Read `.sprue/protocols/verify.md` for the full protocol.

1. Run `python3 .sprue/scripts/decay.py` to check for confidence downgrades from topic staleness
2. Execute the verify protocol (default filter: `--tier critical`)
3. Check `memory/corrections.md` — ensure all active corrections are respected
4. Evaluate correction retirement (3 consecutive passes → eligible)

---

## upgrade

Scan every wiki page. Score each 0-10 against the quality bar:

- Has "When to Use / When to Avoid" (or equivalent decision guidance)
- Has "Gotchas" section with specific footguns
- Code examples are real-world, not toy snippets
- Contains quantified limits, costs, latencies, or performance numbers
- Contains `[[wikilinks]]` to related pages (minimum `config.upgrade.min_wikilinks`)
- States opinions and tradeoffs, not just descriptions
- Appropriate depth for the audience defined in `instance/identity.md`

### Auto-upgrade (execute immediately)

For pages scoring below `config.upgrade.auto_upgrade_score_threshold`, auto-fix these low-risk improvements:
- Add missing `[[wikilinks]]` to obviously related pages
- Add missing "Gotchas" section with `config.upgrade.min_gotchas`–`config.upgrade.max_gotchas` specific footguns
- Add missing "When to Use / When to Avoid" bullet points

Use str_replace for surgical edits. Never rewrite entire pages. Set `reviewed: false`.

### Needs approval

- Replacing toy examples with real-world patterns (higher risk of changing meaning)
- Adding quantified numbers that need verification (mark `[needs-verification]`)

Present auto-upgrades already done + approval items as a table. Log all changes.

---

## reorganize

**Always requires approval.**

First, emit placement signals to ground the analysis:

```
python3 .sprue/scripts/build-index.py          # ensure manifest is fresh
python3 .sprue/scripts/placement-signals.py --json > /tmp/signals.json
python3 .sprue/scripts/placement-signals.py    # human-readable copy
```

The signals are advisory — they never fail verify. Apply judgment from
`.sprue/protocols/compile.md:104-113` placement prose to each proposal.

Then analyze the full wiki structure. Produce a proposal covering:

1. **Placement outliers (S-2)** — pages whose wikilink neighbors live mostly elsewhere. For each high-fraction outlier, propose a `git mv` to its `suggested_dir` when the signal is decisive. Legitimately cross-cutting pages with spread-out neighbors should stay.
2. **Directory splits (S-3 + S-4)** — directories exceeding `navigable_max` that have a clear sub-cluster. Apply the test from `compile.md:108-112`: clear identity + parent-scanning pain + 3+ adjacent future pages. If a split candidate has no qualifying sub-cluster, leave it flat.
3. **Directory absorbs (S-3)** — sparse directories whose pages could live inside a peer.
4. **Dumping-ground coherence (S-1)** — high-entropy dirs with 3+ competing dominants. Consider whether re-placing a few outliers would lower entropy to acceptable levels.
5. **Merge candidates** — pages with >`config.upgrade.merge_overlap_threshold` content overlap (quote overlapping sections).
6. **Split candidates (page-level)** — pages exceeding their `size_profiles.<profile>.split_threshold` covering 3+ distinct subtopics.
7. **Reclassification** — pages whose `type` doesn't match their content.
8. **Missing connections** — page clusters that should cross-reference but don't.

**STOP. Wait for approval.** Then execute approved changes autonomously: `git mv` pages, merge/split, update all affected `[[wikilinks]]` across the wiki, rebuild index, log to `memory/log.jsonl`.

---

## full

Execute in order:

1. `lint` → auto-fix obvious issues, present ambiguous items
2. `verify` → extract claims, fetch sources, fix contradicted claims with evidence
3. `rebuild-index` → autonomous
4. `upgrade` → auto-upgrade low-risk items, present higher-risk items
5. **Single approval gate** → human reviews all pending items from lint + upgrade at once
6. Execute approved items
7. `reorganize` → present proposal → separate approval (structural changes are high-risk)

---

## Rules

- Read files before analyzing them. Never assume content.
- Never modify `raw/`, `notebook/`, or `inbox/`.
- Never create new pages. Flag missing pages for import + compile.
- Never delete pages unless the human explicitly asks.
- Log every change to `memory/log.jsonl` with date, operation, and summary.
- Preserve existing human-written content. Add to it; don't replace.
- When uncertain, mark claims `[needs-verification]` and set `confidence: low`.
