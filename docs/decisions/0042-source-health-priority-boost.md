---
status: accepted
date: 2026-04-18
weight: lite
protocols: [maintain]
---
# ADR-0042: Dead sources boost verification priority, not downgrade confidence

**Decision:** When source health monitoring detects a dead or drifted source, affected pages receive a priority boost for re-verification. Confidence is NOT automatically downgraded — a dead source means "needs re-checking", not "content is wrong".

**Why:** A source URL dying doesn't invalidate the facts extracted from it. The content was correct when verified. Automatic downgrade would create false quality signals and trigger unnecessary remediation cascades across pages sharing a common source.

**Alternative:** Automatic confidence downgrade on source death (rejected: a CDN migration or domain change would cascade confidence drops across dozens of pages, none of which have actual content errors).
