# Contributing to Sprue

This file is for LLM agents helping engineers develop the Sprue **platform itself**.

> **KB operators:** If you are operating a knowledge base built with Sprue, read [engine.md](src/sprue/engine/engine.md) instead. This file is NOT for you.

## Quick Reference

### Audience Gate

| You are… | Read this |
|----------|-----------|
| Contributing to the Sprue platform | **This file** |
| Operating a KB built with Sprue | [engine.md](src/sprue/engine/engine.md) |
| Learning what Sprue does | [Platform Guide](src/sprue/engine/README.md) |

### Six-Layer Stack

| Layer | Location | I want to… |
|-------|----------|------------|
| Specs | `docs/specs/` | Add or change a product guarantee |
| Design Docs | `docs/design/` | Propose a new mechanism or architecture |
| ADRs | `docs/decisions/` | Record a non-obvious decision |
| Plans | `docs/plans/` | Break a feature into ordered tasks |
| Protocols | `src/sprue/engine/protocols/` | Change how the LLM executes an operation |
| Config + Validators | `src/sprue/engine/defaults.yaml` + `src/sprue/engine/scripts/` | Tune a threshold or add a check |

Authoritative reference: [docs/development-process.md](docs/development-process.md)

### Key Commands

```bash
# Installed CLI (after `pip install -e .` from repo root)
sprue verify                              # run all validators
sprue verify --file <path>                # validate one file
sprue init <dir> --identity "one-line"    # scaffold a new KB
sprue upgrade [<dir>]                     # upgrade engine in an existing KB

# Shell wrapper (direct, no install required)
bash src/sprue/engine/verify.sh           # equivalent to `sprue verify`
bash src/sprue/engine/reset.sh --level soft|standard|hard              # dry-run
bash src/sprue/engine/reset.sh --level soft|standard|hard --confirm    # execute
```

## Task Routing

### Adding or Changing a Product Guarantee

- **Prerequisite:** None — this is the top of the stack.
- **Start at:** `docs/specs/` — write or update a spec capturing product intent
- **Then:** Update affected protocols in `src/sprue/engine/protocols/` and validators in `src/sprue/engine/scripts/`
- **After:** `sprue verify`
- **See:** [docs/specs/README.md](docs/specs/README.md)

### Designing a New Mechanism

- **Prerequisite:** A spec in `docs/specs/` the mechanism serves. If none exists, write the spec first.
- **Start at:** `docs/design/` — write a design doc with architecture and trade-offs
- **Then:** Capture non-obvious decisions as ADRs in `docs/decisions/`
- **After:** `sprue verify`
- **See:** [docs/design/README.md](docs/design/README.md)

### Recording a Decision

- **Prerequisite:** A design doc or spec the decision relates to, OR a genuine choice with viable alternatives.
- **Start at:** `docs/decisions/` — create `0040-<slug>.md` (next number: **0040**)
- **Then:** Use established format: YAML frontmatter (`status`, `date`), Context, Decision, Alternatives Considered, Consequences, optional Config Impact
- **After:** `sprue verify`
- **See:** [docs/decisions/README.md](docs/decisions/README.md)
- **Rule:** ADRs are **immutable**. NEVER edit an accepted ADR. To reverse a decision, write a new ADR that supersedes it and set the old one's status to `superseded`.

### Planning a Feature Implementation

- **Prerequisite:** A spec and/or design doc for the feature. Plans implement existing decisions; they do NOT originate them.
- **Start at:** `docs/plans/` — write a task breakdown with ordered steps and file paths
- **Then:** Commit the plan as the first commit on the feature branch
- **After:** `sprue verify`
- **See:** [docs/plans/README.md](docs/plans/README.md) for the template

### Modifying a Protocol

- **Prerequisite:** Understand which spec the protocol serves. If the change alters a product guarantee, update the spec FIRST.
- **Start at:** The protocol in `src/sprue/engine/protocols/` — read it and the spec it serves
- **Then:** Edit in imperative, deterministic style. Reference config via `config.dotpath`. NEVER hardcode thresholds.
- **After:** `sprue verify`
- **See:** [docs/design/prose-as-code.md](docs/design/prose-as-code.md)

### Tuning Config

- **Prerequisite:** The value is already consumed somewhere, OR you are wiring a new consumer in the same change. Orphan config keys are forbidden.
- **Start at:** `src/sprue/engine/defaults.yaml` — find or add the tunable with a comment
- **Then:** Update protocols that reference the dotpath, and wire the key into any validator or script that should consume it (see `src/sprue/engine/scripts/config.py` for the loader). Search for existing consumers: `grep -r "<dotpath>" src/sprue/engine/protocols/ src/sprue/engine/scripts/`
- **After:** `sprue verify`
- **See:** [src/sprue/engine/defaults.yaml](src/sprue/engine/defaults.yaml)
- **Litmus test:** "Would every KB want the same value?" → invariant (bake into protocol prose). Otherwise → config.

### Adding or Fixing a Validator

- **Prerequisite:** An invariant from a spec or protocol that can be checked mechanically. If the invariant doesn't exist yet, document it in the relevant spec/protocol first.
- **Start at:** `src/sprue/engine/scripts/` — create `check-<name>.py` or fix the existing script
- **Then:** Register it as a rule in `memory/rules.yaml` (the orchestrator `src/sprue/engine/scripts/verify.py` loads rules from there — see existing entries for format). NEVER remove comments or logging from scripts.
- **After:** `sprue verify`
- **See:** [docs/decisions/0013-tooling-and-ci-pipeline.md](docs/decisions/0013-tooling-and-ci-pipeline.md)
- **Rule:** Validators MUST be Python. `verify.sh` is the sole bash wrapper.

