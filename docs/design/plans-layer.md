---
status: accepted
date: 2026-04-16
---
# Plans Layer

Task breakdowns that bridge the gap between design (HOW a mechanism works) and implementation (code changes). Plans are the pre-implementation artifact that implementing agents read before writing code.

## Context

The pre-plans stack (Specs → Design → ADRs → Implementation → Verification) captured WHAT the platform does, HOW mechanisms work, and WHY decisions were made — but had no artifact for WHAT TO DO NEXT. During implementation, agents either worked from memory (lost between sessions) or reverse-engineered tasks from design docs (duplicated effort per agent).

The SDD pipeline requires a concrete artifact between Design and Implement: something an agent reads cold and knows exactly which files to touch, in what order, with what acceptance criteria.

## Architecture

Plans sit between ADRs and Implementation in the stack — they consume design decisions and produce implementation guidance.

```
Specs → Design → ADRs → [Plans] → Implementation → Verification
                              ↑                         ↓
                        reads design              guides implementation
```

### Lifecycle

```
planned → in-progress → done
```

- **planned**: Tasks defined, not yet started. First commit on the feature branch.
- **in-progress**: Agent is executing tasks. Checkboxes track progress.
- **done**: All tasks complete, verification passed. Plan stays as permanent record.

### Artifact Structure

Each plan is a single markdown file at `docs/plans/<feature-slug>.md` with:

- **YAML frontmatter**: `feature`, `serves` (which spec), `design` (which design doc), `status`, `date`
- **Tasks**: Ordered checklist with file paths and dependency annotations
- **Acceptance Criteria**: Conditions that must hold when the feature is complete

### Inputs and Outputs

| Direction | What | Example |
|-----------|------|---------|
| Reads | Product spec | `docs/specs/platform-reusability.md` |
| Reads | Design doc | `docs/design/instance-scaffolding.md` |
| Reads | Existing protocols/config | To understand current state |
| Produces | Ordered task list | T1 → T2 → T3 with file paths |
| Consumed by | Implementing agent | Reads plan before writing code |
| Referenced by | ADRs | Decisions made during implementation link back to plan |

### Scope Routing

Not every change needs a plan. The routing criteria from `development-process.md`:

| Change type | Plan needed? |
|-------------|-------------|
| Bug fix / config tune | No |
| Single-file protocol tweak | No |
| Multi-file feature | Yes |
| New capability | Yes |

The threshold: if the implementation involves multiple files or steps that must be ordered, write a plan.

## Interfaces

- **With Design**: Plans reference the design doc via `design:` frontmatter. The design describes the mechanism; the plan breaks it into executable steps.
- **With ADRs**: Decisions made during implementation reference the plan. The plan provides context for why the decision arose.
- **With Git**: Plans are committed as the first commit on a feature branch. The branch name matches the plan's `feature` slug.
- **With Agents**: An agent starting implementation reads the plan file. Progress is tracked via task checkboxes. Multiple agents can work different tasks from the same plan.

## Trade-offs

- **Plans are permanent, not ephemeral.** This costs disk space and adds files to the repo, but provides historical records of how features were built — valuable for understanding implementation decisions that don't rise to ADR level.
- **Plans are flat files, not directories.** A per-feature directory (`.sdd/<feature>/`) was rejected (ADR-0029) because it created a parallel hierarchy duplicating the layer stack. A single file per feature in `docs/plans/` is sufficient.
- **Plans have no automated enforcement.** There is no CI check that a plan exists before implementation. This is intentional — the scope routing table allows small changes to skip plans. Enforcement would add friction to bug fixes.

## Specs

Plans serve all product specs indirectly — they organize implementation work for any feature.

## Decisions

- [ADR-0029: Plans Layer](../decisions/0029-plans-layer.md) — why plans are permanent records in the stack
