This is the Sprue platform repository. You are a contributor developing the engine.

On EVERY session start, before responding to any user message:
1. Read `AGENTS.md` — contributor boot document.
2. Read `docs/development-process.md` — the 6-layer stack and ADR-lite format.

Key rules:
- Follow the 6-layer stack: Specs → Design → ADRs → Plans → Protocols → Config/Validators.
- Protocol behavioral changes need an ADR-lite (ADR-0035). Architectural changes need a full ADR.
- Every change ends with `sprue verify` or `pytest`.
- Commit atomically. Push to feature branches. PR to main.
