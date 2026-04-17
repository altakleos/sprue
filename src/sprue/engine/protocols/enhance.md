# Wiki Enhancement Discovery

Use this prompt to discover gaps, opportunities, and improvements across the entire knowledge base. Spawns parallel agents to analyze different dimensions simultaneously.

**Trigger:** "enhance", "discover gaps", "improve wiki", "what's missing", or similar.

---

## The Prompt

```
Requires `.sprue/engine.md` in context (loaded via bootstrap). Then execute this multi-agent discovery process.

STEP 1: GATHER WIKI STATE
Run these commands to collect data for the agents:

1. Directory counts per folder
2. Top 30 most-linked pages (wikilink frequency)
3. Pages with 0-2 outbound links (isolated nodes)
4. All tags with frequency counts
5. Type distribution (entity/concept/comparison/recipe)
6. Pages exceeding max_words from instance/config.yaml (split candidates)
7. All broken wikilinks
8. Placement signals — run `python3 .sprue/scripts/build-index.py` first, then
   `python3 .sprue/scripts/placement-signals.py --json > /tmp/signals.json`.
   Include the `summary` block plus the top 10 outliers, high-entropy dirs, and
   subdir proposals in the agent brief. Signals are advisory; the LLM decides
   what to act on per `.sprue/protocols/compile.md:104-113` placement judgment.

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

Present the plan. STOP. Wait for human approval before executing anything.

EXECUTION RULES:
- After approval, execute fixes to existing pages (wikilinks, sections, quality improvements)
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
