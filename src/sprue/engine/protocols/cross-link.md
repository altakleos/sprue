# Cross-Link: Wiki Graph Connectivity

Scan wiki pages for missing [[wikilinks]] and add them to strengthen the knowledge graph. Balances link density (every connection helps navigation) with readability (link soup helps nobody).

**Trigger:** "cross-link", "add links", "link audit", "fix links", "connect pages", or similar.

---

## Modes

- `cross-link` — full dry-run scan of all pages, report proposed changes
- `cross-link apply` — apply approved changes
- `cross-link <page-slug>` — scan a single page (both directions: outbound from page + inbound from other pages mentioning it)
- `cross-link cleanup` — find and report rule violations (double-links, links in code blocks, dead links)

**Default is always dry-run.** Never modify files without explicit `apply` instruction.

---

## The Prompt

```
Requires `.sprue/engine.md` in context (loaded via bootstrap). Then execute this cross-linking process.

═══════════════════════════════════════════════════════════
PHASE 1: BUILD ALIAS REGISTRY
═══════════════════════════════════════════════════════════

Crawl all wiki pages. Build a mapping of terms → page slugs:

1. Every page filename (without .md) is a linkable term
2. Load editorial overrides from `instance/config.yaml` `overrides` section — these are terms where this KB uses a different name than the common one. For universal abbreviations (k8s→kubernetes, tf→terraform), the LLM resolves without config.

3. Scan for auto-detected aliases: terms appearing `config.cross_link.alias_mention_threshold`+ times across
   the wiki that match an existing page name (case-insensitive).
   Add to registry and flag as `new_aliases_detected` in output.

═══════════════════════════════════════════════════════════
PHASE 2: SCAN PAGES
═══════════════════════════════════════════════════════════

For each wiki page (batch 20 pages at a time):

1. Read the full page content
2. Find all terms from the alias registry that appear in the page
   body but are NOT already wikilinked
3. For each match, evaluate against the linking rules (below)
4. Record proposed links that pass all rules

Process all pages. Between batches, output progress.

═══════════════════════════════════════════════════════════
LINKING RULES
═══════════════════════════════════════════════════════════

### LINK when ALL of these are true:

✅ A wiki page exists for the target term
✅ It's the FIRST meaningful mention in the page
   (not necessarily first occurrence — skip passing mentions
   in introductory clauses; link at the substantive discussion)
✅ The mention is in PROSE (sentences, paragraphs)
✅ The reader would plausibly want to navigate to the target page
   (the "would I click this?" test)
✅ The page is not already at the link budget cap

### NEVER LINK:

❌ Inside fenced code blocks (```...```) or inline code (`...`)
❌ Inside frontmatter (---...---)
❌ Inside headings (# ## ###) — links in headings break some renderers
❌ The same term twice on the same page (first mention only)
❌ Self-links (page linking to itself)
❌ Inside comparison tables where >`config.cross_link.table_link_cell_threshold` of cells would be links
   → Instead, ensure the prose ABOVE the table links the key terms
❌ Passing mentions in lists of examples
   ("tools like Terraform, Ansible, and Pulumi" — don't link all three
   unless the page is specifically about IaC)
❌ Terms the target audience (see `instance/identity.md`) obviously knows and wouldn't click
   — unless the wiki has a dedicated deep-dive page that adds non-obvious value

### LINK BUDGET:

- Soft guideline: ~1 internal link per `config.cross_link.words_per_link` words of prose
- Hard cap: `config.cross_link.max_links_per_page` internal links per page (excluding See Also section)
- If a page exceeds budget, prioritize by:
  1. Terms the page DEPENDS on (prerequisites, building blocks)
  2. Terms the page DEFINES or deeply discusses
  3. Related-but-optional connections (move to See Also)

### AMBIGUITY RULES:

- If a term could map to multiple pages, check surrounding context
  (paragraph topic, page tags, directory) to disambiguate
- If still ambiguous, flag as AMBIGUOUS in output — do not link
- "container" → check context: Docker/OCI context → [[docker]],
  LXC context → [[lxc]], K8s context → [[kubernetes]]
- "Redis" → [[valkey]] (the wiki uses Valkey as the Redis fork)

### ALIAS LINKING:

- When linking an alias, preserve the author's original text:
  `[[postgresql|PG]]` not rewriting "PG" to "PostgreSQL"
- For abbreviations: `[[kubernetes|K8s]]`

═══════════════════════════════════════════════════════════
PHASE 3: REPORT (DRY RUN)
═══════════════════════════════════════════════════════════

Output a structured report:

### Per-Page Changes

For each page with proposed changes:

**wiki/<dir>/<page>.md** (3 links to add)
| # | Term | Target | Context (before → after) |
|---|------|--------|-------------------------|
| 1 | <ExactName> | [[exact-slug]] | "...mentions ExactName..." → "...mentions [[exact-slug\|ExactName]]..." |
| 2 | <Synonym> | [[canonical-slug]] | "...uses Synonym..." → "...uses [[canonical-slug\|Synonym]]..." |
| 3 | <SubTopic> | [[broader-concept]] | "...applies SubTopic..." → "...applies [[broader-concept\|SubTopic]]..." |

### Summary Report

```
Pages scanned:     217
Pages with changes: 45
Total links to add: 128
Ambiguous (flagged): 7
Pages at budget:    3
New aliases found:  4

