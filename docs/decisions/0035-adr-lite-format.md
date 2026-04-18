---
status: accepted
date: 2026-04-18
---
# ADR-0035: ADR-Lite Format for Protocol Behavioral Changes

## Context

During dogfooding of v0.1.x, rapid protocol iteration produced ~8 behavioral changes in one session. Four of these (compile batch approval, expand default mode, expand scoped-topic bypass, expand facet soft gate) were genuine decisions with alternatives — but none received ADRs because the full format (Context, Decision, Alternatives Considered, Consequences, ~40 lines) felt disproportionate to changes that took 2–5 minutes to implement.

The development process (ADR-0026) says ADRs are "NOT needed for routine protocol updates" but doesn't define a middle tier between full ADRs and commit messages. Protocol changes in a prose-as-code system ARE code changes — they alter LLM behavior. Some warrant a decision record but not a full architectural narrative.

## Decision

Introduce **ADR-lite** — a stripped-down decision record for protocol behavioral changes that don't warrant full ADRs. ADR-lites use the same `docs/decisions/` directory, the same numbering sequence, and the same README index. They are distinguished by `weight: lite` in YAML frontmatter.

Format:

```markdown
---
status: accepted
date: YYYY-MM-DD
weight: lite
protocols: [protocol-name]
---
# ADR-NNNN: One-line description

**Decision:** What was done, in 1–2 sentences.

**Why:** The reasoning, in 1–2 sentences.

**Alternative:** What else was considered. One sentence. Or "None — straightforward improvement."
```

Maximum 15 lines. Three required fields: Decision, Why, Alternative.

### When to use ADR-lite vs full ADR vs commit message

| Tier | When | Artifact |
|---|---|---|
| **Full ADR** | Changes the model — new architecture, new enforcement philosophy, genuine debate with multiple viable alternatives | Full ADR (~40 lines) |
| **ADR-lite** | Changes behavior within an existing model — gate changes, default changes, boundary changes | ADR-lite (~12 lines) |
| **Commit message** | Presentation, formatting, threshold tuning, obvious fixes with no meaningful alternative | Git commit |

Concrete triggers for ADR-lite (any one):
1. Changes a human approval gate (adds, removes, or bypasses)
2. Changes a default that alters out-of-box behavior
3. Moves something from blocked to allowed (or vice versa)
4. Introduces a config knob whose existence encodes a design choice

## Alternatives Considered

- **Protocol changelog section** — rejected because protocol files are mutable (edited during iteration), violating the append-only principle that makes ADRs trustworthy.
- **Single running log file** — rejected because it becomes an unstructured dump. Individual files are linkable, greppable by protocol name, and follow the established ADR pattern.
- **Commit message convention** — rejected because commit messages are invisible to someone reading a protocol file or browsing `docs/decisions/`. They lack structure and get buried in version-bump noise.
- **Nothing new** — rejected because four genuine decisions from one dogfooding session have no record beyond commit messages. The "schema without enforcement" pattern (ADR-0028) applies to process artifacts too.

## Consequences

The `docs/decisions/` directory now contains two weights of decision records. The README index marks lite entries with `(lite)` in the status column. The `protocols:` frontmatter field enables `grep -l 'protocols:.*expand'` to find all decisions affecting a specific protocol.

ADR count will grow faster (lite entries are cheap to write) but signal quality is preserved — full ADRs remain reserved for architectural decisions. The `weight` field lets tooling filter by significance.

## References

- [ADR-0026: Spec-Driven Development Process](0026-spec-driven-development-process.md) — established the 6-layer stack
- [development-process.md](../development-process.md) — "When to Write an ADR" section (to be updated)
