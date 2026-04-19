---
status: accepted
date: 2026-04-19
weight: lite
protocols: [compile]
---
# ADR-0046: Multimodal capability declared by config flag, not runtime probing

**Decision:** The instance operator declares whether the operating LLM can accept image inputs via `config.images.multimodal_available` (default: false). No runtime probing, no capability negotiation, no auto-detection.

**Why:** The operator knows their model's capabilities — they configured it. Runtime probing would require sending test images to measure response behavior, adding latency and cost to every compile. Explicit configuration is simpler, auditable, and consistent with how other capability flags work in the platform.

**Alternative:** Auto-detect by sending a probe image and inspecting the response (rejected: adds latency on every session start, wastes tokens, false negatives when the probe itself fails for unrelated reasons).
