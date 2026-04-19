# SDD Development Process

How this project is developed. This document describes Spec-Driven Development (SDD) as a method — the artifact layers, how work flows through them, and when each layer is required. It is method-neutral: layers are defined functionally (what runs vs. what checks), not materially (Python vs. markdown).

For Sprue's specific instantiation of the bottom two layers (what Implementation and Verification mean in this project), see [sprue-implementation.md](sprue-implementation.md).

Audience: platform contributors. For how the platform *operates* as a KB engine, see [engine.md](../src/sprue/engine/engine.md). For how to *use* the platform as a KB operator, see the [engine README](../src/sprue/engine/README.md).

## The Layer Stack

The project is built from seven artifact layers. Each has a different purpose, audience, abstraction level, and rate of change.

| Layer | Directory | Purpose | Audience | Changes When |
|-------|-----------|---------|----------|--------------|
| Specs | `docs/specs/` | Product intent — WHAT the project does | Contributors | Product vision changes |
| Design Docs | `docs/design/` | Technical architecture — high-level HOW | Contributors | Architecture evolves |
| ADRs | `docs/decisions/` | Decisions — WHICH choices and WHY | Future selves | New decision made |
| Plans | `docs/plans/` | Task breakdowns — WHAT to do in what order | Implementing agents | New feature started |
| Implementation | project-specific | Artifacts that perform operations | Executor (CPU or LLM) | Implementation improves |
| Verification | project-specific | Artifacts that confirm operations met their specs | CI, executor | Specs or implementation change |

Layers are ordered by abstraction. Specs are the most abstract (no implementation details). Verification is the most concrete (executable assertions or semi-mechanical checks). Each layer builds on the one above it.

### Specs

A spec describes WHAT the project does from a product perspective. It is implementation-agnostic — a spec makes sense even if the entire technical architecture changed. Specs capture product intent before any design work begins.

A spec answers: What problem does this solve? What properties must the output have? What invariants must always hold? What is explicitly out of scope?

Example: "Every factual claim must be traceable to a human-produced source" is a spec-level statement. It says nothing about how sources are stored, how claims are extracted, or which executor does the checking. Those are design and implementation concerns.

Specs come BEFORE ADRs. They define the intent that ADRs record decisions about. A feature might reference an existing spec (most new work serves an existing product guarantee) or require a new one (when the project takes on a genuinely new capability).

Specs live in `docs/specs/`. They are named descriptively, not numbered chronologically, because they represent product capabilities with no meaningful ordering — unlike ADRs, where chronological sequence is load-bearing (later decisions build on earlier ones).

### Design Docs

A design doc describes HOW a feature is built at a high level. It takes a spec's intent and proposes an architecture: which components interact, how data flows, what state model applies, what trade-offs were accepted. Design docs are where technical philosophy lives — the decisions about mechanisms, patterns, and system shape.

Design docs are technical but not procedural. They describe the architecture of a solution without specifying step-by-step execution. If numbered steps appear, the content belongs in an implementation artifact, not a design doc.

Design docs may be ephemeral in the sense that the implementation can diverge from the original plan. The ADRs capture the decisions that survive; the design doc captures the thinking that led to them.

Design docs live in `docs/design/`.

### ADRs

An Architecture Decision Record captures a single decision with its context, the choice made, alternatives considered, and consequences. ADRs are the "why" layer — they explain reasoning that might otherwise seem arbitrary to a future reader.

ADRs are NOT the starting point for new work. They are produced DURING design and implementation, as decisions crystallize. A feature might produce zero ADRs (if it follows existing patterns) or several (if it requires novel choices).

ADRs follow a consistent format: YAML frontmatter (`status`, `date`), then Context, Decision, Alternatives Considered, Consequences, and optionally Config Impact. ADRs are **immutable** once accepted. To reverse a decision, write a new ADR that supersedes it and set the old one's status to `superseded`.

ADRs live in `docs/decisions/`. See `docs/decisions/README.md` for the full index.

### Plans

A plan is an ordered task breakdown written AFTER design and BEFORE implementation. It tells the implementing agent exactly what to build, in what order, touching which files. Plans are the bridge between "we know HOW to build it" (design) and "we're building it" (implement).

Plans are feature-scoped, not mechanism-scoped. A plan answers: What are the ordered steps? Which files are created or modified? What are the acceptance criteria for each step? What depends on what?

Plans are committed to the feature branch as the first commit and kept as permanent records after the feature ships. They serve as historical records of how features were built — useful for understanding implementation decisions that don't rise to ADR level.

Plans live in `docs/plans/`. See `docs/plans/README.md` for the template.

### Implementation

Implementation is the layer that performs operations. The artifacts at this layer can be:

- Traditional code run by a CPU (Python, TypeScript, etc.).
- Prose instructions interpreted by an LLM runtime.
- Configuration consumed by either.
- Any combination.

What matters is that the artifact produces the behavior the spec requires. The split between Implementation and Verification is functional (what runs vs. what checks), not material (Python vs. markdown).

