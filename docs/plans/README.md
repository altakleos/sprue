# Plans

Task breakdowns for platform features. Written AFTER design, BEFORE implementation. Implementing agents read the plan before writing code.

Plans are permanent records — they stay after the feature ships as historical documentation of how features were built.

See `docs/development-process.md` for when to write a plan and how plans fit in the development stack. For how an implementing agent should execute a plan (streaming mechanical tasks, stopping at decisions and destructive ops, avoiding approval theater), see [development-process.md § How Plans Are Executed](../development-process.md#how-plans-are-executed).

## Template

```markdown
---
feature: <feature-slug>
serves: docs/specs/<spec>.md          # which product spec this serves
design: docs/design/<mechanism>.md    # which design doc (if any)
status: planned | in-progress | done
date: YYYY-MM-DD
---
# Plan: <Feature Name>

## Tasks

- [ ] T1: <description> → `path/to/file`
- [ ] T2: <description> → `path/to/file` (depends: T1)
- [ ] T3: <description> → `path/to/file`

## Acceptance Criteria

- [ ] AC1: <what must be true when done>
- [ ] AC2: <what must be true when done>
- [ ] verify.sh passes
```
