# Sprue

A reusable engine for building LLM-operated knowledge bases. You provide the identity and content — Sprue provides the protocols, tooling, and configuration.

**Sprue** is the channel through which raw material flows into a mold. Raw sources flow through the engine and emerge as structured wiki pages.

## Status

v0.1.0 — alpha. The CLI and engine work end-to-end but the API may change before 1.0. See the [distribution spec](docs/specs/platform-distribution.md) and [ADR-0033](docs/decisions/0033-sprue-distribution-model.md) for design rationale.

## Quick Start

### From source (available today)

```bash
git clone https://github.com/altakleos/sprue.git
cd sprue
pip install -e .
```

### From PyPI (pending first release)

```bash
pip install sprue
```

### Create a knowledge base

```bash
sprue init my-kb --identity 'Professional technology reference for a Staff SDE.'
cd my-kb
```

Point your LLM agent at the directory and tell it to read `AGENTS.md`. The agent will discover the engine and begin operating the knowledge base.

## What `sprue init` produces

| Directory | Purpose |
|---|---|
| `.sprue/` | Engine files (protocols, scripts, schemas — don't edit) |
| `instance/` | Your identity and config overrides |
| `raw/` | Source material (immutable after import) |
| `wiki/` | Compiled knowledge pages |
| `notebook/` | Your own writing (never touched by the LLM) |
| `inbox/` | Drop zone for unsorted material (gitignored) |
| `memory/` | Agent memory — learned rules, corrections, logs |
| `state/` | Runtime state (gitignored) |

## Documentation

- [Platform Guide](src/sprue/engine/README.md) — how to use Sprue, customization, directory structure
- [Engine Reference](src/sprue/engine/engine.md) — architecture, commands, schema, constraints
- [Configuration Reference](src/sprue/engine/defaults.yaml) — every tunable value with comments

## For Contributors

- [Development Process](docs/development-process.md) — how the platform is developed
- [Architecture Decisions](docs/decisions/README.md) — why decisions were made
- [Specifications](docs/specs/README.md) — product intent and invariants
- [Design Documents](docs/design/README.md) — technical architecture

## License

MIT