A project using prose-as-LLM-instructions as its primary implementation medium must still treat that prose as code — reviewed, versioned, and tested like any other code. Ambiguity in an instruction is a bug in the same sense that an undefined variable is a bug.

For Sprue's instantiation of Implementation (prose-as-code protocols, YAML config, deterministic Python helpers), see [sprue-implementation.md](sprue-implementation.md).

### Verification

Verification is the layer that confirms Implementation met its spec. The artifacts at this layer can be:

- Unit tests and integration tests run by a test framework.
- Type checks, linters, and static analysis.
- Executable assertions (e.g., `check-*` scripts).
- Prose instructions directing an LLM to verify that expectations were met.
- Human review procedures expressed as executable checklists.

What matters is that every spec invariant has a mechanical or semi-mechanical check. Verification is not "tooling" — tooling helps do work (a formatter, a scaffolder, a migration script); verification confirms that the work is correct. Verifiers may run on a CPU, in an LLM, or both, but they must be invokable deterministically enough that the same input produces the same pass/fail result.

For Sprue's instantiation of Verification (`check-*.py`, `sprue verify`, CI), see [sprue-implementation.md](sprue-implementation.md).

---

## How Work Flows Through the Layers

Not every change touches every layer. The path through the stack depends on the scope and nature of the change.

### New Feature: Full Stack

When introducing a new user-visible capability:

1. **Spec** — Write or update a spec capturing product intent. What problem does this solve? What properties must the output have? What invariants must hold?
2. **Design Doc** — Write a design doc proposing architecture. Which components, how data flows, what trade-offs.
3. **ADRs** — As design decisions crystallize, capture each in an ADR. Not every design decision needs an ADR — only those where the choice was non-obvious or where viable alternatives existed.
4. **Plan** — Write a task breakdown in `docs/plans/<feature>.md`. Ordered steps, file paths, acceptance criteria. Commit this as the first commit on the feature branch. Implementing agents read this before writing code.
5. **Implementation** — Build or modify the artifacts that produce the behavior. These may be code, prose instructions, configuration, or any combination the project's instantiation allows.
6. **Verification** — Write or extend checks to assert the new invariants hold.

### Behavioral Change: Implementation + (maybe) ADR

When the change modifies HOW an existing feature works without changing WHAT it does:

1. Skip specs (product intent unchanged).
2. Skip design docs (architecture unchanged).
3. An ADR may be warranted if the change involves a non-obvious choice.
4. Write a plan if the change involves multiple steps across files.
5. Update the Implementation artifacts.
6. Update Verification if invariants changed.

### Bug Fix or Tuning: Implementation or Verification Only

The simplest path. A threshold is wrong, a check has a bug, a configuration value needs adjustment. Touch only the affected layer. No spec, no design doc, no ADR unless the fix reveals a design flaw that requires a decision.

---

## Relationships Between Layers

```
Specs ────────► Design Docs ────────► Implementation
                     │                     │
                     ▼                     ▼
                   ADRs              Verification
```

**Specs drive Design Docs.** A spec's intent constrains the solution space for the design.

**Design Docs produce ADRs.** Decisions made during design are captured as ADRs. Not every design decision needs an ADR — only those where the choice was non-obvious or where alternatives were genuinely viable.

**Design Docs inform Implementation.** The design's architecture becomes the implementation's structure.

**Implementation consumes configuration.** Where configuration is a distinct artifact, it should be externalized from the implementation artifacts that reference it, so that tuning can happen without changing logic. What is a "tunable" versus a "baked-in invariant" is an instantiation choice and belongs in the project's instantiation doc.

**Verification enforces Specs via Implementation.** Verification artifacts assert that implementation outputs conform to spec invariants. These invariants originate in specs (product-level guarantees) and are realized through implementation. Verification closes the loop by checking that the realization actually respects the spec.

**ADRs are retrospective, not prescriptive.** ADRs explain why the implementation and design are the way they are. They are the archaeological record, not the blueprint. Reading ADRs tells a future contributor "why was it done this way?" — the answer to the question that specs (what) and design docs (how) don't address.

---

## When to Write a Spec

A spec is warranted when:

- The change introduces a new user-visible capability (a new command, a new automation mode, a new classification dimension).
- The product intent needs to be captured before design begins.
- Multiple design approaches are possible and the spec constrains which are viable.
- A guarantee is being made to users that must survive implementation changes.

A spec is NOT needed for: implementation refactors, config tuning, single-artifact fixes, adding checks, adding a new output type that follows existing patterns.

Specs use a lightweight format: YAML frontmatter (`status`, `date`), then sections for Intent, Invariants, Rationale, and links to related Decisions. See `docs/specs/README.md` for the template.

## When to Write a Plan

A plan is warranted when:

- The implementation involves multiple files or steps that must be ordered.
- An agent (or multiple agents) will implement the work and needs a concrete task list before starting.
- The feature branch will have more than 2-3 commits.

A plan is NOT needed for: single-file bug fixes, config tuning, documentation improvements, or any change where the implementation is obvious from the design doc or ADR alone.

