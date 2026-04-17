# Expand Protocol

*Requires `AGENTS.md` and `sprue/engine.md` in context (loaded via bootstrap).*

**Trigger:** "expand", "grow the wiki", "what's missing", "find gaps", or similar.

## Role

Discover knowledge gaps in the wiki and fill them by triggering IMPORTs. EXPAND is the growth engine — it analyzes what exists, identifies what's missing, researches sources, and imports them. It does NOT compile; that's a separate step.

**Key difference from enhance:** Enhance analyzes quality of *existing* content (read-only). Expand discovers and imports *new* content.

---

## Phase 1: Crawl

Build a map of what the wiki knows.

1. Read `wiki/.index/manifest.yaml` for page metadata
2. Collect all tags — build frequency table
3. Find all dangling `[[wikilinks]]` (referenced but no page exists)
4. Find unlinked mentions — technology names appearing in body text but never wikilinked
5. Map cluster edges — what each directory covers and where it stops
6. Load `instance/state/enhancements.yaml` — collect entries with `status: pending` (enhance-flagged gaps). If the file doesn't exist, skip silently.

Output a brief summary:
```
🔍 Crawling wiki... N pages, 6 directories
   Dangling links: X
   Unlinked mentions: Y
   Cluster edges identified: Z
   Enhance-flagged gaps loaded: N (from YYYY-MM-DD)
```

---

## Phase 2: Discover

Apply 6 discovery strategies. Deduplicate across strategies — Strategy 0 runs first so subsequent strategies skip topics already covered.

**Strategy 0: Enhance-flagged gaps** — topics flagged by `enhance` as needing new pages. Read from `instance/state/enhancements.yaml`, entries with `status: pending`. These are pre-validated by multi-agent quality analysis and carry high signal. Skip if the file doesn't exist or has no pending entries.

**Strategy 1: Dangling links** — topics already `[[wikilinked]]` but with no page. Highest signal. Targets queued by `sprue/protocols/resolve-relationships.md` (entries with `source: rel-link` in `instance/state/expansions.yaml`) are first-class here — their acceptance criteria are already written in the source pages; prefer them over topic-proximity gaps.

**Strategy 2: Cluster edge expansion** — for each directory, what's the next most important topic the target audience (see `instance/identity.md`) would need? Propose 2-3 per directory with justification.

**Strategy 3: Cross-reference gaps** — topics at the intersection of 2+ existing pages with no dedicated coverage (the "glue" concepts).

**Strategy 4: Online research** — search for trending technologies and concepts relevant to the KB's audience. Cross-reference against existing pages. Filter aggressively.

**Strategy 5: Recipe & comparison gaps** — clusters of 3+ related entities without a comparison page, or common integration patterns without a recipe.

### Filtering

Reject candidates that:
- Already exist in the wiki (check manifest)
- Were previously proposed and rejected (check `instance/state/expansions.yaml` and `instance/state/enhancements.yaml`)
- Fall below the audience bar defined in `instance/identity.md` (too basic, below `size_profiles.min_creation_words` of non-obvious content)
- Would drift too far from the KB's existing facet values (must share `config.expand.min_shared_facets`+ facet values with existing content)

Enhance-flagged gaps (Strategy 0) go through the same filters. If expand rejects an enhance finding, update its `status` to `filtered` in `instance/state/enhancements.yaml` with a `filter_reason`.

---

## Phase 3: Prioritize

Score each candidate on 3 dimensions:

| Dimension | Weight | Scoring |
|---|---|---|
| **Connectivity** | 40% | How many existing pages would link to/from this? |
| **Lookup frequency** | 35% | How often would the target audience look this up? |
| **Uniqueness** | 25% | Does this add knowledge beyond 5 min of Googling? |

**Enhance signal bonus:** Strategy 0 candidates receive an additive bonus of `expand.enhance_signal_bonus` (default 0.10) after base scoring. This reflects their pre-validation by quality analysis. The bonus is capped so the final score never exceeds 1.0. Strategy 0 candidates that provide `related_pages` use those for the connectivity dimension directly (more accurate than heuristic estimation).

Present the results as a ranked table with enhance-flagged gaps in a distinct section at the top:

```
 ── Enhance-flagged gaps (from enhance run YYYY-MM-DD) ────────────────────
 #   Topic                    Type        Dir             Signal              Score
 E1  grpc-load-balancing      concept     sprue/       enhance: Graph      0.91
 E2  kafka-exactly-once       concept     data/           enhance: Content    0.87

 ── Expand discoveries ────────────────────────────────────────────────────
 1   flink-checkpointing      concept     data/           dangling link       0.92
 2   kafka-streams-vs-flink   comparison  architecture/   missing comparison  0.88
 3   circuit-breaker-overhead  recipe      architecture/   conflict follow-up  0.85
 ...
 ─   ──────────────────────   ─────────   ──────────────  ──────────────────  ─────
 ×   kubernetes-basics        concept     sprue/       cluster edge        0.45  REJECTED: below audience bar
```

**STOP. Wait for approval.** Accept: `all`, `1,3,E1`, `all except E2,4`, `none`.

---

## Phase 4: Research & Present Sources

For each approved topic:

1. **Research online** — find 1-3 authoritative sources per topic. The LLM ranks source authority based on the KB identity in `instance/identity.md`. Use the web fetching methods from `sprue/protocols/query.md`.
2. If no good source is found, the agent can offer to write from its own knowledge — note `Source: LLM knowledge (no authoritative source found)`.

**Present all discovered sources in a numbered table:**

