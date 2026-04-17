---
status: accepted
date: 2026-04-16
---
# ADR-0033: Sprue Distribution Model — pip + Local Engine Copy

## Context

The `platform-distribution` spec commits Sprue to being installable without cloning the repo, initializable with a single command, upgradeable without touching instance content, and operable by an LLM agent that can read engine files at runtime. The `platform-reusability` spec commits to a domain-agnostic engine with identity as the only required per-instance input.

A distribution mechanism must satisfy all of these simultaneously. The LLM-readability constraint is the most specific — engine files must live at a path the agent can browse, not hidden inside `site-packages` where typical LLM tooling does not look. This rules out treating Sprue as a pure Python library.

## Decision

Distribute Sprue as a **pip-installable Python package with local engine copy**. Installation provides a CLI; `sprue init` copies the engine files (protocols, scripts, prompts, defaults, schemas, profiles, engine.md) into a `.sprue/` directory at the instance root. Instance content (`identity.md`, `config.yaml`, `raw/`, `wiki/`, `memory/`, `state/`) lives alongside `.sprue/` and is owned by the user. `sprue upgrade` is an explicit user-initiated command that replaces only `.sprue/`, never touching instance files.

Packaging uses `hatchling` as the build backend with a `src/sprue/` package layout. Engine files are bundled as package data and accessed at runtime via `importlib.resources.files()`. The CLI entry point is declared in `[project.scripts]` per PEP 621. SemVer governs the package; `schema_version` in `defaults.yaml` evolves independently and gates compatibility.

Migration tooling in v1 takes the form of guided instructions printed by the CLI when `schema_version` changes. Automated migration scripts may be added in later versions within the same compatibility framework.

## Alternatives Considered

- **Pure pip package (engine in `site-packages` only)** — rejected because the LLM agent cannot reliably browse `site-packages` at runtime. The entire runtime model depends on engine files being visible at a path the agent reads. A hidden engine forces the agent to operate blind.
- **Git submodule / subtree** — rejected because the user experience is painful (manual clone, update dance, easy to forget), and it couples instance repos to the platform's git URL. Fails the "installable without cloning" invariant.
- **Cookiecutter-style one-shot scaffold** — rejected because there is no upgrade path. Users would fork the engine at init and never receive platform improvements, violating `platform-reusability` invariant 5 (platform upgrades ship new defaults).
- **Monorepo remains** — rejected by ADR-0030, ADR-0032, and the entire `platform-distribution` spec. Not a real alternative; listed for completeness.
- **CRA-eject style** — rejected. The ejection model has been widely abandoned (CRA itself deprecated it) because it bifurcates users into "still supported" and "on their own" populations. Sprue needs one path.

## Consequences

Users install via `pip install sprue`, run `sprue init <dir>`, answer identity prompts, and get a functional KB. The `.sprue/` directory is plain text and can be committed to git, making instances portable across machines with the same engine version installed. `sprue upgrade` is the only thing that modifies `.sprue/`; nothing silent ever runs.

The ~76 hardcoded `sprue/` path references across scripts, protocols, `engine.md`, and `AGENTS.md` must migrate to resolve `.sprue/` at runtime. This is a mechanical but broad refactor; the design doc prescribes routing through a single `config.engine_root` resolver rather than find-and-replace.

v1 migration UX is deliberately simple (printed instructions) rather than full automation. This is acknowledged in both the spec and the design as a scope choice; the compatibility framework leaves room for automation in later versions without a spec change.

Distribution introduces a new enforcement surface: a build-time check that no instance content is included in the wheel, and a runtime `check-config.py` assertion that the instance's `schema_version` is within the engine's supported range. Both are called out in the spec's Enforcement table.

## Config Impact

Adds a `schema_version` compatibility window concept to `defaults.yaml` (exact shape specified in the design doc). No existing config keys change.

## References

- [Platform Distribution](../specs/platform-distribution.md) — product invariants this decision implements
- [Platform Reusability](../specs/platform-reusability.md) — domain-agnostic engine invariants
- [Sprue Distribution Model](../design/sprue-distribution.md) — technical mechanism
- [ADR-0006: Configuration Layering](0006-configuration-layering.md) — deep-merge model that upgrade preserves
- [ADR-0007: Platform/Instance Architecture](0007-platform-instance-architecture.md) — the split this decision packages
- [ADR-0025: Schema Versioning](0025-schema-versioning.md) — schema version policy referenced here
- [ADR-0031: Product Name — Sprue](0031-product-name-sprue.md) — the package name
