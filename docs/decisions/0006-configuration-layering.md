---
status: accepted
date: 2025-06-01
---
# ADR-0006: Configuration Layering — Platform Defaults + Instance Overrides

## Context
Configuration started as a 257-line monolith mixing platform defaults with instance-specific values. Hardcoded thresholds were scattered across engine docs and protocol files. There was no separation between "what the platform provides" and "what the instance customizes," making it impossible to ship platform upgrades without overwriting user config. A design principle attempted to draw the line between config and protocol, but it wasn't formalized.

## Decision
Adopt a three-tier configuration model: hardcoded invariants (safety rules that can't be overridden), platform defaults (defaults.yaml with every tunable value), and instance overrides (config.yaml with only what differs). Deep-merge semantics apply: scalars replace, dicts merge recursively, lists replace entirely. All thresholds, prompt heuristics, section contracts, and memory settings are externalized. Config is validated before every operation to catch inconsistencies early.

## Alternatives Considered
- **Single config file with comments marking "don't change"** — rejected because it relies on discipline rather than enforcement, and platform updates would conflict with user edits
- **Environment variables for overrides** — rejected because the config is too structured (nested facets, type schemas) for flat env vars

## Consequences
Instance authors only need to specify what's different, keeping config files small and intention-revealing. Platform upgrades can ship new defaults without touching instance config. The cost is merge-semantics complexity — users must understand that lists replace entirely, which occasionally surprises.

## Specs

- [Platform Reusability](../specs/platform-reusability.md)