```
🔍 Researched N topics, found M candidate sources:

 #  Topic                   Source                                    Date     Words
 1  consensus-algorithms    raft.github.io/raft.pdf                   2014     12000
 2  consensus-algorithms    eli.thegreenplace.net/paxos-vs-raft       2023      2400
 3  connection-pooling      brandur.org/fragments/connection-pooling   2024      2400
 4  wal-vs-binlog           bytebase.com/blog/wal-vs-binlog           2024      3600

Import which? [all / 2,3,4 / all except 1 / none]
```

**STOP. Wait for source-level approval.** The user sees URLs, dates, and sizes before anything enters `raw/`. Accept: `all`, `2,3,4`, `all except 1`, `none`.

## Phase 5: Import Approved Sources

For each user-approved source, invoke the IMPORT protocol (`sprue/protocols/import.md`). IMPORT handles fetching, dedup, hashing, saving to `raw/`, and state updates. Expand never duplicates import's logic.

```
📥 N sources imported to raw/
   Queue: N uncompiled — run `compile` to process.
```

---

## Phase 6: Update state

Append to `instance/state/expansions.yaml`:
```yaml
- run_at: "<ISO8601>"
  scope: "<full | directory-name>"
  pages_analyzed: N
  gaps_found:
    - topic: "<name>"
      action: imported
      sources:
        - url: "<url>"
          selected: true
        - url: "<url>"
          selected: false
          reason: "<user skipped: too dense / outdated / etc>"
    - topic: "<name>"
      action: rejected
      reason: "<user's reason or auto-filter reason>"
  manifest_hash: sha256:<hash8>
```

**Update enhance state:** For each Strategy 0 candidate processed in this run, update its `status` in `instance/state/enhancements.yaml`:
- `consumed` — topic was approved and sources were imported. Set `consumed_by: "<expand run_at timestamp>"`.
- `rejected` — user rejected the topic. Set `filter_reason: "<user's reason>"`.
- `filtered` — expand's filters rejected it. Set `filter_reason: "<reason>"` (e.g., "below audience bar", "topic drift").

Append to `memory/log.jsonl`.

---

## Modes

Three automation levels. Settings in `instance/config.yaml` under `expand:`.

| Mode | Invocation | Topic gate | Source gate | Behavior |
|---|---|---|---|---|
| **manual** | `expand` | User picks | User picks | Full control. Default. |
| **semi** | `expand --semi` | User picks | LLM picks best | User steers topics, LLM handles sources. |
| **auto** | `expand --auto` | LLM picks top N | LLM picks best | Fully delegated. Post-hoc report. |

Auto is **stricter**, not looser — less oversight means tighter caps. See `instance/config.yaml` for thresholds (`max_topics`, `min_topic_score`, `sources_per_topic`).

### Mode behavior in each phase

**Phase 3 (topic approval):**
- manual / semi: STOP. Present ranked table. Wait for user selection.
- auto: LLM selects top `auto.max_topics` topics scoring ≥ `auto.min_topic_score`. No stop. Log selections.

**Phase 4 (source research + presentation):**
- manual: Research all approved topics. Present source table with metadata. STOP. Wait for user selection.
- semi: Research all approved topics. LLM picks best `semi.sources_per_topic` per topic. No stop for sources.
- auto: Research auto-selected topics. LLM picks best `auto.sources_per_topic` per topic. No stop.

**Phase 5 (import):** All modes delegate to `sprue/protocols/import.md`. No difference.

**Phase 6 (state):** All modes write to `expansions.yaml`. Entry includes `mode: manual|semi|auto`.

### Post-hoc report (semi and auto)

For modes that skip gates, show what the LLM chose — anomalies first:

```
🤖 expand --auto completed

Topics selected (3 of 8 discovered):
 ✅  flink-checkpointing       0.92  dangling link
 ✅  grpc-load-balancing       0.89  enhance-flagged (Graph Analyst)
 ✅  wal-vs-binlog             0.88  missing comparison
 ──  circuit-breaker-overhead  0.81  SKIPPED: auto cap (top 3 only)

Sources imported:
 1. flink-checkpointing  → nightlies.apache.org/flink/...  (2024, 3200w)
 2. grpc-load-balancing  → grpc.io/blog/grpc-lb             (2023, 1800w)
 3. wal-vs-binlog        → brandur.org/fragments/wal        (2024, 2400w)

📥 3 sources imported. Queue: 3 uncompiled.
```

### Other flags

- `expand data/` — focus on one directory
- `expand --limit 5` — cap at 5 topic discoveries

---

## Constraints

- Maximum topics and imports per run: see `instance/config.yaml` `expand:` section.
- EXPAND never compiles. It only imports. The user runs `compile` when ready.
- EXPAND never modifies existing wiki pages.
- Topic drift detection: every candidate must share `config.expand.min_shared_facets`+ facet values with the seed content or existing wiki pages.
- Don't re-propose topics rejected in previous runs (check `instance/state/expansions.yaml` and `instance/state/enhancements.yaml`).

---

## How it differs from other operations

| Operation | Discovers gaps? | Creates raw files? | Creates wiki pages? | Researches online? | Writes to enhancements.yaml? |
|---|---|---|---|---|---|
| **Import** | No | Yes | No | Only to fetch the given URL | No |
| **Compile** | No | No | Yes | No | No |
| **Expand** | Yes | Yes (via Import) | No | Yes | Reads + updates status |
| **Enhance** | Yes (quality) | No | No | No | Writes pending findings |
| **Maintain** | Flags missing pages | No | No | No | No |
