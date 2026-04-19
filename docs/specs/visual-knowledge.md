---
status: draft
date: 2026-04-18
---
# Visual Knowledge

## Intent

Images from source material are captured, understood, and used to enrich wiki pages. Visual content is a first-class knowledge source — not decoration. The platform preserves images with the same snapshot philosophy applied to text sources, and extracts knowledge from them using the same cite-then-claim model.

## Invariants

- **Image capture** — When importing source material that contains images, the images are downloaded and stored in `raw/assets/` as immutable snapshots, following the same preservation principle as text sources. Imported images are referenced from wiki pages via local paths. Images that cannot be fetched during import are skipped with a warning — import never fails due to an unreachable image.

- **Image classification** — During compilation, every image from a raw source is classified into categories including subject-photo, diagram, chart, screenshot, and decorative. Decorative images are excluded from wiki pages. Import captures all images indiscriminately; compile classifies and filters. Classification uses surrounding text context and alt text; multimodal analysis enhances classification when available but is not required.

- **Image-informed compilation** — The compile protocol uses image understanding to produce richer wiki pages. Subject photos are placed contextually. Diagrams and charts inform the text content — the LLM describes what they show and references them in prose. Image placement follows page type section contracts.

- **Image-derived knowledge** — When a chart, diagram, or data visualization contains extractable knowledge (data points, relationships, component names), that knowledge is compiled into wiki text and cited with standard `[^src-N]` provenance markers pointing to the source image. Image-derived claims are distinguished in the verification ledger by a `source_media` field. Image-derived claims have inherently lower independent verifiability than text-derived claims — the adversarial verification model cannot apply full scrutiny to image sources without multimodal capability. The `extraction_confidence` field encodes this asymmetry.

- **Image provenance** — Every image in a wiki page traces to its source: the raw asset path, the original URL, and the import date. Image-derived claims follow the same provenance chain as text-derived claims. The verification ledger records `source_media` type and `extraction_confidence` for image-sourced entries.

- **Graceful degradation** — When the operating LLM lacks multimodal capabilities, image classification and understanding degrade gracefully to text-only inference using alt text, filenames, and surrounding prose context. Wiki pages are never broken by the absence of multimodal analysis — they are enriched by its presence.

## Rationale

Knowledge is not exclusively textual. For many domains — biology, architecture, cooking, hardware design — images are the knowledge. A breed photo communicates more than 500 words of description. An architecture diagram encodes component relationships that the accompanying prose may not fully enumerate. Treating images as passive decoration wastes knowledge that the source author included for a reason.

The platform already snapshots text sources because external content disappears. Images deserve the same treatment — a URL that works today may return a 404 tomorrow. Local immutable copies ensure the knowledge base remains self-contained and auditable regardless of upstream availability.

The existing cite-then-claim model extends naturally to images. A chart is a source. A diagram contains relationships. A photo shows physical attributes. The `[^src-N]` provenance markers, the verification ledger, and the tiered authority model all work without modification — images simply become another raw source type that flows through the same pipeline. The `source_media` and `extraction_confidence` fields let the verification system apply appropriate scrutiny to visual claims without requiring a parallel provenance infrastructure. This is an accepted trade-off: image-derived claims carry less verification rigor than text-derived claims, but the knowledge value of capturing visual content outweighs the verification cost.

## Design

- [Source Authority Model](../design/source-authority-model.md) — will be extended for image provenance and visual source tiers

## Decisions

ADRs will be created when design and implementation begin.

## Dependencies

- **Depends on:** [Source-Grounded Knowledge](source-grounded-knowledge.md) (accepted) — raw immutability, snapshot philosophy, provenance model.
- **Depends on:** [Per-Claim Source Provenance](source-authority-pipeline.md) (accepted) — cite-then-claim pattern, `[^src-N]` markers, verification ledger schema.
