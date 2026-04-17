# Platform Development Process

How the LLM Wiki Platform itself is developed. This document describes the artifact layers, how work flows through them, and the execution model that makes this platform distinctive.

Audience: platform developers and contributors. For how the platform *operates* (commands, schemas, constraints), see `sprue/engine.md`. For how to *use* the platform as a KB operator, see `sprue/README.md`.

## The Six-Layer Stack

The platform is built from six distinct artifact layers. Each layer has a different purpose, audience, abstraction level, and rate of change.

| Layer | Directory | Purpose | Audience | Changes When |
|-------|-----------|---------|----------|--------------|
| Specs | `docs/specs/` | Product intent — WHAT the platform does | Platform developers | Product vision changes |
| Design Docs | `docs/design/` | Technical architecture — high-level HOW | Platform developers | Architecture evolves |
| ADRs | `docs/decisions/` | Decisions — WHICH choices and WHY | Future selves | New decision made |
| Plans | `docs/plans/` | Task breakdowns — WHAT to do in what order | Implementing agents | New feature started |
| Protocols | `sprue/protocols/` | Prose code — LLM-executable implementation | LLM runtime | Implementation improves |
| Config | `sprue/defaults.yaml` | Tuning knobs — thresholds, vocabularies, limits | Instance operators | Tuning for a domain |
| Validators | `sprue/scripts/` | Executable assertions — the test suite | CI pipeline | Specs or design change |

The layers are ordered by abstraction. Specs are the most abstract (no implementation details). Validators are the most concrete (executable shell and Python). Each layer builds on the one above it.

### Specs

A spec describes WHAT the platform does from a product perspective. It is implementation-agnostic — a spec makes sense even if the entire technical architecture changed. Specs capture product intent before any design work begins.

A spec answers: What problem does this solve? What properties must the output have? What invariants must always hold? What is explicitly out of scope?

Example: "Every factual claim must be traceable to a human-produced source" is a spec-level statement. It says nothing about how sources are stored, how claims are extracted, or which LLM model does the checking. Those are design and implementation concerns.

Specs come BEFORE ADRs. They define the intent that ADRs record decisions about. A feature might reference an existing spec (most new work serves an existing product guarantee) or require a new one (when the platform takes on a genuinely new capability).

Specs live in `docs/specs/`. They are named descriptively, not numbered chronologically, because they represent product capabilities with no meaningful ordering — unlike ADRs, where chronological sequence is load-bearing (later decisions build on earlier ones).

### Design Docs

A design doc describes HOW a feature is built at a high level. It takes a spec's intent and proposes an architecture: which components interact, how data flows, what state model applies, what trade-offs were accepted. Design docs are where technical philosophy lives — the decisions about mechanisms, patterns, and system shape.

Design docs are technical but not procedural. They describe the architecture of a solution without specifying step-by-step execution. If numbered steps appear, the content belongs in a protocol, not a design doc.

Example: "The platform uses prose-as-code — markdown protocols interpreted by an LLM runtime" is a design-level statement. It describes a technical approach that serves the product specs, explains why it was chosen, and defines its properties. The step-by-step instructions the LLM follows are protocol-level, not design-level.

Design docs may be ephemeral in the sense that the implementation can diverge from the original plan. The ADRs capture the decisions that survive; the design doc captures the thinking that led to them.

Design docs live in `docs/design/`.

### ADRs

An Architecture Decision Record captures a single decision with its context, the choice made, alternatives considered, and consequences. ADRs are the "why" layer — they explain reasoning that might otherwise seem arbitrary to a future reader.

ADRs are NOT the starting point for new work. They are produced DURING design and implementation, as decisions crystallize. A feature might produce zero ADRs (if it follows existing patterns) or several (if it requires novel choices).

The existing 25 ADRs follow a consistent format: YAML frontmatter (`status`, `date`), then Context, Decision, Alternatives Considered, Consequences, and optionally Config Impact. This format is established and should not change.

ADRs live in `docs/decisions/`. See `docs/decisions/README.md` for the full index.

### Plans

A plan is an ordered task breakdown written AFTER design and BEFORE implementation. It tells the implementing agent exactly what to build, in what order, touching which files. Plans are the bridge between "we know HOW to build it" (design) and "we're building it" (implement).

Plans are feature-scoped, not mechanism-scoped. A plan answers: What are the ordered steps? Which files are created or modified? What are the acceptance criteria for each step? What depends on what?

