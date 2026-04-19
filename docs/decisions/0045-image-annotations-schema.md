---
status: accepted
date: 2026-04-19
weight: lite
protocols: [compile]
---
# ADR-0045: Image annotations in a single state ledger, not per-image sidecars

**Decision:** Compile Step 4a writes image analysis results to a single `instance/state/image-annotations.yaml` ledger, keyed by content_hash. Each entry contains the full annotation (classification, description, extracted_claims). No per-image sidecar files (e.g., `raw/assets/foo.png.annotations.yaml`).

**Why:** Matches the platform's existing state model — all state lives in `instance/state/` as append-only YAML ledgers (verifications.yaml, imports.yaml, compilations.yaml). Sidecar files fragment state across directories, complicate cleanup, and violate the 'raw/ is immutable, state/ is append-only' separation. Content_hash keying provides stable lookup across re-compilations.

**Alternative:** Per-image sidecar YAML files next to each image in raw/assets/ (rejected: mixes state with raw content, fragments ledger scans, violates immutability boundary since sidecars would live alongside immutable raw assets).
