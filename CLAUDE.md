See @AGENTS.md for all project conventions and operating instructions.

Key reminders:
- Follow the 6-layer stack: Specs → Design → ADRs → Plans → Protocols → Config/Validators.
- Layer gate: check `docs/plans/` before modifying `src/`. Plan required for 3+ files or multi-layer changes.
- Publish workflow: see AGENTS.md "Publish Workflow" section. Execute all 10 steps end-to-end.
- Every change ends with `sprue verify` or `pytest`.