Top targets (most inbound links to add):
  postgresql: +12
  kubernetes: +9
  kafka: +8
  ...

Orphan pages (0 inbound links): [list]
Hub pages (>20 inbound links): [list]
```

═══════════════════════════════════════════════════════════
PHASE 4: EXECUTE (only after "apply" instruction)
═══════════════════════════════════════════════════════════

STOP after Phase 3. Present the report. Wait for approval.
Accept: "apply", "apply all", specific page names, or "abort".

After approval:
1. Apply changes using str_replace (surgical, one link at a time)
2. Never rewrite prose — only wrap existing terms in [[wikilinks]]
3. Set reviewed: false on modified pages
4. After every 10 pages, output progress
5. Update memory/log.jsonl:

   ## [YYYY-MM-DD] cross-link | Wiki Graph Connectivity
   Scanned N pages. Added M wikilinks across K pages.
   Top targets: [[postgresql]] (+12), [[kubernetes]] (+9), ...

═══════════════════════════════════════════════════════════
SINGLE-PAGE MODE (for new page maintenance)
═══════════════════════════════════════════════════════════

When triggered with a page slug (e.g., "cross-link kafka"):

1. OUTBOUND: Scan the target page for unlinkable terms → propose links
2. INBOUND: Scan ALL other pages for mentions of the target page's
   name/aliases that aren't linked → propose links TO the target

This is the maintenance mode — run after creating a new page to
weave it into the existing graph without a full wiki scan.

═══════════════════════════════════════════════════════════
CLEANUP MODE
═══════════════════════════════════════════════════════════

When triggered with "cross-link cleanup":

1. Find double-links (same target linked twice on one page)
2. Find links inside code blocks (rendering artifacts)
3. Find dead links (target page doesn't exist)
4. Find self-links
5. Report all violations with page, line, and proposed fix
```

---

## Design Rationale

This prompt synthesizes three perspectives:

- **From the maximalist:** Build a comprehensive alias registry so no valid link is missed. Scan systematically. Automated scanning is the only sustainable maintenance strategy at 200+ pages.
- **From the conservative:** First-mention-only rule. Never link in code blocks or comparison tables. The "would I click this?" test. Budget cap prevents link soup. Default to not linking when ambiguous.
- **From the pragmatist:** Batched processing for scale. Dry-run default for safety. Single-page mode for maintenance. Structured output for human review. Budget system forces prioritization.
