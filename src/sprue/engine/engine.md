# KB Engine

Reusable platform rules for any LLM-maintained knowledge base. This file is the same for every KB that uses this engine. Instance-specific configuration lives in `AGENTS.md`.

> **Layering note:** This file is the LLM's operational reference — it restates product intent and architecture in actionable terms. The authoritative source of truth for product guarantees is `docs/specs/`; for technical architecture, `docs/design/`. Blockquote pointers throughout this file trace each section to its source. See `docs/development-process.md` for the full SDD layer model.

## Design Principles

> Architecture: [design/three-command-pipeline.md](design/three-command-pipeline.md), [design/append-only-state.md](design/append-only-state.md), [design/prose-as-code.md](design/prose-as-code.md)

Seven principles guide all architectural decisions:

1. **Three-command separation** — Import, Compile, and Expand own exactly one boundary each. No command crosses another's boundary.
2. **Raw immutability** — Files in `raw/` are never modified after capture. No injected headers, no metadata, no frontmatter.
3. **Separation of intelligence** — IMPORT detects format (trivial). COMPILE understands content (requires LLM). Classification happens at the latest responsible moment.
4. **Emergent structure** — Directories, vocabulary, and taxonomy emerge from content. Nothing is predefined.
5. **Manifest as vocabulary** — The manifest IS the approved-values list. No separate registry. Pages are truth; indexes are cache.
6. **Derived state** — Everything regenerable is regenerated. `build-index.py` can reconstruct all indexes from wiki pages alone. If it can be derived, don't store it separately.
7. **Three-tier configuration** — Every value falls into one of three tiers: **(a) Platform invariants** are structural rules baked into protocol prose that no instance should change (e.g., "compile never writes `confidence: high`", "raw files are immutable"). **(b) Tunables** are numeric thresholds, limits, and heuristics that live in `.sprue/defaults.yaml` with sensible defaults; instance operators override any subset in `instance/config.yaml` via deep merge. Both Python scripts and the LLM read the effective (merged) config. **(c) Identity** is prose that shapes the LLM's voice, audience, and scope — it lives in `instance/identity.md`. Litmus test: "Would a cooking KB, a finance KB, and a tech KB all want the same value?" If yes → invariant. If no → tunable.

### Configuration Layering

All tunables live in `.sprue/defaults.yaml` with sensible defaults. Users override any subset in `instance/config.yaml`. The effective config is a deep merge (instance wins for scalars, recursive merge for dicts, lists replaced entirely). Scripts use `.sprue/scripts/config.py` to load the merged config. Protocols reference values via `config.dotpath` notation (e.g., `config.size_profiles.standard.max_words`).

## Architecture

Three layers with strict ownership:

- `raw/` — Source material. Organized by content type. **Immutable** — files are never modified after capture. Classification metadata lives in `instance/state/imports.yaml`, not in the files themselves. When `config.images.enabled` is true, `raw/assets/` stores captured images as immutable snapshots alongside their source documents.
- `wiki/` — LLM-maintained knowledge. The LLM creates, updates, and cross-references all content here.
- `notebook/` — Human-only writing. **Never modify.**

Optional convenience directory:

- `inbox/` — Zero-commitment drop zone. Users dump files here for later triage. Not tracked by the compile queue, not version-controlled (gitignored). To process: `ingest inbox/<file>` moves the file through the normal import pipeline and removes it from inbox/.

### Three-Command Model

> Spec: [specs/source-grounded-knowledge.md](specs/source-grounded-knowledge.md) | Architecture: [design/three-command-pipeline.md](design/three-command-pipeline.md)

Content flows through three independent commands:

```
IMPORT ──► raw/          (seconds — fetch and save, no processing)
COMPILE ──► wiki/        (minutes — batch transform raw → wiki pages)
EXPAND ──► raw/ via IMPORT  (exploratory — discover gaps, research, import)
```

Each command owns exactly one boundary:
- **Import** owns outside world → `raw/`
- **Compile** owns `raw/` → `wiki/`
- **Expand** owns existing knowledge → knowledge gaps → triggers Import

