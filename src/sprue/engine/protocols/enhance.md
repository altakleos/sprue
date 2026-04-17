# Wiki Enhancement Discovery

Use this prompt to discover gaps, opportunities, and improvements across the entire knowledge base. Spawns parallel agents to analyze different dimensions simultaneously.

**Trigger:** "enhance", "discover gaps", "improve wiki", "what's missing", or similar.

---

## The Prompt

```
Requires `.sprue/engine.md` in context (loaded via bootstrap). Then execute this multi-agent discovery process.

STEP 1: GATHER WIKI STATE
Run `python3 .sprue/scripts/build-index.py` to ensure the manifest is current.
Then read the structured data — do NOT run raw grep/awk/sed commands:

1. Read `wiki/.index/manifest.yaml` — contains per-page metadata: slug, type,
   facets, directory, links_to, sections, summary, confidence, decay_tier.
2. Read `wiki/.index/by-type.yaml` — type distribution.
3. Derive from the manifest:
   - Inbound link counts: for each slug, count how many other pages' `links_to`
     include it. Flag pages with 0–2 inbound links as isolated.
   - Outbound link counts: `links_to` length per page. Flag pages with 0–2.
   - Broken wikilinks: for each page's `links_to`, check if the target exists
     as a manifest key. Report any that don't resolve.
   - Pages exceeding `config.size_profiles.<profile>.max_words` (split candidates).
   - Tag/facet frequency: aggregate facet values across all pages.
4. Run `python3 .sprue/scripts/placement-signals.py --json > /tmp/signals.json`.
   Include the `summary` block plus the top 10 outliers, high-entropy dirs, and
   subdir proposals in the agent brief. Signals are advisory; the LLM decides
   what to act on per `.sprue/protocols/compile.md:104-113` placement judgment.

Present a concise stats summary to the user (not the raw commands):

```
📊 Wiki state: N pages across M directories
   Types: ... | Graph: N isolated, N broken links, avg N.N links/page
   Signals: N placement outliers (details below)
```

STEP 2: SPAWN PARALLEL AGENTS

Read `instance/config.yaml` `enhance.agents` for the list of agents to spawn.
Each agent entry has a `name` and `focus` — use the focus as the agent's prompt.

Give each agent the wiki stats from Step 1 plus the wiki overview content.

**CRITICAL: All agents are READ-ONLY. They must NOT create, modify, or delete
any files. They analyze and report only. All changes happen after the human
approves the synthesized plan.**

For each agent: use its `focus` from config.yaml as the analysis directive.
Read `instance/identity.md` for audience and voice context.
Output: a ranked list of findings with specific page names and actions.

STEP 3: SYNTHESIZE
After all agents return, synthesize their findings into a single prioritized plan:

| Priority | Action | Type | Source Agent |
|----------|--------|------|-------------|
| P0 | ... | fix/new/update | Agent N |

Group into:
- **Immediate fixes** (broken links, isolated pages, quality issues)
- **High-value new content** (pages that would be used weekly)
- **Medium-value new content** (pages that would be used monthly)
- **Structural improvements** (reorganization, hub pages)

Present the plan. Apply risk-tiered execution per `config.approval.*`:

**When `config.approval.cross_links` is `auto` (default):**
Apply cross-link additions directly. Do NOT present them for approval.
Do NOT ask "approve?". Write the wikilinks, then report what changed:
```
✓ Applied 4 cross-links:
  demystifying-feline-behavior.md → added [[cat-behaviour-myths]]
  multi-cat-household-setup.md    → added [[introducing-a-new-cat]]
  ...
```

**When `config.approval.cross_links` is `ask`:**
Present cross-link additions in the plan table. Wait for approval.
Accept: `all`, specific item numbers, or `none`.

Same pattern for `config.approval.broken_link_fixes`.

**Always require approval (regardless of config):**
- New-page proposals (`config.approval.new_pages`)
- Content modifications (`config.approval.content_changes`)
- Structural changes (`config.approval.structural_changes`)

For items requiring approval, present the plan table and STOP.
Accept: `all`, specific item numbers, or `none`.

EXECUTION RULES:
- After approval, execute approved fixes to existing pages
- For NEW pages needed: flag them — "New page needed: [topic]. Run import + compile."
- Enhance is a quality engine, not a creation engine. It fixes what exists.
- Update index and log after every 5 pages
- Commit after each tier of changes
```

---

## Step 4: Persist New-Page Gaps

After the human approves the synthesized plan and fixes are executed, persist all approved "New page needed" items to `instance/state/enhancements.yaml`. These are the findings enhance cannot act on — they're handoffs to `expand`.

Only persist items from the **High-value new content** and **Medium-value new content** tiers. Immediate fixes and structural improvements are executed by enhance directly.

Append to `instance/state/enhancements.yaml`:
```yaml
- run_at: "<ISO8601>"
  scope: "<full | directory-name>"
  pages_analyzed: N
  manifest_hash: sha256:<hash8>
  findings:
    - topic: "<slug>"
      source_agent: "<agent name>"
      priority: P0|P1|P2|P3
      rationale: "<one sentence — why this page is needed>"
      related_pages: [<existing slugs that reference or would link to this>]
      suggested_type: "<page type from .sprue/defaults.yaml → page_types:>"
      suggested_dir: "<directory name>"
      status: pending
```

Output after persisting:
```
📝 N new-page gaps saved to instance/state/enhancements.yaml:
 #  Topic                     Source Agent         Priority
 1  grpc-load-balancing       Graph Analyst        P1 (high-value)
 2  kafka-exactly-once        Content Gap Analyst  P1 (high-value)
 3  sqs-dlq-patterns          Content Gap Analyst  P2 (medium-value)

These will appear in your next `expand` run. View anytime: `status --pending`
```

Append to `memory/log.jsonl`.
