# LLM Wiki Platform

A reusable platform for building LLM-operated knowledge bases. You provide the identity and content — the platform provides the engine, protocols, and tooling.

## How It Works

```
.sprue/         ← The engine (you don't edit this)
  specs/           ← Product intent — WHAT the platform guarantees
  design/          ← Technical architecture — high-level HOW
  decisions/       ← Architecture Decision Records — WHICH choices and WHY
  defaults.yaml    ← Every tunable value with sensible defaults
  engine.md        ← Architecture, commands, schema, constraints
  development-process.md ← How the platform is developed (six-layer stack)
  protocols/       ← Operation procedures (compile, verify, expand, etc.)
  scripts/         ← Python validators (lint, index, search, decay)
  prompts/         ← LLM prompt templates
  schemas/         ← Pipeline profiles
  verify.sh        ← Lint and verification runner

instance/          ← Your customization (you edit this)
  identity.md      ← One sentence defining your KB's audience, voice, and scope
  config.yaml      ← Override any platform default

wiki/              ← Your compiled knowledge (LLM-generated from raw sources)
raw/               ← Your source material (immutable once imported)
notebook/          ← Your own writing (never touched by the LLM)
inbox/             ← Drop zone for unsorted material (gitignored, local-only)
memory/            ← Agent memory — learned rules, corrections, logs
AGENTS.md          ← Agent bootstrap — points the LLM to the engine
```

## Prerequisites

- **Python 3.10+** with `pyyaml` (`pip install pyyaml`)
- **An LLM agent** with file system access (e.g., Claude, GPT-4 via an agent framework)
- The agent must be configured to read `AGENTS.md` at the project root on startup — this file points it to `.sprue/engine.md` and `instance/identity.md`, which together define how the agent operates

Optional for semantic search: `pip install sentence-transformers numpy`

## Quick Start

### 1. Define your identity

Create `instance/identity.md` with a single sentence:

```markdown
# KB Identity

Professional technology reference for a Staff SDE. Capture transferable
concepts, patterns, and tools; strip project-specific mechanics and personal information.
```

This sentence drives everything — the LLM derives audience, voice, depth, and scope from it. A cooking KB might say:

```markdown
Home cook's reference for techniques and science. Prioritize understanding
over recipes; explain why methods work, not just how.
```

### 2. Customize config (optional)

Create `instance/config.yaml` with only what differs from platform defaults. Browse `.sprue/defaults.yaml` to see every tunable value.

```yaml
# instance/config.yaml — only what you want to change
overrides:
  redis: valkey          # normalize facet vocabulary
  machine-learning: llm
```

The platform deep-merges your overrides on top of `.sprue/defaults.yaml`:
- Scalars → your value replaces the default
- Dicts → recursive merge (your keys override, unmentioned defaults survive)
- Lists → your list replaces the entire default list

### 3. Start using it

Talk to the LLM agent in natural language:

| Say | What happens |
|---|---|
| `ingest <url>` | Fetches the URL, saves to `raw/`, compiles to `wiki/` pages |
| `compile` | Processes uncompiled raw files into wiki pages |
| `expand` | Discovers knowledge gaps, researches, imports new sources |
| `maintain` | Lints, upgrades quality, checks health |
| `verify` | Fact-checks claims against authoritative sources |
| `query <question>` | Answers from wiki knowledge |
| `status` | Shows KB stats and pending work |
| `help` | Full command overview |

## What You Can Customize

Everything in `.sprue/defaults.yaml` is overridable. Key sections:

### Facets

Classification dimensions with LLM-instructional descriptions. Override descriptions to match your domain:

```yaml
# instance/config.yaml
facets:
  domain:
    description: >
      Legal practice areas. A case typically spans 1-2 areas.
      Create new areas conservatively.
    max_per_page: 2
    creation_threshold: 15
```

### Page Types

Add new types or modify section contracts:

```yaml
# instance/config.yaml
page_types:
  case_brief:                    # new type for a legal KB
    size_profile: compact
    description: >
      Summary of a legal case. Reader gets holding, reasoning, and significance.
    sections:
      - TL;DR
      - Facts
      - Holding
      - Reasoning
      - Significance
```

### Size Profiles

Control page length thresholds:

```yaml
# instance/config.yaml
size_profiles:
  min_creation_words: 300       # raise the bar for standalone pages
  standard:
    max_words: 5000             # allow longer pages
```

### All Tunables

| Section | Controls |
|---|---|
| `facets` | Classification dimensions, descriptions, guardrails |
| `page_types` | Content types, section contracts, size profiles |
| `size_profiles` | Page creation, split, and merge thresholds |
| `granularity` | Split/merge signal thresholds |
| `entity` | Entity page attribute and relationship ranges |
| `cross_link` | Wikilink density and detection thresholds |
| `upgrade` | Automatic quality improvement thresholds |
| `half_life_tiers` | Content freshness decay rates |
| `risk_tier_multipliers` | Risk-based decay adjustments |
| `placement` | Directory organization rules |
| `maintenance` | Staleness and cooldown timers |
| `expand` | Gap discovery and research controls |
| `verify` | Fact-checking controls and weights |
| `enhance` | Agent personas for enhancement |
| `overrides` | Facet vocabulary normalization |

## Directory Structure

| Directory | Purpose | Who writes |
|---|---|---|
| `wiki/` | Compiled knowledge pages | LLM (via compile) |
| `raw/` | Source material (articles, papers, snippets) | Import command |
| `notebook/` | Your own writing, learnings, questions | You (human only) |
| `inbox/` | Drop zone for unsorted material (gitignored, local-only) | You |
| `memory/` | Agent memory — learned rules, corrections, evolution logs | LLM + human |
| `instance/` | Your identity and config overrides | You |
| `.sprue/` | The engine (don't edit) | Platform maintainer |
| `AGENTS.md` | Agent bootstrap — reads this on startup, follows `engine.md` | Platform maintainer |

The `inbox/` directory is a convenience feature — drop files there for later triage. Contents are not version-controlled. To process an inbox item: `ingest inbox/<file>` moves it through the normal import pipeline and removes it from inbox/.

## Optional Validators

The engine ships validators your instance can enable by registering them
in `memory/rules.yaml`. Register only the ones you want enforced:

| Validator | Enforces |
|---|---|
| `.sprue/scripts/check-sources.py` | Every LLM-authored `provenance: sourced` page declares non-empty `sources:` (ADR-0028) |
| `.sprue/scripts/check-package-contents.py` | Built wheels contain no instance paths (CI gate) |

Example `memory/rules.yaml` entry:

```yaml
rules:
  - name: sources-declared
    command: python3 .sprue/scripts/check-sources.py --quiet
    scope: whole
```

## Going Deeper

- `.sprue/engine.md` — Full architecture, command reference, schema, constraints
- `docs/development-process.md` — How the platform is developed (for contributors)
- `.sprue/defaults.yaml` — Browse every tunable value with comments
- `.sprue/protocols/` — Detailed procedures for each operation

## CI

The platform includes a GitHub Actions workflow (`verify.yml`) that runs lint and verification on push/PR. It executes `.sprue/scripts/lint-rules.py` and `.sprue/scripts/verify.py`.
