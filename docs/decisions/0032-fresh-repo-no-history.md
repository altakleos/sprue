---
status: accepted
date: 2026-04-16
---
# ADR-0032: Fresh Repo for Sprue Platform — No History Carry-Over

## Context

The Sprue platform needed to be extracted from the `altakleos/tech-kb` monorepo into its own repository. The monorepo has 217+ commits, but ~80% are instance content operations (wiki page edits, backfill batches, raw file imports) — not platform work. The git history also contains 537 raw files, 566 wiki pages, and personal notebook content that should not appear in a public platform repo.

## Decision

Start the Sprue repo fresh with no git history. Copy the current platform files (`sprue/`, `docs/`) into a new repo with a clean first commit. The monorepo backup in the parent folder preserves the full history for archaeology. The 25 consolidated ADRs capture every meaningful platform decision, making git history redundant for understanding the platform's evolution.

## Alternatives Considered

- **Keep full history, delete instance files from HEAD** — rejected because personal KB content remains accessible in git history, and 80% of commits are irrelevant instance operations
- **`git filter-repo` to strip instance content** — rejected because it rewrites all commit hashes, adds complexity, and the filtered history is still noisy with instance-related commits
- **`git subtree split`** — rejected because it only extracts commits touching `sprue/`, losing the docs/ history and producing a partial, confusing history

## Consequences

The Sprue repo starts clean — first commit is the product as it stands today. No risk of personal content leaking. `git blame` on platform files starts from the extraction date, but the ADRs provide the decision archaeology that blame would have served. The monorepo backup is the escape hatch if deep history is ever needed.
