This is the Sprue platform repository. You are a contributor developing the engine.

On EVERY session start, before responding to any user message:
1. Read `AGENTS.md` — contributor boot document.
2. Read `docs/development-process.md` — the SDD layer stack and ADR-lite format.
3. Read `docs/sprue-implementation.md` — how Sprue instantiates Implementation and Verification.

Key rules:
- Follow the layer stack: Specs → Design → ADRs → Plans → Implementation → Verification.
- Implementation behavioral changes need an ADR-lite (ADR-0035). Architectural changes need a full ADR.
- Every change ends with `sprue verify` or `pytest`.
- Commit atomically. Push to feature branches. PR to main.

Layer gate (MANDATORY before writing code):
- Before modifying any file in `src/`, check: does a plan exist in `docs/plans/` for this work?
- If the task touches 3+ files or spans multiple layers → a plan is REQUIRED.
- If no plan exists → create one first, following the template in `docs/plans/README.md`.
- If a plan exists → read it, confirm which phase/task you are executing, and update it when done.

Publish workflow (when user says "publish"):
- See AGENTS.md "Publish Workflow" section. Execute all 10 steps end-to-end without prompting.