Composites for convenience:
- `ingest <url>` = import + compile (backward-compatible shortcut)
- `ingest <url> --deep` = import + compile + expand
- `import --compile <url>` = import + compile (lighter, no gap analysis)

Commands are matched LITERALLY on the user's leading verb. `import` does NOT imply `ingest`; run bare import and stop.

### Classification Model

> Spec: [specs/emergent-classification.md](specs/emergent-classification.md)

Content is classified along two independent axes:

**Facets** — multi-valued metadata written in frontmatter. Defined in `.sprue/defaults.yaml` → `facets:` section. Each facet has a description, guardrails (max per page, creation threshold, hard max), and its own granularity (conservative or liberal). The manifest is the vocabulary — no predefined value lists. Facets answer: *what is this page about?*

**Directories** — singular filesystem placement. One page lives in one directory. Directories are physical groupings for navigation — like library shelves. They're emergent: the LLM creates them as needed during compile by reading the manifest to understand what each directory contains. Directories answer: *where do I find this page?*

These axes are **independent**. A page placed in any one directory can carry multiple unrelated `domain` values in its frontmatter. The directory is a coarse navigation shelf; the facets are fine-grained conceptual tags. They often correlate but don't have to match.

| Property | Facets | Directories |
|---|---|---|
| Cardinality | Multi-valued (lists) | Singular (one per page) |
| Stored as | Frontmatter YAML fields | Filesystem path |
| Defined in | `.sprue/defaults.yaml` → `facets:` | Emergent (no config) |
| Tracked in manifest | Per-facet value arrays | `dir` string field |
| Changed by | Edit frontmatter | `git mv` (move file) |
| Created by | Write a new value | `mkdir` |
| Validated by | `.sprue/scripts/check-tags.py` | Compile protocol (step 7) |
| Indexed by | `by-{facet}.yaml` | Overview directory table |

Both use the manifest as their vocabulary source. Both are emergent. But facets are metadata (no side effects), while directories are physical structure (filesystem operations). This is why they're managed separately: facet assignment in compile step 6, directory placement in compile step 7.

### Entity Ontology

Entity pages carry structured data beyond frontmatter, in two body sections parsed by `build-index.py` into the manifest:

- `## Attributes` — Key-value pairs: `- **Key**: Value`. The "Kind" attribute mirrors the entity's type from `instance/entity-types.yaml`. Other common attributes: Default Port, Language, License, Managed Offerings.
- `## Relationships` — Typed edges using wikilinks: `- **Competes with**: [[sqs]], [[rabbitmq]]`. Relationship types are a controlled vocabulary defined in `instance/entity-types.yaml`.

The entity type registry (`instance/entity-types.yaml`) maps topic slugs to their ontological kind (e.g., `kafka: message-broker`). This is NOT a facet — it is a property of the **subject**, not of the page. One entity has exactly one type. `build-index.py` reads this file and enriches manifest entries with `entity_type`. The vocabulary is emergent: new types are added during compile. The controlled vocabulary is enforced by `.sprue/scripts/check-entity-types.py`, which runs as part of the standard verification sweep.

Three independent classification layers:
- **Facets** (domain, topic, aspect) → what is this page **about**?
- **Content types** (entity, concept, pattern...) → what **form** does the knowledge take?
- **Entity types** (message-broker, relational-database...) → what **kind of thing** is the subject?

## Frontmatter Schema

Every wiki page requires this YAML frontmatter. The **facet fields** (listed in `.sprue/defaults.yaml` → `facets:`) are config-driven — adding, removing, or renaming a facet in `defaults.yaml` propagates through the entire system.

```yaml
---
type: <see .sprue/defaults.yaml → page_types: for allowed values>
# Facet fields — read .sprue/defaults.yaml → facets: for the current list, descriptions, and guardrails.
# Values are emergent — drawn from the manifest vocabulary, not predefined.
domain: [area-one, area-two]
topic: [subject-a, subject-b]
aspect: [quality-one]
# System fields
confidence: high | medium | low
decay_tier: fast | medium | stable | glacial
author: llm | human | hybrid
provenance: sourced | synthesized
last_verified: null
risk_tier: critical | operational | conceptual | reference
summary: "One-sentence description for agent retrieval and index generation."
sources:                    # raw file(s) + original URLs this page was compiled from (sourced pages only)
  - raw: raw/articles/...
    url: https://...
---
```

