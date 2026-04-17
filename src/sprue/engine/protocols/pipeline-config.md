# Pipeline Configuration Guide

The three commands (import, compile, expand) are fully customizable. Zero config required — sensible defaults work out of the box.

## Quick Reference

| I want to... | Do this |
|---|---|
| Import a URL (fast, no processing) | `import <url>` |
| Import and compile immediately | `ingest <url>` or `import --compile <url>` |
| Import, compile, and discover gaps | `ingest <url> --deep` |
| Compile all pending raw files | `compile` |
| Compile specific items from queue | `compile 1,3,5` |
| Compile with shallow summary | `compile --profile quick` |
| Compile with deep extraction | `compile --profile research` |
| Compile as source-summary only | `compile --profile reference` |
| Extract claims from a paper | `compile --profile claims` |
| Grab code examples only | `compile --profile code` |
| Use a custom compilation prompt | `compile --strategy custom --custom_prompt "Extract only..."` |
| Find and fill knowledge gaps | `expand` |
| Expand — user picks topics, LLM picks sources | `expand --semi` |
| Expand — fully delegated to LLM | `expand --auto` |
| Expand focused on one directory | `expand data/` |
| See what's pending | `status` |
| See detailed compile queue | `status --queue` |
| Remove item from compile queue | `drop 3` |

## How Configuration Works

Three layers, highest wins:

```
CLI flags (per-run)          ← highest priority
  ↓
Active profile               ← named preset in pipeline.yaml or sprue/profiles/*.yaml
  ↓
sprue/schemas/pipeline.yaml            ← persistent defaults
  ↓
Built-in defaults            ← hardcoded, works with no config file at all
```

## The Three Commands

### Import (sprue/protocols/import.md)
Fast capture. Fetch → save to `raw/`. No processing.

Settings in `sprue/schemas/pipeline.yaml` under `import:`:
- `timeout_seconds` — fetch timeout
- `extract` — what to pull from web pages (full/article/code_only)
- `crawl_depth` — follow links N levels deep

### Compile (sprue/protocols/compile.md)
Batch transform `raw/` → `wiki/`. The intelligence layer.

Settings in `sprue/schemas/pipeline.yaml` under `compile:`:
- `strategy` — how to transform content (wiki_page, key_claims, concept_map, code_extract, flashcards, raw_summary, custom)
- `depth` — extraction depth (shallow, standard, deep)
- `diagrams` — generate mermaid diagrams
- `place.mode` — wiki directory selection (auto, ask, fixed)
- `tag.mode` — tag assignment (auto, suggest, manual)
- `link.outbound/inbound` — wikilink behavior
- `verify.mode` — run verify.sh after writes
- `approval.*` — where the pipeline pauses for human input

### Expand (sprue/protocols/expand.md)
Discover gaps → research → import. The growth engine.

Settings in `sprue/schemas/pipeline.yaml` under `expand:`:
- `max_suggestions` — topics to propose per run
- `max_imports` — auto-imports per run
- `research_depth` — how thoroughly to research each topic
- `mode` — propose (default, safe) or auto

## Compile Strategies

| Strategy | Output | Best for |
|---|---|---|
| `wiki_page` | Full wiki page per sprue/engine.md contracts | Default. Most sources. |
| `key_claims` | Numbered claims with evidence ratings | Papers, benchmarks |
| `concept_map` | Concept → relationship graph + mermaid | Dense articles, new areas |
| `code_extract` | Code examples with context | Tutorials, repos |
| `flashcards` | Q&A pairs for spaced repetition | Study material |
| `raw_summary` | TL;DR + bullet points | Quick capture, bookmarks |
| `custom` | Your prompt | Anything else |

Each strategy has a prompt template in `sprue/prompts/<strategy>.md`. Edit to change globally.

## Profiles

Profiles are named presets that override specific compile settings. Everything else uses defaults.

| Profile | What it does | When to use |
|---|---|---|
| `quick` | Shallow summary, no linking/verify | Bookmarking, rapid capture |
| `research` | Deep extraction, thorough research | Deep-diving a new area |
| `reference` | Source-summary page, no inbound links | Archiving papers/articles |
| `claims` | Extract verifiable claims | Papers, benchmarks |
| `code` | Code examples only, skip prose | Tutorials, repos |

### Creating Custom Profiles

Create `sprue/profiles/<name>.yaml`. Only specify what you want to override:

```yaml
# sprue/profiles/security-audit.yaml
compile:
  depth: deep
  strategy: key_claims
  tag: { extra_tags: [security] }
  place: { mode: fixed, directory: security }
```

Use it: `compile --profile security-audit`

### Combining Profiles with CLI Overrides

```
compile --profile research --depth shallow    # research profile but shallow depth
compile --profile quick --verify.mode auto    # quick profile but still verify
```

## State Management

Three append-only files in `instance/state/` track what each command has done. See `instance/state/README.md` for details.

| File | Purpose |
|---|---|
| `imports.yaml` | URL → raw path (dedup) |
| `compilations.yaml` | raw path → wiki pages produced |
| `expansions.yaml` | expand run history + topic dispositions |
