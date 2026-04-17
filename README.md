# Sprue

A reusable engine for building LLM-operated knowledge bases. You provide the identity and content — Sprue provides the protocols, tooling, and configuration.

**Sprue** is the channel through which raw material flows into a mold. Raw sources flow through the engine and emerge as structured wiki pages.

## Quick Start

```bash
pip install sprue
sprue init my-kb
cd my-kb
# Tell your LLM agent: "ingest https://some-article.com"
```

## Documentation

- [Platform Guide](sprue/README.md) — how to use Sprue, customization, directory structure
- [Engine Reference](sprue/engine.md) — architecture, commands, schema, constraints
- [Configuration Reference](sprue/defaults.yaml) — every tunable value with comments

## For Contributors

- [Development Process](docs/development-process.md) — how the platform is developed
- [Architecture Decisions](docs/decisions/README.md) — why decisions were made
- [Specifications](docs/specs/README.md) — product intent and invariants
- [Design Documents](docs/design/README.md) — technical architecture

## License

MIT
