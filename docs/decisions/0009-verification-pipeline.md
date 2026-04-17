---
status: accepted
date: 2025-05-01
---
# ADR-0009: Verification Pipeline — Shift-Left to Adversarial

## Context
Early verification was a post-write afterthought — the agent would compile a page and optionally check it. There was no centralized pipeline, no confidence tracking, and no adversarial review. LLM-generated content could enter the wiki at high confidence without independent verification. Config-driven frontmatter checks existed but weren't wired into a coherent system. Raw source files had no integrity validation.

## Decision
Build a centralized verification pipeline with multiple layers. Compile always writes pages at medium confidence. Verify promotes confidence through an adversarial writer/critic/judge model — three independent LLM passes that challenge claims. Static config cross-consistency checks catch schema violations. Raw file invariants (validate-raw.py) ensure source material integrity. The confidence invariant (compile writes medium, verify promotes) is enforced as a hard rule.

## Alternatives Considered
- **Single-pass LLM verification** — rejected because the same model that wrote the content has the same blind spots when checking it
- **Human-only verification** — rejected because it doesn't scale; the adversarial model catches most factual issues automatically

## Consequences
Content quality improved significantly — the adversarial model catches hallucinations and unsupported claims that single-pass review misses. The cost is that verification is expensive (three LLM calls per page) and slow, making it impractical to verify every page on every compile cycle.

## Specs

- [Continuous Quality](../specs/continuous-quality.md)
- [Source-Grounded Knowledge](../specs/source-grounded-knowledge.md)

## Design

- [Source Authority Model](../design/source-authority-model.md)
- [Confidence State Machine](../design/confidence-state-machine.md)
