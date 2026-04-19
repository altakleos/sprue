---
status: accepted
date: 2026-04-19
---
# ADR-0044: Image Capture Pipeline — Download at Import, Rewrite URLs in Raw

## Context

The Visual Knowledge spec requires images to be captured as immutable snapshots in `raw/assets/`, applying the same philosophy as text sources. Jina Reader returns web articles with images as `![alt](url)` referencing remote servers — the image bytes are not included in the markdown body. These remote URLs may go down, move, or change content after import. To deliver on the snapshot philosophy, images must be downloaded locally AND the raw markdown must reference local paths.

The source-grounded-knowledge invariant states: "Raw source files are immutable after capture — the original human-produced content is preserved unchanged." Rewriting image URLs in the raw file appears to violate this invariant. This ADR resolves that tension.

## Decision

Images are downloaded during import and stored in `raw/assets/` using the naming convention `<source-slug>-<sequence>-<hash8>.<ext>`. Image URLs in the raw markdown are rewritten from remote URLs to relative `raw/assets/` paths. The original URL is preserved in an HTML comment next to each rewritten reference.

This rewriting is defined as part of the capture operation itself — the "captured" raw file includes URL rewriting. Immutability applies AFTER capture completes. The final raw file (post-rewrite) is the immutable artifact, not the intermediate fetch output.

Rationale: the raw file's purpose is to be a self-contained, auditable snapshot. A raw file with dead external URLs fails that purpose. Local paths with preserved original URLs satisfy both immutability (post-capture, the file never changes) and snapshot philosophy (the file is self-contained).

Image downloads that fail are skipped with warnings. Import never fails due to an unreachable image. The raw file keeps the remote URL for failed downloads, marked with a comment. Filtering heuristics (min SVG bytes, tracking domain blocklist, dimension hints) filter out tracking pixels, tiny icons, and non-image URLs before download. The `imports.yaml` state gains an additive `assets` field recording `local_path`, `original_url`, `alt_text`, `size_bytes`, and `content_hash` per image.

## Alternatives Considered

- **Keep original URLs, store images as sidecar without rewriting** — rejected because raw files would have dead URLs when upstream disappears, defeating the snapshot philosophy. Consumers would see broken images.
- **Store images only in imports.yaml metadata, leave raw markdown untouched** — rejected because compile would need to cross-reference `imports.yaml` to find images. Breaks the "raw file is the source" model.
- **Use an image proxy/CDN** — rejected because it adds infrastructure and doesn't solve immutability (proxy can go down too).
- **Do not download images, just preserve URLs** — rejected explicitly by the spec: "downloaded and stored as immutable snapshots."

## Consequences

The raw file IS modified once during capture (URL rewriting). After capture completes, it is immutable per the existing invariant. This is a refinement of "immutable after capture," not a violation. Storage grows with image-heavy sources; config limits (`max_bytes` per image, `max_per_source`) cap the blast radius.

Raw files are now self-contained — they can be browsed locally without internet access. A failed image download leaves the remote URL in the raw markdown. If the remote source later disappears, that image is permanently lost. This is accepted; immutability forbids going back to re-download. The original URL preserved in HTML comments enables future re-fetch workflows (operator-initiated, creating a new raw file) without losing provenance.

## Specs

- [Visual Knowledge](../specs/visual-knowledge.md) — image capture invariant
- [Source-Grounded Knowledge](../specs/source-grounded-knowledge.md) — raw immutability

## Design

- [Visual Knowledge Model](../design/visual-knowledge-model.md) — Image Capture & Storage section
