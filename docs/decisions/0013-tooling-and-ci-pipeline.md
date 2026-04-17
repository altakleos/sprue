---
status: accepted
date: 2025-05-25
---
# ADR-0013: Tooling and CI Pipeline

## Context
Platform scripts started as bash one-liners that grew into unmaintainable shell scripts with implicit dependencies. The verify runner shelled out to undeclared Python packages, and there was no CI — broken scripts or invalid config could be pushed without detection. Contributors had no way to know if their changes passed basic quality checks before merging.

## Decision
Migrate the verify runner and all platform scripts from bash to Python with explicitly declared dependencies. Establish a GitHub Actions CI pipeline that runs lint (lint-rules.py) and verify (verify.py) on every push and pull request. This creates a continuous quality baseline — no change merges without passing structural and content checks.

## Alternatives Considered
- **Keep bash scripts with shellcheck linting** — rejected because the scripts needed structured data handling (YAML parsing, frontmatter validation) that bash handles poorly
- **Pre-commit hooks only, no CI** — rejected because hooks are local and optional; CI enforces checks regardless of contributor setup

## Consequences
Every push is validated automatically, catching config inconsistencies and lint violations before they reach mainline. Python scripts are easier to test and extend than bash. The trade-off is a Python 3.10+ runtime dependency and the need to maintain CI workflow configuration alongside the platform.
