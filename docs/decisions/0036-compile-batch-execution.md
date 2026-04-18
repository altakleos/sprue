---
status: accepted
date: 2026-04-17
weight: lite
protocols: [compile]
---
# ADR-0036: Compile executes approved batch without per-page pauses

**Decision:** After Step 3 classification is approved, compile streams through all pages without pausing. The protocol explicitly forbids "Page N done, say go for page N+1."

**Why:** Dogfooding showed the LLM paused after every page despite no protocol mandate. The per-page gate was approval theater — zero user rejections across dozens of invocations.

**Alternative:** Keep per-page approval for first-time users (rejected: the classification plan in Step 3 is the designed approval point; per-page adds friction without safety value).
