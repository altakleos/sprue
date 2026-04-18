---
status: accepted
date: 2026-04-18
weight: lite
protocols: [verify]
---
# ADR-0041: Extend verification ledger with per-claim source fields

**Decision:** Each claim entry in verifications.yaml gains five additive fields: `id` (stable claim identifier), `source_ref` (raw file path), `source_url` (authoritative URL), `source_excerpt` (supporting text), and `excerpt_hash` (SHA-256 of excerpt). Three derived frontmatter fields are added to pages: `source_quality`, `claims_verified`, `claims_unverifiable`. All fields are optional — existing ledger entries parse unchanged.

**Why:** The Per-Claim Source Provenance spec requires each claim to link to its source excerpt. The current ledger records claim text and verdicts but not the source chain. Adding fields to the existing schema (rather than a sidecar file) keeps the append-only model intact and avoids a second state file.

**Alternative:** Sidecar `claims-index.yaml` per page (rejected: fragments state across files, complicates query-provenance.py, violates the single-ledger-per-page pattern).