### System Fields

| Field | Purpose | Notes |
|---|---|---|
| `type` | Page classification | Drives index generation, Dataview grouping, agent filtering |
| `confidence` | Trust signal | Lint flags `low` for review. Decays by topic velocity. **`high` is a promotion state reached only via `.sprue/protocols/verify.md` source-backed fact-checking — compile never writes `high` for `author: llm` pages.** |
| `decay_tier` | How fast content goes stale | `fast` · `medium` · `stable` · `glacial`. LLM assigns during compile. Half-life values in `config.half_life_tiers` |
| `author` | Who wrote it | `llm`, `human`, or `hybrid` |
| `provenance` | Where the content came from | `sourced` (compiled from a raw file) or `synthesized` (generated from LLM knowledge). Set during compile. |
| `last_verified` | ISO date or `null` | Bumped by verification engine or human confirmation |
| `risk_tier` | Auto-classified | See `config.risk_tier_multipliers` for tier definitions |
| `summary` | One sentence | Required. Powers `wiki/.index/manifest.yaml`. Be specific, not vague |
| `sources` | Raw file paths + source URLs | Set during compile for `provenance: sourced` pages. Omitted for synthesized. Machine-readable provenance chain. |

### Confidence Invariant

> Spec: [specs/continuous-quality.md](specs/continuous-quality.md) | Architecture: [design/confidence-state-machine.md](design/confidence-state-machine.md)

For `author: llm` pages, compile writes `confidence: medium` (default) or `confidence: low` (explicit, when the page is speculative). It never writes `confidence: high`. Only `.sprue/protocols/verify.md`, after source-backed fact-checking, promotes a page to `high` and sets `last_verified` to a real date. This invariant exists because an earlier calibration found ~70% of LLM-self-assigned `high` pages had factual errors on verifiable claims — confidence for LLM-authored content is an operational state, not a judgment the LLM makes about its own output. Human-authored (`author: human` or `hybrid`) pages are exempt; a human may set any confidence at write time.

### Facet Fields

Defined in `.sprue/defaults.yaml` → `facets:` section. Each facet has a `description`, `max_per_page`, and optional `creation_threshold` and `hard_max`. The LLM reads the facets config to understand what each facet means and how to manage its values. The manifest is the vocabulary — no predefined value lists.

**Excluded fields:** `title` (= filename + H1), `related` (= [[wikilinks]] in body), `created`/`updated` (= git history), `sources` (= inline citations next to claims).

### Page Type Sections

Page types are defined in `.sprue/defaults.yaml` → `page_types:` section — the single source of truth for type names, descriptions, and section contracts. The LLM reads the page types config during compile to pick the right type and follow its section contract. Scripts read it to validate frontmatter values.

Section contracts can be overridden per instance in `config.page_types`. If a type is listed there, those sections replace the defaults from `.sprue/defaults.yaml`.

## Operation Dispatch

| # | Signal | Operation | Delegation |
|---|---|---|---|
| 1 | Question about a technology | **Query** | Read `.sprue/protocols/query.md` |
| 2 | URL, file, "save this", "capture" | **Import** | Read `.sprue/protocols/import.md` — includes image capture for markdown sources when images are enabled |
| 3 | "compile", "process", "build pages" | **Compile** | Read `.sprue/protocols/compile.md` |
| 4 | "expand", "grow", "what's missing" | **Expand** | Read `.sprue/protocols/expand.md` — modes: `--semi`, `--auto` |
| 5 | Fix, clean, check existing content | **Maintain** | Read `.sprue/protocols/maintain.md` — first step is always `bash .sprue/verify.sh` |
| 6 | Add links between pages | **Cross-Link** | Read `.sprue/protocols/cross-link.md` |
| 7 | Improve pages or find gaps | **Enhance** | Read `.sprue/protocols/enhance.md` |
| 8 | "verify", "check facts", "validate claims" | **Verify** | Read `.sprue/protocols/verify.md` — modes: `--semi`, `--auto`, `--adversarial` (composable) |
| 9 | Review what agent has learned | **Evolve** | Read `.sprue/protocols/evolve.md` |
| 10 | "reset", "start over", "wipe", "clean slate" | **Reset** | Read `.sprue/protocols/reset.md` |
| 11 | "resolve relationships", "triage rel-links", "fix broken rel-links" | **Resolve Relationships** | Read `.sprue/protocols/resolve-relationships.md` |

