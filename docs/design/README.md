# Design Documents

Technical architecture for the platform. Each design doc describes a high-level HOW — mechanisms, data flows, state machines — without being step-by-step procedures (that is what protocols are for).

For the full development model, see `docs/development-process.md`.

| # | Design | Description | Status |
|---|--------|-------------|--------|
| 1 | [Prose-as-Code Execution Model](prose-as-code.md) | Markdown protocols as executable code interpreted by an LLM runtime | accepted |
| 2 | [Three-Command Pipeline](three-command-pipeline.md) | Import, Compile, Expand — each command owns exactly one boundary | accepted |
| 3 | [Append-Only State Model](append-only-state.md) | Append-only YAML ledgers for auditable, crash-safe state tracking | accepted |
| 4 | [Source Authority Model](source-authority-model.md) | Tiered source authority, per-claim verification ledger, provenance query interface, and cite-then-claim generation | accepted |
| 5 | [Confidence State Machine](confidence-state-machine.md) | Confidence states, decay model, verification prioritization, and source health monitoring | accepted |
| 6 | [Agent Memory and Learning](agent-memory.md) | Structured rules and tracked corrections for cross-session learning | accepted |
| 7 | [Plans Layer](plans-layer.md) | Task breakdowns bridging design to implementation | accepted |
| 8 | [Sprue Distribution Model](sprue-distribution.md) | Pip-installable package with CLI scaffolding and local engine copy | accepted |
| 9 | [Visual Knowledge Model](visual-knowledge-model.md) | Image capture, compile-time understanding, provenance, and graceful degradation for visual content | accepted |
