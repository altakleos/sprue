---
status: accepted
date: 2026-04-16
---
# Platform Distribution

## Intent

The platform is distributed as **Sprue** — an installable product that any knowledge domain can adopt without forking or disentangling engine from content. Users install Sprue, run an initialization command, and get a fully configured instance with identity, configuration, and empty content directories. The current monorepo (engine + one instance) is split into a reusable engine package and per-domain instances that depend on it.

## Invariants

- The engine is installable without cloning the full repository. Users get the platform via a package manager.
- Instance initialization completes in a single command. The resulting instance passes `sprue verify` with zero violations and is immediately operable by the LLM agent (engine files are readable, protocols are present, config resolves).
- The engine ships defaults that produce an instance passing all validators without any configuration beyond identity. Identity is the only required input — a single sentence defining audience and scope.
- Instance configuration is optional and minimal. Only what differs from platform defaults needs to be specified. Unmentioned values inherit defaults.
- Engine upgrades preserve instance configuration, content, and state. Only engine files are replaced. Schema changes are backward-compatible within a compatibility window, or include migration tooling. Migration tooling may be automated or guided instructions produced by the CLI.
- A failed or interrupted upgrade leaves the instance in a usable state. The previous engine state is preserved if the upgrade does not complete fully.
- Engine upgrades are user-initiated. The engine never modifies instance files without an explicit upgrade command.
- The engine declares a schema compatibility window. Instances created under schema version N are operable by engine versions supporting schema N. Schema upgrades are explicit and user-initiated.
- The distributed package is verifiable against the public source repository. Package builds are reproducible.
- Re-initializing an existing instance is refused by default. Users must explicitly opt in to overwrite.
- The engine contains no instance-specific content — no raw files, no wiki pages, no memory state, no instance identity. These belong entirely to the instance.
- Multiple instances can coexist on the same machine, each with independent content and state, sharing the same engine installation.
- The platform provides both a CLI entry point (for mechanical operations) and an LLM agent entry point (for knowledge work). Both share the same engine and configuration.
- All engine files are locally readable by the LLM agent at runtime. The agent accesses protocols, engine docs, and defaults as files on disk, not as opaque package internals.
- The engine makes no network requests. All operations are local. No telemetry, no phone-home.
- Instances are portable across machines. Moving an instance directory to a new machine with the same engine version installed yields a functional KB without reconfiguration.
- Engine files copied into the instance (`.sprue/`) are plain text suitable for version control. Users may commit them to preserve engine-version reproducibility.

## Rationale

The platform/instance split (ADR-0007) already achieves clean separation at the directory level. The engine protocols, scripts, and defaults are domain-agnostic. But distribution is still coupled — the only way to create a new instance today is to clone the monorepo and delete the existing instance's content. This blocks adoption by anyone who wants to build a cooking KB, a legal KB, or a medical KB without inheriting a technology reference.

Formalizing the distribution model transforms the platform from a personal tool into a product. The 25+ ADRs, 15 protocols, and verification pipeline represent 19 months of operational knowledge that others could use immediately — if they could install it. The single-command initialization invariant ensures that the barrier to adoption is as low as possible, with identity as the only required input.

The local-readability invariant exists because the LLM agent is the primary consumer of engine files. Protocols are prose-as-code — the LLM must read them from disk to execute operations. Burying engine files in opaque package internals would break the execution model that makes this platform work.

## Enforcement

| Invariant | Enforcement | Mechanism |
|---|---|---|
| Installable via package manager | Structural | PyPI package build + `pip install sprue` |
| Single-command init passes verify | Validator | `sprue verify` runs post-init; CI tests scaffold-then-verify |
| Defaults produce valid instance | Validator | `sprue verify` on a fresh init with identity-only input |
| Upgrades preserve instance content | Structural | `.sprue/` is the only directory touched by `sprue upgrade` |
| Upgrade atomicity | Structural | Upgrade writes to temp directory, then atomic rename |
| Explicit upgrade | Structural | No auto-upgrade code path exists in the CLI |
| Schema compatibility window | Validator | `check-config.py` asserts schema version is within supported range |
| Artifact integrity | Best-effort | Reproducible builds; users can diff package contents against source repo tag |
| Init idempotency | Structural | `sprue init` checks for existing `.sprue/` and refuses without `--force` |
| No instance content in engine | Validator | `pyproject.toml` package inclusion rules + optional CI check against instance paths |
| Multiple instances coexist | Structural | No shared state; each instance is self-contained |
| CLI + agent dual entry points | Structural | Separate entry points in package; both use same config loader |
| Engine files locally readable | Structural | `sprue init` copies files to `.sprue/` as plain text |
| No network requests | Best-effort | Code review; no HTTP/network imports in engine modules |
| Portability | Structural | `.sprue/` committed to git; no absolute paths in engine files |
| Git-committable engine files | Structural | All `.sprue/` files are plain text (`.md`, `.yaml`, `.sh`, `.py`) |

## Decisions

- [ADR-0006: Configuration Layering](../decisions/0006-configuration-layering.md) — platform defaults + instance overrides with deep-merge semantics
- [ADR-0007: Platform/Instance Architecture](../decisions/0007-platform-instance-architecture.md) — reusable engine decoupled from domain identity
- [ADR-0030: Rename platform/ to sprue/, Split Contributor Docs](../decisions/0030-rename-platform-to-sprue-split-docs.md) — directory boundary = shipping boundary
- [ADR-0031: Product Name — Sprue](../decisions/0031-product-name-sprue.md) — naming choice and rationale

## Design

- [Sprue Distribution Model](../design/sprue-distribution.md) — hybrid pip CLI + local file copy distribution model