Plans are committed to the feature branch as the first commit and kept as permanent records after the feature ships. They serve as historical records of how features were built — useful for understanding implementation decisions that don't rise to ADR level.

Plans live in `docs/plans/`. See `docs/plans/README.md` for the template.

### Protocols

Protocols are the implementation layer. They are **prose code** — markdown files written in imperative style that an LLM runtime interprets and executes. Protocols are NOT documentation. They are instructions the LLM follows to perform operations.

The distinction matters: documentation explains how something works so a reader understands it. A protocol tells the LLM exactly what to do so it produces correct behavior. Protocol quality is measured the same way code quality is measured — by whether the executor (the LLM) produces correct output when following the steps.

This means protocols are optimized for determinism, not readability. They avoid hedging language ("consider", "you might want to") in favor of deterministic directives ("classify as X if Y", "skip if Z"). When judgment is required, the protocol provides explicit criteria and classification tiers. An instruction that is clear to a human but ambiguous to an LLM is a bug.

Protocols reference config values via `config.dotpath` notation rather than hardcoding thresholds. They delegate to Python scripts for mechanical work (index building, tag validation) while retaining judgment-requiring steps (classification, content assessment) for the LLM.

Protocols live in `sprue/protocols/`.

### Config

Config is the layer of tuning knobs — numeric thresholds, vocabularies, limits, and heuristics. Platform defaults live in `sprue/defaults.yaml`; instance overrides live in `instance/config.yaml`. Config values are referenced by protocols and consumed by scripts.

The config layer exists to externalize values that would otherwise be magic numbers scattered through protocols and scripts. The litmus test from `sprue/engine.md` applies: "Would a cooking KB, a finance KB, and a tech KB all want the same value?" If yes, it is a platform invariant (baked into protocol prose). If no, it is a tunable (lives in config).

Config is the most frequently changed layer. Adjusting a threshold or adding a facet vocabulary entry requires no protocol changes, no design docs, no ADRs.

### Validators

The Python scripts in `sprue/scripts/` are executable assertions. They verify that content, configuration, and state conform to platform invariants. They are the test suite, not tooling.

The distinction from "tooling" is precise: tooling helps do work (a formatter, a scaffolder, a migration script). Validators verify that the work is correct. `check-tags.py` asserts that frontmatter tags are valid. `check-config.py` asserts that configuration is consistent. `verify.py` runs all structural checks from `memory/rules.yaml`. The CI pipeline runs validators on every push. The LLM runs them inline during operations — `compile.md` calls `bash sprue/verify.sh --file <path>` before considering a page complete.

Some scripts straddle the line: `build-index.py` generates derived state AND validates it. `decay.py` calculates and applies confidence decay. These dual-purpose scripts still function primarily as assertions — the generated artifacts are derived state that must be reconstructable from source (Design Principle 6: "Everything regenerable is regenerated").

Validators live in `sprue/scripts/`. The runner is `sprue/verify.sh`.

---

## The Prose-as-Code Execution Model

The platform has two kinds of executable artifacts: Python scripts and Markdown protocols. Python scripts execute on CPython. Protocols execute on an LLM. Both are code in the meaningful sense — they have inputs, produce outputs, can be buggy, and must be tested.

### How the LLM Executes Protocols

The LLM runtime loads a protocol by reading it into its context window. The protocol's instructions become the LLM's program:

| Protocol Element | Code Analog |
|-----------------|-------------|
| Step numbers | Program counter |
| Decision trees, classification tiers | Control flow (if/else, switch) |
| `config.dotpath` references | Variable lookups |
| "Read `sprue/engine.md`" | Import statement |
| "Present to user, wait for approval" | I/O, blocking call |
| "Run `bash sprue/verify.sh`" | Foreign function call |
| "Append to `instance/state/compilations.yaml`" | Write to database |

The boot sequence follows a defined import chain:

```
AGENTS.md (entry point)
  loads engine.md (kernel)
    dispatches to protocol/*.md (procedure)
      reads defaults.yaml + config.yaml (runtime config)
      calls scripts/*.py (deterministic subroutines)
      reads/writes state/*.yaml (append-only state)
      reads memory/rules.yaml (runtime assertions)
```

### The Division of Labor

Protocols and Python scripts have complementary roles:

