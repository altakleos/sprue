---
status: accepted
date: 2026-04-17
weight: lite
protocols: [expand]
---
# ADR-0038: Expand defaults to semi mode

**Decision:** Bare `expand` (no flag) uses semi mode — user picks topics, LLM auto-selects sources. Configurable via `config.expand.default_mode`.

**Why:** Manual mode (user approves both topics AND sources) was friction without safety benefit. The source gate adds a second approval round on information the user can't meaningfully evaluate (URL quality, word count).

**Alternative:** Keep manual as default (rejected: too cautious for the target audience; `--manual` flag remains available for users who want full control).
