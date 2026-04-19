# Architecture Decision Records

ADRs capture decisions made during platform design and implementation — the WHICH and WHY layer. They are produced as decisions crystallize, not as the starting point for new work. Product intent lives in `docs/specs/`; technical architecture lives in `docs/design/`. For the full development model, see `docs/development-process.md`.

Platform decisions in chronological order. Each ADR captures the context, decision, alternatives considered, and consequences of a platform-level architectural choice.

| # | Decision | Status |
|---|---|---|
| 0001 | [Origin and Scaling Vision](0001-origin-and-scaling-vision.md) | accepted |
| 0002 | [Content Safety Invariants](0002-content-safety-invariants.md) | accepted |
| 0003 | [Three-Command Pipeline — Import/Compile/Expand](0003-three-command-pipeline.md) | accepted |
| 0004 | [Faceted Classification System](0004-faceted-classification-system.md) | accepted |
| 0005 | [Content Type System — Types, Schemas, and Size Profiles](0005-content-type-system.md) | accepted |
| 0006 | [Configuration Layering — Platform Defaults + Instance Overrides](0006-configuration-layering.md) | accepted |
| 0007 | [Platform/Instance Architecture — Reusable Engine](0007-platform-instance-architecture.md) | accepted |
| 0008 | [Emergent Directory Structure](0008-emergent-directory-structure.md) | accepted |
| 0009 | [Verification Pipeline — Shift-Left to Adversarial](0009-verification-pipeline.md) | accepted |
| 0010 | [Slug-Based Addressing](0010-slug-based-addressing.md) | accepted |
| 0011 | [Entity Ontology — Types, Relationships, and Resolution](0011-entity-ontology.md) | accepted |
| 0012 | [Agent Memory — Rules, Corrections, and Learning](0012-agent-memory.md) | accepted |
| 0013 | [Tooling and CI Pipeline](0013-tooling-and-ci-pipeline.md) | accepted |
| 0014 | [Emergent Data Structures — Synonyms, Signals, Guards](0014-emergent-data-structures.md) | accepted |
| 0015 | [Content Quality Model — Confidence, Decay, and Self-Healing](0015-content-quality-model.md) | accepted |
| 0016 | [Navigation Architecture — Hub and Sub-Indexes](0016-navigation-architecture.md) | accepted |
| 0017 | [Operational Logging — JSONL and Summary Fields](0017-operational-logging.md) | accepted |
| 0018 | [Three Automation Modes — Manual/Semi/Auto](0018-three-automation-modes.md) | accepted |
| 0019 | [LLM Retrieval Optimization](0019-llm-retrieval-optimization.md) | accepted |
| 0020 | [Mermaid Diagram Standard](0020-mermaid-diagram-standard.md) | accepted |
| 0021 | [Configurable Enhance Agents](0021-configurable-enhance-agents.md) | accepted |
| 0022 | [Agent Bootstrap — AGENTS.md Import Chain](0022-agent-bootstrap.md) | accepted |
| 0023 | [Reset Command — Soft/Standard/Hard Levels](0023-reset-command.md) | accepted |
| 0024 | [Inbox Drop Zone](0024-inbox-drop-zone.md) | accepted |
| 0025 | [Schema Versioning and Status Reporting](0025-schema-versioning.md) | accepted |
| 0026 | [Spec-Driven Development Process](0026-spec-driven-development-process.md) | superseded by 0043 |
| 0027 | [Sources Field in Frontmatter](0027-sources-field-in-frontmatter.md) | accepted |
| 0028 | [Provenance Enforcement Model](0028-provenance-enforcement-model.md) | accepted |
| 0029 | [Plans Layer — Task Breakdowns as Permanent Records](0029-plans-layer.md) | accepted |
| 0030 | [Rename platform/ to sprue/, Split Contributor Docs to docs/](0030-rename-platform-to-sprue-split-docs.md) | accepted |
| 0031 | [Product Name — Sprue](0031-product-name-sprue.md) | accepted |
| 0032 | [Fresh Repo for Sprue Platform — No History Carry-Over](0032-fresh-repo-no-history.md) | accepted |
| 0033 | [Sprue Distribution Model — pip + Local Engine Copy](0033-sprue-distribution-model.md) | accepted |
| 0034 | [Tool-Specific Agent Hook Files](0034-tool-specific-agent-hooks.md) | accepted |
| 0035 | [ADR-Lite Format for Protocol Behavioral Changes](0035-adr-lite-format.md) | accepted |
| 0036 | [Compile Executes Approved Batch Without Per-Page Pauses](0036-compile-batch-execution.md) | accepted (lite) |
| 0037 | [Scoped Expand Skips the Topic Approval Gate](0037-scoped-expand-skips-topic-gate.md) | accepted (lite) |
| 0038 | [Expand Defaults to Semi Mode](0038-expand-default-semi-mode.md) | accepted (lite) |
| 0039 | [Soften Facet Gate to Scoring Penalty with Deepen/Broaden Split](0039-soften-facet-gate-deepen-broaden.md) | accepted (lite) |
| 0040 | [Cite-Then-Claim Generation at Compile Time](0040-cite-then-claim-generation.md) | accepted |
| 0041 | [Extend verification ledger with per-claim source fields](0041-extend-verification-ledger-per-claim-source-fields.md) | accepted (lite) |
| 0042 | [Dead sources boost verification priority, not downgrade confidence](0042-dead-sources-boost-verification-priority.md) | accepted (lite) |
| 0043 | [Generic SDD Layer Names — Decouple Method from Sprue Artifacts](0043-generic-sdd-layers.md) | accepted |
| 0044 | [Image Capture Pipeline — Download at Import, Rewrite URLs in Raw](0044-image-capture-pipeline.md) | accepted |
| 0045 | [Image annotations in a single state ledger, not per-image sidecars](0045-image-annotations-single-state-ledger.md) | accepted (lite) |
| 0046 | [Multimodal capability declared by config flag, not runtime probing](0046-multimodal-config-flag.md) | accepted (lite) |