| Work Type | Handled By | Why |
|-----------|-----------|-----|
| Classification, synthesis, assessment | Protocol (LLM) | Requires understanding of content, context, and domain |
| Index building, hashing, scoring | Script (Python) | Requires deterministic, reproducible output |
| Facet assignment, page generation | Protocol (LLM) | Requires judgment and emergent vocabulary awareness |
| Frontmatter validation, tag checking | Script (Python) | Requires exhaustive schema checking |
| Source fetching, claim extraction | Protocol (LLM) | Requires reading comprehension and authority assessment |
| Config merging, decay calculation | Script (Python) | Requires arithmetic precision |

The principle: scripts handle what can be computed; protocols handle what requires understanding.

### Implications for Protocol Development

Because protocols are code:

- **Ambiguity is a bug.** An instruction clear to a human but ambiguous to an LLM produces inconsistent behavior. Protocols must be precise enough for deterministic execution.
- **Testing is mandatory.** Every protocol invokes `bash sprue/verify.sh` to validate its output. A protocol that produces content failing validation is broken, like code that fails its test suite.
- **Refactoring is possible.** Protocol steps can be reordered, merged, or split — as long as the output still meets the spec. The spec defines correctness; the protocol defines mechanism.
- **Version control matters.** Protocol changes are code changes. They should be reviewed with the same scrutiny as a Python script change.

---

## How Work Flows Through the Layers

Not every change touches every layer. The path through the stack depends on the scope and nature of the change.

### New Feature: Full Stack

When introducing a new user-visible capability:

1. **Spec** — Write or update a spec capturing product intent. What problem does this solve? What properties must the output have? What invariants must hold?
2. **Design Doc** — Write a design doc proposing architecture. Which components, how data flows, what trade-offs.
3. **ADRs** — As design decisions crystallize, capture each in an ADR. Not every design decision needs an ADR — only those where the choice was non-obvious or where viable alternatives existed.
4. **Plan** — Write a task breakdown in `docs/plans/<feature>.md`. Ordered steps, file paths, acceptance criteria. Commit this as the first commit on the feature branch. Implementing agents read this before writing code.
5. **Protocol** — Write or modify the protocol that implements the behavior. This is where the LLM learns the new feature.
6. **Config** — Externalize tunable values. Add to `sprue/defaults.yaml` with sensible defaults.
7. **Validators** — Write or extend scripts to assert the new invariants hold.

Example: The verification pipeline (ADR-0009) introduced adversarial fact-checking. The product intent: "high confidence is earned through independent verification against authoritative sources." The design: tiered source escalation with a writer/critic/judge model. The ADR: why three roles instead of single-pass review. The plan: ordered tasks from source model implementation through validator wiring. The protocol: `sprue/protocols/verify.md` with step-by-step instructions. The config: `verify.weights`, `verify.cooldown_days`. The validator: rules in `memory/rules.yaml` checking that confidence:high requires last_verified.

### Behavioral Change: Protocol + Config

When the change modifies HOW an existing feature works without changing WHAT it does:

1. Skip specs (product intent unchanged).
2. Skip design docs (architecture unchanged).
3. An ADR may be warranted if the change involves a non-obvious choice.
4. Write a plan if the change involves multiple steps across files.
5. Update the protocol and/or config.
6. Update validators if invariants changed.

Example: Adjusting the compile classification tiers from three to four categories. The product intent (transform raw sources into wiki pages) is unchanged. The architecture (three-command pipeline) is unchanged. But the implementation detail (how candidates are classified) changed, possibly warranting an ADR if the alternatives were debated.

### Bug Fix or Tuning: Config or Validator Only

The simplest path. A threshold is wrong, a script has a bug, a config value needs adjustment. Touch only the affected layer. No spec, no design doc, no ADR unless the fix reveals a design flaw that requires a decision.

Example: Changing `facets.domain.creation_threshold` from 10 to 15 after observing premature domain creation. Pure config change — no protocol, design, or spec work needed.

---

## Relationships Between Layers

```
Specs ────────► Design Docs ────────► Protocols
                     │                     │
                     ▼                     ▼
                   ADRs              Config + Validators
```

**Specs drive Design Docs.** A spec's intent constrains the solution space for the design. "Every fact traces to a human-produced source" constrains the design to include a source authority model, tiered verification, and provenance tracking.

**Design Docs produce ADRs.** Decisions made during design are captured as ADRs. Not every design decision needs an ADR — only those where the choice was non-obvious or where alternatives were genuinely viable. ADR-0003 (three-command pipeline) emerged from the design of the content pipeline. ADR-0012 (agent memory) emerged from the design of the learning system.

**Design Docs inform Protocols.** The design's architecture becomes the protocol's structure. A design that says "verification uses a tiered source authority model" becomes `verify.md`'s four-phase procedure with source escalation ladder.

