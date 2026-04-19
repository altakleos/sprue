---
status: accepted
date: 2026-04-19
supersedes: 0026
---
# ADR-0043: Generic SDD Layer Names — Decouple Method from Sprue Artifacts

## Context

ADR-0026 adopted a six-layer development stack and named the bottom layers after Sprue's specific artifacts: Protocols (markdown prose-as-code), Config (YAML tunables), and Validators (Python `check-*.py` scripts). This conflates two concerns: the SDD *method* (specs → design → decisions → plans → implementation → verification) and Sprue's *instantiation* of that method (how each layer is realized in markdown, YAML, and Python).

Analysis performed during v0.1.x dogfooding found three problems:

1. The process doc mixes method with artifact. A reader cannot distinguish "this is how SDD works" from "this is how Sprue happens to do SDD."
2. The layer model does not absorb new Sprue artifact types gracefully. `src/sprue/engine/prompts/`, `profiles/`, and `schemas/` are part of the implementation surface but are not named as layers.
3. "Protocols" carries Sprue's most distinctive idea (prose-as-code markdown) into the abstract layer name, so the method itself appears Sprue-specific to anyone reading the process doc.

## Decision

Rename the bottom two layers in `docs/development-process.md` to method-neutral names:

- **Implementation** — artifacts that perform the operation, regardless of executor. Can be traditional code run by a CPU, prose instructions interpreted by an LLM, configuration consumed by either, or any combination.
- **Verification** — artifacts that confirm the operation met its spec, regardless of how the check is executed. Can be unit tests, type checks, executable assertions, linters, LLM-executed verification prose, or any mix.

Both descriptions are functional (what runs vs. what checks), not material (Python vs. markdown).

Move Sprue-specific instantiation into a new document, `docs/sprue-implementation.md`:

- Implementation in Sprue = `src/sprue/engine/protocols/` (prose-as-code, judgment) + `defaults.yaml` (config) + deterministic helpers in `scripts/`.
- Verification in Sprue = `scripts/check-*.py` (executable assertions) + `sprue verify` + CI.
- Load-bearing principles (prose is code, scripts compute / protocols judge, config externalization litmus test) live in that doc.

Mark ADR-0026 as `superseded` with `superseded-by: 0043`. The SDD adoption decided in 0026 stands; only the layer naming is replaced.

## Alternatives Considered

- **Do nothing — keep the Sprue-named layers.** Rejected because the process doc remains method/artifact-coupled. Contributors must learn Sprue's artifact inventory before understanding the SDD process that governs it.
- **Collapse into a single "Implementation" layer that absorbs verification.** Rejected because verification deserves peer status with implementation (tests as peer of code). Hiding verification inside implementation weakens the discipline that every spec invariant needs a check.
- **Extract SDD entirely into an external framework (GitHub Spec Kit, AWS Kiro).** Rejected for the same reason ADR-0026 rejected it: those tools assume spec → traditional code, and Sprue's implementation is already prose-as-code in markdown. This proposal keeps Sprue's process in its own repo but makes the method layer legible without requiring Sprue-specific knowledge.

## Consequences

`docs/development-process.md` reads as a generic SDD reference applied to a prose-as-code system. `docs/sprue-implementation.md` is the authoritative source for "what Implementation and Verification mean in Sprue." Every principle previously in `development-process.md` (prose as code, scripts compute / protocols judge, config externalization) moves to the Sprue-specific doc; nothing is dropped.

`AGENTS.md` task-routing sections ("Modifying a Protocol", "Tuning Config", "Adding or Fixing a Validator") remain as Sprue-specific verbs — they are correct for contributors operating on Sprue's instantiation. A preamble notes that these instantiate the generic Implementation and Verification layers.

ADR supersession is exercised for the first time in Sprue's history. This establishes the supersession workflow as real, not aspirational.

## Config Impact

- New file: `docs/sprue-implementation.md`
- Superseded: `docs/decisions/0026-spec-driven-development-process.md`
- Updated: `docs/development-process.md`, `AGENTS.md`, `docs/decisions/README.md`, `docs/design/plans-layer.md`, `docs/operations/release-playbook.md`, `src/sprue/engine/engine.md`, `src/sprue/engine/README.md`, `.kiro/steering/contributor.md`, `CHANGELOG.md`

## References

- [ADR-0026: Spec-Driven Development Process](0026-spec-driven-development-process.md) — established the SDD method; superseded only for layer naming
- [ADR-0029: Plans Layer](0029-plans-layer.md) — adds plans between ADRs and implementation
- [ADR-0035: ADR-Lite Format](0035-adr-lite-format.md) — two-tier decision records
- [development-process.md](../development-process.md) — generic SDD reference
- [sprue-implementation.md](../sprue-implementation.md) — Sprue's instantiation of the bottom layers