Plans use a lightweight format: YAML frontmatter (`feature`, `serves`, `design`, `status`, `date`), then sections for Tasks (ordered checklist with file paths and inline `(depends: T1)` annotations) and Acceptance Criteria. See `docs/plans/README.md` for the template.

## How Plans Are Executed

Plans are executed by an implementing agent (LLM or human). Each task in a plan falls into one of three categories, and the execution mode differs for each:

| Task type | Examples | Execution mode |
|---|---|---|
| **Mechanical** | File edit, test run, lint fix, deterministic refactor, dependency install, read/search | Stream through. Report one line per task. |
| **Decision** | Choose between architectures, resolve scope surprise, pick a library, name a thing | Stop. Present options. Wait for input. |
| **Destructive** | `git push --force`, delete files/branches, drop DB tables, publish to PyPI, production deploy | Stop. Describe intent and blast radius. Wait for explicit approval. |

**Streaming** means: execute consecutive mechanical tasks without pausing between them. Report progress inline with a single status line per task (`✓ T3: Created lib.py`). Summarize at the end, not after each step. The user can interrupt at any time by typing any message — the agent stops and awaits direction.

**Default mode negotiation**: At the start of a plan's execution, the agent announces the plan and asks whether to execute autonomously (stream mechanical tasks, stop only at decisions and destructive ops) or step-by-step (pause after each task). If the user confirms the plan with "go", "run it", or equivalent, the default is autonomous. If the user says "walk me through it" or asks detailed questions up front, the default is step-by-step.

**Pause triggers during a streaming batch** — even in autonomous mode, the agent stops when:

- A command fails in a non-obvious way (not a typo, not a missing import — a real failure)
- An audit or investigation reveals scope materially larger than planned
- The next task would violate a spec invariant or skip a layer-stack prerequisite
- The agent is about to execute a task not in the original plan

**Anti-pattern — approval theater**: pausing between consecutive mechanical tasks to ask "continue?" when the user has no realistic reason to say no. If a user response of "next" or "continue" is repeated more than twice in a row without any course correction, the agent is over-gating. Stream.

**Progress reporting** during streaming should be terse. Group trivial steps (`✓ T3–T5: created 3 test files, all passing`). Do not re-explain the plan. Do not ask for permission to continue unless a real pause trigger fires. At batch end, summarize what changed, any deviations, and the next decision point.

## When to Write a Design Doc

A design doc is warranted when:

- A new technical mechanism is being introduced (a new state model, a new verification approach, a new classification algorithm).
- The architecture is not obvious from reading the implementation alone — the reader needs to understand the system-level thinking.
- Trade-offs were evaluated and the design doc captures the reasoning before it fades.

A design doc is NOT needed for: threshold tuning, bug fixes, adding content to an existing output type, extending a vocabulary.

Design docs use a lightweight format: YAML frontmatter (`status`, `date`), then sections for Overview, Context, Architecture, Interfaces, and links to related Specs and Decisions. See `docs/design/README.md` for the template.

## When to Write an ADR

ADRs come in two weights (see ADR-0035):

### Full ADR (~40 lines)

Use when the decision changes the **model** — new architecture, new enforcement philosophy, genuine debate with multiple viable alternatives. Format: YAML frontmatter (`status`, `date`), then Context, Decision, Alternatives Considered, Consequences, optional Config Impact.

Warranted when:
- The decision has genuine alternatives that were debated.
- A future reader might ask "why was it done this way?" and need a full narrative.
- The decision constrains future work (establishing an invariant, choosing a data format, picking an architecture pattern).
- The decision was debated or reversed a previous approach.

### ADR-lite (~12 lines)

Use when the decision changes **behavior within an existing model** — gate changes, default changes, boundary changes. Format: YAML frontmatter (`status`, `date`, `weight: lite`, `protocols: [names]`), then three fields: Decision, Why, Alternative.

Concrete triggers (any one):
1. Changes a human approval gate (adds, removes, or bypasses).
2. Changes a default that alters out-of-box behavior.
3. Moves something from blocked to allowed (or vice versa).
4. Introduces a config knob whose existence encodes a design choice.

### No ADR needed

Bug fixes, threshold tuning, documentation improvements, presentation/formatting changes, adding a new output type that follows existing patterns, routine implementation updates with no meaningful alternative.

---

## References

- [ADR-0043: Generic SDD Layer Names](decisions/0043-generic-sdd-layers.md) — why these layer names
- [ADR-0026: Spec-Driven Development Process](decisions/0026-spec-driven-development-process.md) — original SDD adoption (superseded by 0043 for layer naming; the method itself stands)
- [ADR-0029: Plans Layer](decisions/0029-plans-layer.md) — why plans exist between ADRs and Implementation
- [ADR-0035: ADR-Lite Format](decisions/0035-adr-lite-format.md) — two-tier decision records
- [sprue-implementation.md](sprue-implementation.md) — Sprue's instantiation of Implementation and Verification