**Composite shortcuts:**
- `ingest <url>` = Import + Compile (one source, immediately)
- `ingest <url> --deep` = Import + Compile + Expand
- Other composite requests: execute in order Import → Compile → Enhance → Cross-Link → Maintain.

**Command matching is LITERAL.** The leading verb the user typed is what you execute. `import <url>` is NOT `ingest <url>`. If the user typed `import`, run bare Import and stop — even if ingest looks more convenient. Do not second-guess the user's literal command. Do not infer that they "meant" a composite. The composite shortcuts above activate ONLY when the user types that exact verb.

**Status & queue management:**
- `status` — show compile queue count, inbox count, last operation timestamps, KB stats. Include `📬 Inbox: N items` if `inbox/` contains any files.
- `status --queue` — show detailed compile queue
- `drop <n>` — remove item from compile queue (keeps raw file in `raw/`)

**Lifecycle management:**
- `reset` — return KB to blank slate. Three levels: `soft` (recompile), `standard` (start over), `hard` (new domain). Read `.sprue/protocols/reset.md`

**Pipeline configuration**: compile behavior is customizable per-run via profiles and stage overrides. Read `.sprue/protocols/pipeline-config.md` for the full guide. Config file: `.sprue/schemas/pipeline.yaml`. Prompt templates: `.sprue/prompts/`. Custom profiles: `.sprue/profiles/`.

**Page granularity** decisions (new page vs. new section, split vs. merge): read `.sprue/protocols/granularity.md`.

**Agent capabilities**: if you lack write/shell access, operate in read-only (answer queries from wiki) or advisory mode (propose actions as a checklist).

When in doubt, ask the user which operation they intend.

## Memory

> Architecture: [design/agent-memory.md](design/agent-memory.md)

The agent learns from corrections across sessions. **Read `.sprue/protocols/memory.md` for the full protocol.**

Bootstrap checklist — before every operation:
1. Run `python3 .sprue/scripts/check-config.py`. If it reports errors, stop and surface them to the user before proceeding.
2. Read `memory/rules.yaml` (structural rules; see `.sprue/scripts/lint-rules.py` for the schema)
3. Before any write: also read `memory/corrections.md` (active factual corrections)

## Style Rules