## The Six-Layer Stack

Higher layers are more abstract and change less often. Lower layers change more frequently.

```
Specs → Design Docs → ADRs → Plans → Protocols → Config + Validators
(most stable)                                      (most volatile)
```

**Cardinal rule:** Changes flow top-down. A protocol change that alters a product guarantee MUST update the spec first. A config change that introduces a new mechanism MUST have a design doc.

### When Do I Need Each Layer?

- **Spec** — New user-visible capability or product guarantee
- **Design Doc** — New technical mechanism where architecture is non-obvious
- **ADR** — Decision with genuine alternatives a future reader would question
- **Plan** — Multi-step feature with 3+ commits across multiple files
- **Protocol** — Any change to how the LLM executes an operation
- **Config** — Any tunable value; NEVER hardcode in protocol prose
- **Validator** — Any new invariant that can be checked mechanically

Full reference: [docs/development-process.md](docs/development-process.md)

## Verification

### Setup

```bash
pip install -e .           # install the sprue package in editable mode (once)
```

### Full Suite

```bash
sprue verify                              # preferred (requires pip install -e .)
bash src/sprue/engine/verify.sh           # alternative (no install required)
```

### Individual Validators

```bash
python3 src/sprue/engine/scripts/check-frontmatter.py      # YAML frontmatter fields
python3 src/sprue/engine/scripts/check-tags.py              # facet tag cardinality
python3 src/sprue/engine/scripts/check-entity-types.py      # entity type registry
python3 src/sprue/engine/scripts/check-config.py            # config consistency
python3 src/sprue/engine/scripts/check-fences.py            # code fence validation
python3 src/sprue/engine/scripts/check-wikilinks.py         # wikilink integrity
python3 src/sprue/engine/scripts/check-constraints.py       # memory constraint probes
python3 src/sprue/engine/scripts/check-placement.py         # directory placement rules
python3 src/sprue/engine/scripts/lint-rules.py              # rules.yaml validation
python3 src/sprue/engine/scripts/verify.py                  # all rules from memory/rules.yaml
python3 src/sprue/engine/scripts/check-package-contents.py  # built wheel integrity (CI)
```

### Reset

```bash
bash src/sprue/engine/reset.sh --level soft|standard|hard              # dry-run (shows what would be deleted)
bash src/sprue/engine/reset.sh --level soft|standard|hard --confirm    # execute (requires clean git tree)
```

- `soft` — wiki + indexes + compile/verify state. Raw preserved.
- `standard` — + raw, memory, all state, domain config.
- `hard` — + identity, config overrides, enhance agents.

### Build Verification (CI)

```bash
python3 -m build --wheel
python3 src/sprue/engine/scripts/check-package-contents.py   # verify wheel has no instance paths
```

## Repository Map

```
AGENTS.md                          ← you are here (platform contributors)
README.md                          ← project overview and quick start
pyproject.toml                     ← build config (hatchling), deps, CLI entry point
docs/
  development-process.md           ← authoritative 6-layer stack reference
  specs/          (8 specs)        ← product intent and invariants
  design/         (8 docs)         ← technical architecture
  decisions/      (33 ADRs)        ← decision records (immutable, next: 0034)
  plans/          (template only)  ← feature task breakdowns
src/sprue/                         ← Python package root
  __init__.py                      ← version string (single source of truth)
  engine_root.py                   ← resolves engine path at runtime
  cli/                             ← CLI subcommands (init, upgrade, verify)
  engine/                          ← ships to users (domain-agnostic engine)
    engine.md                      ← LLM operational kernel (KB operators)
    README.md                      ← platform guide
    defaults.yaml                  ← all tunables with defaults
    protocols/    (15 files)       ← prose code (LLM-executable)
    scripts/      (21 files)       ← Python validators and utilities
    prompts/      (10 files)       ← prompt templates
    schemas/                       ← pipeline schemas
    profiles/                      ← compile profiles
    verify.sh                      ← test suite runner (thin wrapper → verify.py)
    reset.sh                       ← KB reset (soft/standard/hard)
  templates/                       ← instance scaffolding for `sprue init`
.github/workflows/                 ← CI (verify.yml) + release (release.yml)
instance/                          ← user domain (created by `sprue init`, NOT in platform repo)
```

### Boundary Rules

- `src/sprue/engine/` = platform engine. Ships to users. MUST be domain-agnostic.
- `src/sprue/cli/` = CLI entry points. Thin wrappers around engine logic.
- `instance/` = user domain. NEVER committed to the platform repo.
- `docs/` = contributor docs. Stays in source repo. NEVER ships to users.

## Key Principles

- **Prose is code.** Protocols are executable instructions, not documentation. Ambiguity is a bug.
- **Specs before design.** Product intent MUST exist before architecture work begins.
- **Config over hardcoding.** Every tunable value goes in `src/sprue/engine/defaults.yaml`, referenced via `config.dotpath`.
- **Validators close the loop.** Every invariant from a spec MUST have a mechanical check in `src/sprue/engine/scripts/`.
- **Cross-link, don't duplicate.** Point to the authoritative source; NEVER copy content between layers.
- **Append-only state.** State files are append-only logs. NEVER mutate or delete entries.
- **Scripts compute, protocols judge.** Deterministic work → Python. Judgment and synthesis → LLM protocol.
- **`raw/` is immutable.** Source material in `raw/` MUST NEVER be modified after ingestion.
