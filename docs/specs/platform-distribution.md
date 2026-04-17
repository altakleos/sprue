---
status: draft
date: 2026-04-16
---
# Platform Distribution

## Intent

The platform is distributed as **Sprue** — an installable product that any knowledge domain can adopt without forking or disentangling engine from content. Users install Sprue, run an initialization command, and get a working KB instance with identity, configuration, and empty content directories. The current monorepo (engine + one instance) is split into a reusable engine package and per-domain instances that depend on it.

## Invariants

- The engine is installable without cloning the full repository. Users get the platform via a package manager.
- Instance initialization is a single command that scaffolds identity, configuration, and directory structure. A new user goes from zero to a working KB in minutes, not hours.
- The engine ships with sensible defaults that produce a working KB without any configuration. Identity is the only required input — a single sentence defining audience and scope.
- Instance configuration is optional and minimal. Only what differs from platform defaults needs to be specified. Unmentioned values inherit defaults.
- Engine upgrades do not overwrite instance configuration, content, or state. The deep-merge model, three-tier separation, and schema versioning ensure backward compatibility. Schema changes are backward-compatible or include automated migration.
- The engine contains no instance-specific content — no raw files, no wiki pages, no memory state, no instance identity. These belong entirely to the instance.
- Multiple instances can coexist on the same machine, each with independent content and state, sharing the same engine installation.
- The platform provides both a CLI entry point (for mechanical operations) and an LLM agent entry point (for knowledge work). Both share the same engine and configuration.
- All engine files are locally readable by the LLM agent at runtime. The agent accesses protocols, engine docs, and defaults as files on disk, not as opaque package internals.
- The engine makes no network requests. All operations are local. No telemetry, no phone-home.
- Instances are portable. A KB directory can be moved to another machine with the same engine version installed and function without reconfiguration.

## Rationale

The platform/instance split (ADR-0007) already achieves clean separation at the directory level. The engine protocols, scripts, and defaults are domain-agnostic. But distribution is still coupled — the only way to create a new instance today is to clone the monorepo and delete the existing instance's content. This blocks adoption by anyone who wants to build a cooking KB, a legal KB, or a medical KB without inheriting a technology reference.

Formalizing the distribution model transforms the platform from a personal tool into a product. The 25+ ADRs, 15 protocols, and verification pipeline represent 19 months of operational knowledge that others could use immediately — if they could install it. The zero-friction onboarding invariant (single command, sensible defaults, identity as the only input) ensures that the barrier to adoption is as low as possible.

The local-readability invariant exists because the LLM agent is the primary consumer of engine files. Protocols are prose-as-code — the LLM must read them from disk to execute operations. Burying engine files in opaque package internals would break the execution model that makes this platform work.

## Decisions

- [ADR-0006: Configuration Layering](../decisions/0006-configuration-layering.md) — platform defaults + instance overrides with deep-merge semantics
- [ADR-0007: Platform/Instance Architecture](../decisions/0007-platform-instance-architecture.md) — reusable engine decoupled from domain identity
- [ADR-0030: Rename platform/ to sprue/, Split Contributor Docs](../decisions/0030-rename-platform-to-sprue-split-docs.md) — directory boundary = shipping boundary
- [ADR-0031: Product Name — Sprue](../decisions/0031-product-name-sprue.md) — naming choice and rationale

## Design

- [Sprue Distribution Model](../design/sprue-distribution.md) — hybrid pip CLI + local file copy distribution model
