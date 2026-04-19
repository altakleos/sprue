# Sprue's Instantiation of the SDD Stack

The development process in [`development-process.md`](development-process.md) describes Spec-Driven Development as a method: seven generic layers (Specs → Design → ADRs → Plans → Implementation → Verification, with Plans between ADRs and Implementation). This document describes how Sprue specifically instantiates the bottom two layers — **Implementation** and **Verification** — and carries the load-bearing principles that make Sprue's instantiation distinctive.

For the generic method, read `development-process.md`. For Sprue's artifact choices, read this doc.

## Implementation Layer

Implementation in Sprue is realized across three artifact types, all under `src/sprue/engine/`:

| Artifact type | Location | Executor | Role |
|---|---|---|---|
| Prose-as-code protocols | `src/sprue/engine/protocols/*.md` | LLM runtime | Judgment-requiring operations (classification, synthesis, authority assessment) |
| Tunable configuration | `src/sprue/engine/defaults.yaml` | Both | Thresholds, vocabularies, limits, heuristics |
| Deterministic helpers | `src/sprue/engine/scripts/*.py` (non-`check-*`) | CPython | Mechanical work (hashing, index building, decay arithmetic) |

### Prose-as-Code Protocols

Sprue's protocols are markdown files, but they are **code**, not documentation. An LLM runtime reads them into its context window and executes the instructions step by step. See [design/prose-as-code.md](design/prose-as-code.md) for the execution model.

Key implications:

- Ambiguity is a bug. An instruction clear to a human but ambiguous to an LLM produces inconsistent behavior.
- Protocols reference config values via `config.dotpath` notation rather than hardcoding thresholds.
- Protocols delegate to Python helpers for mechanical work, reserving the LLM for judgment.

### Configuration

Every tunable value — thresholds, vocabularies, limits — lives in `defaults.yaml`, consumed by both protocols and scripts via the loader in `src/sprue/engine/scripts/config.py`. Instance operators override selected keys in `instance/config.yaml` via deep merge.

**Litmus test for "is this a tunable?"** — Would a cooking KB, a finance KB, and a tech KB all want the same value? If yes → platform invariant, bake into protocol prose. If no → tunable, add to `defaults.yaml`.

### Deterministic Helpers

Not every Python script in `scripts/` is a validator. Some (e.g., `build-index.py`, `decay.py`, `prioritize.py`) generate derived state or perform arithmetic. These are Implementation-layer helpers that protocols invoke for work that requires reproducibility, not judgment.

## Verification Layer

Verification in Sprue is the set of artifacts that confirm Implementation met its specs. Every spec invariant that can be checked mechanically has a check.

| Artifact type | Location | Executor | Role |
|---|---|---|---|
| Executable assertions | `src/sprue/engine/scripts/check-*.py` | CPython | Structural checks (frontmatter, tags, wikilinks, placement) |
| Rule catalog | `memory/rules.yaml` | CPython (via `verify.py`) | Registry of invariants with their check commands |
| Orchestrator | `src/sprue/engine/scripts/verify.py` | CPython | Runs all rules from `rules.yaml` |
| Top-level runner | `sprue verify` (CLI) and `verify.sh` (shell) | CPython | Entry point for CI and inline invocation |

### How Verification Fits Implementation

Sprue's `compile.md` protocol calls `bash verify.sh --file <path>` before considering a page complete. This is verification-as-inline-check: the LLM runs the verifier on its own output, and a failure is treated as a bug in the produced content, not a suggestion. See [decisions/0013-tooling-and-ci-pipeline.md](decisions/0013-tooling-and-ci-pipeline.md) for the full CI story.

## Load-Bearing Principles

These are Sprue-specific principles. They are not requirements of SDD as a method — they are choices Sprue made and should survive any future instantiation changes.

1. **Prose is code.** Protocols are executable instructions, not documentation. Reviewed, versioned, and tested like any other code.
2. **Scripts compute, protocols judge.** Deterministic work goes to Python. Judgment and synthesis go to LLM protocols. The split is principled, not accidental.
3. **Config over hardcoding.** No magic numbers in protocol prose. Every tunable is in `defaults.yaml` with a comment.
4. **Validators close the loop.** Every spec invariant that can be checked mechanically has a `check-*.py`.
5. **Cross-link, don't duplicate.** Point to the authoritative source; never copy content between layers.

## Where to Look for What

| Question | Read |
|---|---|
| "How is SDD supposed to flow?" | [`development-process.md`](development-process.md) |
| "Where is the decision that set the layer names?" | [`decisions/0043-generic-sdd-layers.md`](decisions/0043-generic-sdd-layers.md) |
| "What is the prose-as-code execution model?" | [`design/prose-as-code.md`](design/prose-as-code.md) |
| "Where are the tunables?" | `src/sprue/engine/defaults.yaml` |
| "How do I add a validator?" | [`../AGENTS.md`](../AGENTS.md) § Adding or Fixing a Validator |