**Protocols consume Config.** Protocols reference config values via `config.dotpath` instead of hardcoding thresholds. This separates what changes frequently (tuning) from what changes rarely (logic).

**Validators enforce Specs via Protocols.** Scripts assert that protocol outputs conform to platform invariants. These invariants originate in specs (product-level guarantees) and are implemented through protocols (LLM-executable procedures). Validators close the loop by checking that the implementation actually respects the spec.

**ADRs are retrospective, not prescriptive.** ADRs explain why the protocols and config are the way they are. They are the archaeological record, not the blueprint. Reading ADRs tells a future developer "why was it done this way?" — the answer to the question that specs (what) and design docs (how) don't address.

---

## What Lives Where

Quick-reference for platform developers.

| Artifact | Location | Naming | Example |
|----------|----------|--------|---------|
| Product spec | `docs/specs/` | Descriptive slug | `source-grounded-knowledge.md` |
| Design doc | `docs/design/` | Descriptive slug | `prose-as-code.md` |
| Architecture decision | `docs/decisions/` | `NNNN-slug.md` (numbered) | `0009-verification-pipeline.md` |
| Feature plan | `docs/plans/` | `feature-slug.md` | `kb-init.md`, `source-backfill.md` |
| Operation protocol | `sprue/protocols/` | `operation.md` | `compile.md`, `verify.md` |
| Platform config | `sprue/defaults.yaml` | Single file | All tunables with defaults |
| Instance overrides | `instance/config.yaml` | Single file | Only what differs |
| Validator script | `sprue/scripts/` | `check-*.py`, `*.py` | `check-tags.py`, `verify.py` |
| Prompt template | `sprue/prompts/` | `strategy.md` | `wiki_page.md`, `key_claims.md` |
| Pipeline schema | `sprue/schemas/` | `*.yaml` | `pipeline.yaml` |
| Compile profile | `sprue/profiles/` | `name.yaml` | `flashcards.yaml` |

---

## When to Write a Spec

A spec is warranted when:

- The change introduces a new user-visible capability (a new command, a new automation mode, a new classification dimension).
- The product intent needs to be captured before design begins.
- Multiple design approaches are possible and the spec constrains which are viable.
- A guarantee is being made to users that must survive implementation changes.

A spec is NOT needed for: implementation refactors, config tuning, protocol bug fixes, adding validators, adding a new page type that follows existing patterns.

Specs use a lightweight format: YAML frontmatter (`status`, `date`), then sections for Intent, Invariants, Rationale, and links to related Decisions. See `docs/specs/README.md` for the template.

## When to Write a Plan

A plan is warranted when:

- The implementation involves multiple files or steps that must be ordered.
- An agent (or multiple agents) will implement the work and needs a concrete task list before starting.
- The feature branch will have more than 2-3 commits.

A plan is NOT needed for: single-file bug fixes, config tuning, documentation improvements, or any change where the implementation is obvious from the design doc or ADR alone.

Plans use a lightweight format: YAML frontmatter (`feature`, `status`, `date`), then sections for Tasks (ordered checklist with file paths), Dependencies (which tasks depend on others), and Acceptance Criteria. See `docs/plans/README.md` for the template.

## When to Write a Design Doc

A design doc is warranted when:

- A new technical mechanism is being introduced (a new state model, a new verification approach, a new classification algorithm).
- The architecture is not obvious from reading the protocol alone — the reader needs to understand the system-level thinking.
- Trade-offs were evaluated and the design doc captures the reasoning before it fades.

A design doc is NOT needed for: threshold tuning, bug fixes, adding content to an existing page type, extending a facet vocabulary.

Design docs use a lightweight format: YAML frontmatter (`status`, `date`), then sections for Overview, Context, Architecture, Interfaces, and links to related Specs and Decisions. See `docs/design/README.md` for the template.

## When to Write an ADR

An ADR is warranted when:

- The decision has genuine alternatives — if there is only one reasonable choice, no ADR needed.
- A future reader might ask "why was it done this way?" and not find the answer in the code or design doc.
- The decision constrains future work (establishing an invariant, choosing a data format, picking an architecture pattern).
- The decision was debated or reversed a previous approach.

An ADR is NOT needed for: bug fixes, threshold tuning, documentation improvements, adding a new page type that follows existing patterns, routine protocol updates.

Follow the established format in `docs/decisions/`: YAML frontmatter (`status`, `date`), then Context, Decision, Alternatives Considered, Consequences, optional Config Impact.
