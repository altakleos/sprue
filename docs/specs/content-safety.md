---
status: accepted
date: 2026-04-16
---
# Content Safety

## Intent

The platform prevents the loss, corruption, or unauthorized modification of knowledge. The agent operates within strict behavioral boundaries that protect content integrity regardless of automation level. These boundaries are non-negotiable — they cannot be overridden by configuration, relaxed by the agent, or bypassed by composite commands.

## Invariants

- Never delete pages without explicit human approval. Niche topics are valid; the KB accumulates knowledge.
- Bias toward page creation when the operator's intent is clear. Use explicit criteria to decide standalone page vs. section merge — not agent judgment about whether the topic "deserves" a page.
- No side-effect page creation — pages are created only through explicit pipeline commands, never as byproducts of queries, maintenance, or other operations.
- Never silently overwrite content that seems wrong. Flag contradictions visibly and reduce confidence rather than making quiet corrections.
- Never edit many pages without approval. Propose a batch plan first; let the operator decide the scope.
- Source files are verbatim captures. Classification metadata is stored separately, never injected into the original content.
- Destructive operations (reset, bulk edits) require explicit confirmation and offer graduated levels of destruction.

## Rationale

Early operations revealed three failure modes: the agent deleted pages it deemed low-quality (losing human-curated content), created pages as side effects of other commands (polluting the wiki), and silently overwrote content it disagreed with (corrupting the knowledge base without audit trail). Soft guidelines failed — the agent optimized around them, treating them as suggestions rather than constraints. Non-negotiable invariants, enforced structurally, are the only reliable defense.

The bias toward creation over suppression reflects a core product value: it is cheaper to have a page that needs improvement than to not have a page at all. Knowledge loss is permanent; quality improvement is iterative.

## Decisions

- [ADR-0002: Content Safety Invariants](../decisions/0002-content-safety-invariants.md) — the three founding invariants (no deletion, bias toward creation, no side effects)
- [ADR-0023: Reset Command](../decisions/0023-reset-command.md) — graduated destruction with explicit confirmation

## Design

- [Append-Only State Model](../design/append-only-state.md) — crash-safe state prevents data loss
- [Agent Memory and Learning](../design/agent-memory.md) — correction loop preserves content integrity