- Use [[wikilinks]] for all internal cross-references.
- Always specify language in code blocks (` ```java `, ` ```python `, etc.).
- Page size limits are per-type — see `config.page_types.<type>.size_profile` and `config.size_profiles`.
- Prefer concrete code examples over abstract descriptions.
- Use mermaid diagrams (` ```mermaid `) when a visual clarifies — don't force them on every page. Prefer mermaid over ASCII art.
- When confidence is low, say so explicitly in the page content.
- **KB identity & guidelines**: read `instance/identity.md`. The LLM derives audience, voice, depth, and scope from the identity statement.
- **Visual knowledge**: images embedded in source material are captured, classified, and cited alongside text. See `.sprue/protocols/import.md` (Step 4a) and `.sprue/protocols/compile.md` (Step 4a).

## Special Files

| File | Purpose |
|---|---|
| `memory/log.jsonl` | Append-only op log: `{"ts":"ISO8601","op":"...","title":"...","created":N,"modified":N,"deleted":N,"summary":"..."}` |
| `wiki/overview.md` | Auto-generated stats + navigation. Regenerate: `python3 .sprue/scripts/build-index.py` |
| `wiki/.index/manifest.yaml` | Machine-readable page metadata. Generated by `build-index.py` |
| `wiki/.index/by-tag.yaml` | Reverse index: tag → slugs |
| `wiki/.index/by-type.yaml` | Reverse index: type → slugs |
| `instance/state/imports.yaml` | Import ledger: URL → raw path (dedup). Append-only. |
| `instance/state/compilations.yaml` | Compile ledger: raw path → wiki pages. Append-only. |
| `instance/state/expansions.yaml` | Expand history: runs, topics proposed/accepted/rejected. Append-only. |
| `instance/state/enhancements.yaml` | Enhance gap ledger: new-page findings approved by human. Consumed by EXPAND. Append-only. |
| `instance/state/verifications.yaml` | Verify ledger: page claims checked, fixes applied. Append-only. |
| `instance/state/image-annotations.yaml` | Image classification and extracted claims, keyed by content hash. Append-only. |
| `raw/assets/` (directory) | Immutable storage for captured images. Populated during import when `config.images.enabled` is true. |
| `instance/config.yaml` | User overrides — only what differs from defaults |
| `.sprue/defaults.yaml` | All tunables with platform defaults — facets, page types, size profiles, thresholds |
| `instance/entity-types.yaml` | Entity ontological registry: topic slug → kind, relationship type vocabulary |
| `wiki/.index/by-entity-type.yaml` | Reverse index: entity kind → slugs. Generated by `build-index.py` |
| `wiki/.index/by-relationship.yaml` | Typed relationship graph: rel_type → {source: [targets]}. Generated by `build-index.py` |
| `wiki/.index/by-slug-raws.yaml` | Reverse index: slug → [raw file paths]. Derived from `compilations.yaml` filtered against the current manifest (orphaned rows dropped). Generated by `build-index.py`. Consumed by verify Phase 2a, compile `--recompile`, and `prioritize.py`. |
| `.sprue/schemas/pipeline.yaml` | Compile pipeline configuration: strategies, profiles, approval gates |
| `.sprue/prompts/*.md` | Compilation prompt templates (one per strategy) |
| `.sprue/profiles/*.yaml` | Custom compile profiles (one per file) |
| `.sprue/reset.sh` | Mechanical reset script: deletes content, state, domain config by level |
| `.sprue/protocols/reset.md` | Reset protocol: level selection, confirmation flow, recovery |
| `docs/development-process.md` | How the platform itself is developed — generic SDD method and work flows |

## Constraints

> Spec: [specs/content-safety.md](specs/content-safety.md), [specs/source-grounded-knowledge.md](specs/source-grounded-knowledge.md)

| Rule | Instead |
|---|---|
| Never create pages without frontmatter | — |
| Never duplicate content across pages | Link instead |
| Never use vague summaries | Be specific: not "useful tool" but "Kafka consumer groups, offset management, lag" |
| Only compile creates wiki pages | Import saves to raw/. Expand triggers imports. During maintain/enhance, flag: "New page needed: [topic]. Run import + compile." |
| Never delete wiki pages unless human explicitly asks | Niche topics are valid. KB accumulates knowledge |
| Never reset without explicit user confirmation | Run dry-run first, require user to type the level name |
| Don't silently overwrite content that seems wrong | Add a conflict callout. Set `confidence: low` with `> ⚠️ **Outdated**: ...` |
| Don't edit many pages without approval | Compile Step 3 classification plan IS the batch plan. Once approved, execute ALL pages without pausing. NEVER say "Page N done, say go for page N+1." |
| Never create duplicate raw files for the same source URL | Check `instance/state/imports.yaml` before every write — including within a batch. In batch mode, maintain an in-memory seen-set of URLs processed so far in the current run |
| Never inject metadata into raw files | Raw files are verbatim source content. Classification metadata (source URL, title, content_type) belongs only in `instance/state/imports.yaml` — never as YAML frontmatter or headers in the file itself |
| Never skip image capture during import when the source contains embedded images | Capturing images is part of the import protocol (Step 4a). Images are first-class knowledge sources, not decoration. See `.sprue/protocols/import.md` |
