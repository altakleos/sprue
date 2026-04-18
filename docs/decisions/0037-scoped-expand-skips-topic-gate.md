---
status: accepted
date: 2026-04-17
weight: lite
protocols: [expand]
---
# ADR-0037: Scoped expand skips the topic approval gate

**Decision:** When the user provides a scope (e.g., `expand into breed profiles`), the topic gate is bypassed — the user's scope IS the topic selection. Execution proceeds directly to source research.

**Why:** Asking "approve which?" after the user already specified the scope is redundant. The user expressed intent; re-presenting a table for confirmation is approval theater.

**Alternative:** Always present the topic table regardless of scope (rejected: forces the user to re-confirm what they just said).
