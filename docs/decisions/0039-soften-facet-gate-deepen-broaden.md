---
status: accepted
date: 2026-04-17
weight: lite
protocols: [expand]
---
# ADR-0039: Soften facet gate to scoring penalty with Deepen/Broaden split

**Decision:** `min_shared_facets` changed from hard rejection to a scoring penalty (`config.expand.facet_miss_penalty`, default 0.15). Candidates below the threshold appear in a **Broaden** section of the results table instead of being silently dropped.

**Why:** The hard gate hid legitimate broadening candidates. A KB with identity "Anything about cats" and behaviour-heavy content silently rejected nutrition/health topics that were squarely in scope. Users couldn't broaden their KB because they never saw the candidates.

**Alternative:** Keep hard gate with a lower threshold (rejected: still binary — candidates are either visible or invisible, with no user choice between depth and breadth).
