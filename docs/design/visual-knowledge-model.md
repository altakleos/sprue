---
status: draft
date: 2026-04-18
---
# Visual Knowledge Model

Images from source material are first-class knowledge — captured as immutable snapshots, understood at compile time, and cited with the same provenance model as text. The platform treats visual content as a source to extract claims from, not decoration to display.

## Context

Knowledge is not exclusively textual. An architecture diagram encodes component relationships that prose may not enumerate. A breed photo communicates physical attributes more precisely than description. A benchmark chart contains data points that the accompanying text may summarize but not fully reproduce. Treating images as passive decoration wastes knowledge the source author included for a reason.

The visual knowledge pipeline has three stages: **capture** (import downloads images to `raw/assets/` as immutable snapshots), **understand** (compile classifies images by role and extracts knowledge via alt text, context, and optionally multimodal analysis), and **cite** (image-derived claims flow through the existing cite-then-claim model with `source_media` and `extraction_confidence` fields in the verification ledger).

This design extends existing infrastructure rather than building a parallel pipeline. Images are raw source files — they use the same `raw/` immutability guarantee, the same `[^src-N]` provenance markers, and the same verification ledger. The `source_media` and `extraction_confidence` fields let the verification system apply appropriate scrutiny to visual claims without requiring new protocols. The three-command pipeline (import → compile → verify) is unchanged; images flow through it as a new source type.

## Architecture

*The capture pipeline, compile-time understanding, and provenance model are documented in their respective architecture subsections (below). This section covers the cross-cutting concerns: degradation behavior, configuration, and integration points.*
### Image Capture & Storage

During import, images embedded in source material are downloaded to `raw/assets/` as immutable snapshots. Import treats images like text — capture faithfully, record metadata, stop. Classification and interpretation are compile's job.

#### Image Extraction from Raw Markdown

Jina Reader returns images as `![Image N: alt](url)` in fetched markdown. The import protocol scans raw content for the standard markdown image pattern `![alt](url)` and applies filtering heuristics before fetching:

| Filter | Rule | Rationale |
|--------|------|-----------|
| SVG size | Skip SVGs under `config.images.capture.min_svg_bytes` | Tiny SVGs are icons or spacers |
| Dimension hints | Skip URLs containing `1x1`, `2x1`, `1x2` | Tracking pixels |
| Tracking domains | Skip URLs matching `config.images.capture.tracking_domains` | Analytics beacons (`pixel.`, `beacon.`, `analytics.`) |
| Data URIs | Skip `data:image/` under `config.images.capture.min_data_uri_bytes` | Inline icons |
| Extension filter | Only fetch `config.images.capture.allowed_extensions` | Reject non-image URLs |

Import captures **all images that pass filtering** without classifying relevance. Compile assigns roles (subject-photo, diagram, decorative) and decides what reaches wiki pages.

#### Download Pipeline

1. **HTTP fetch** — GET with `config.images.capture.timeout_seconds` timeout. Follow up to `config.images.capture.max_redirects` redirects.
2. **Content-type validation** — `Content-Type` must start with `image/`. Reject HTML error pages.
3. **Size limit** — reject responses exceeding `config.images.capture.max_bytes`.
4. **Retry** — one retry on transient failures (429, 5xx, timeout). No retry on 4xx.
5. **Write** — save to `raw/assets/` per naming convention below.

**Failure handling:** skip with warning — import never fails due to an unreachable image.

```
📥 "Kafka Deep Dive" (article, 3200w) → raw/articles/kafka-deep-dive-2026-05-01-a1b2c3d4.md
   ⚠️ 2/8 images skipped (1 timeout, 1 too large)
```

#### Storage Naming

```
raw/assets/<source-slug>-<sequence>-<hash8>.<ext>
```

- `source-slug` — kebab-case from parent article title, max 30 chars
- `sequence` — 1-indexed position in the source document
- `hash8` — first 8 chars of SHA-256 of image content
- `ext` — original extension from URL or Content-Type

```
raw/assets/kafka-architecture-guide-1-7f2a3b4c.png
raw/assets/kafka-architecture-guide-2-e8d1c5f9.svg
raw/assets/kafka-architecture-guide-3-1a2b3c4d.jpg
```

**Why this format?** Source slug → traceability. Sequence → document order. Hash → deduplication (identical images across sources share a hash; skip re-download). Predictable paths → compile locates assets without scanning.

#### URL Rewriting in Raw

After downloading, remote URLs in the raw markdown are replaced with relative paths to `raw/assets/`. This is the **one exception** to raw immutability — image URLs are rewritten so the file is self-contained.

```markdown
# Before (as fetched from Jina)
![Image 3: Kafka partition layout](https://example.com/images/kafka-partitions.png)

# After (URL rewritten, original preserved in comment)
![Image 3: Kafka partition layout](raw/assets/kafka-architecture-guide-3-1a2b3c4d.png)
<!-- original: https://example.com/images/kafka-partitions.png -->
```

- Alt text preserved exactly as fetched.
- Original URL kept in an HTML comment for provenance tracing and re-fetch.
- Failed downloads left as remote URLs (no rewrite).

#### imports.yaml Schema Extension

Each import entry gains an optional `assets` list:

```yaml
- source: "https://example.com/kafka-architecture"
  raw: raw/articles/kafka-architecture-guide-2026-05-01-a1b2c3d4.md
  title: "Kafka Architecture Guide"
  content_type: article
  content_hash: sha256:a1b2c3d4
  imported_at: "2026-05-01T14:00:00Z"
  assets:
    - local_path: raw/assets/kafka-architecture-guide-1-7f2a3b4c.png
      original_url: "https://example.com/images/kafka-overview.png"
      alt_text: "Kafka cluster overview showing brokers, topics, and partitions"
      size_bytes: 245760
      content_hash: sha256:7f2a3b4c
    - local_path: raw/assets/kafka-architecture-guide-2-e8d1c5f9.svg
      original_url: "https://example.com/images/replication-flow.svg"
      alt_text: "Replication flow between leader and follower brokers"
      size_bytes: 18432
      content_hash: sha256:e8d1c5f9
```

| Field | Type | Purpose |
|-------|------|---------|
| `local_path` | string | Path to downloaded image in `raw/assets/` |
| `original_url` | string | Source URL the image was fetched from |
| `alt_text` | string | Alt text from the markdown reference |
| `size_bytes` | integer | File size in bytes |
| `content_hash` | string | SHA-256 of image content (first 8 chars match filename hash) |

The `assets` field is optional — existing entries without it are valid. This follows the additive schema pattern used by the verification ledger.

#### What sprue init Creates

`sprue init` must scaffold `raw/assets/` alongside the other `raw/` subdirectories. Currently `init.py` only creates the top-level `raw/` directory. Add `raw/assets/` to `_INSTANCE_DIRS` so it exists before the first import.

#### Size and Format Limits

All thresholds live under `config.images.capture`:

```yaml
images:
  capture:
    enabled: true                          # master switch for image downloading
    allowed_extensions: [png, jpg, jpeg, gif, svg, webp]
    max_bytes: 10485760                    # 10 MB per image
    min_svg_bytes: 512                     # skip tiny SVG icons
    min_data_uri_bytes: 1024               # skip inline data URI icons
    timeout_seconds: 15                    # HTTP fetch timeout
    max_redirects: 3                       # redirect chain limit
    tracking_domains:                      # URL substrings indicating tracking pixels
      - "pixel."
      - "beacon."
      - "analytics."
      - "track."
      - "1x1"
```

Setting `config.images.capture.enabled: false` disables image downloading entirely — import captures text only, leaving remote URLs in place.

### Compile-Time Image Understanding

During compilation, every image from a raw source is classified, described, and — when it carries knowledge — mined for claims that flow into the wiki page through the same cite-then-claim pattern used for text. The compile protocol gains a new sub-step (4a) that produces structured annotations before page generation begins. These annotations become citable source excerpts, making images first-class inputs to the provenance chain.

#### Image Triage Step

Step 4a inserts between "read raw file" and "write wiki page" in the compile protocol. For each raw source in the compile queue, the LLM scans for image references and triages each one: classify, describe, and optionally extract claims. Results persist to `instance/state/image-annotations.yaml` keyed by `content_hash`, so re-compilation reuses existing annotations. If the image changes (new hash), a fresh annotation is produced.

When `config.images.enabled` is `false`, Step 4a is skipped entirely — zero behavioral change for existing instances.

#### Classification Taxonomy

Every image receives exactly one classification:

| Classification | Signal Pattern | Knowledge Value |
|----------------|---------------|-----------------|
| `subject-photo` | Names the page entity; first image; photo format | Visual attributes for description |
| `diagram` | Alt contains "architecture", "flow", "sequence"; near technical prose | Components, relationships, flows |
| `chart` | Alt contains "chart", "graph", "benchmark"; near numeric claims | Data points, trends, labels |
| `screenshot` | UI chrome visible; near step-by-step prose | Visible text, UI elements, config values |
| `illustration` | Explanatory drawing; supports a concept | Conceptual reinforcement (limited extraction) |
| `infographic` | Mixed text and visual; statistics, timelines | Statistics, comparisons, timelines |
| `decorative` | Empty alt, generic filename, no contextual description | None — excluded from wiki pages |
| `unknown` | Ambiguous signals | Treated as illustration; flagged for review |

Classification uses a **context-first** strategy: the LLM reads alt text, filename, surrounding prose, and document position before assigning a category. When `config.images.multimodal_fallback` is enabled and context signals are insufficient, the LLM escalates to multimodal analysis. Both paths produce the same output. See the Graceful Degradation section for the full fallback chain.

#### Two-Track Understanding

**Multimodal track** — The LLM sees the image directly. Chart labels, diagram components, and photo attributes are extracted from pixels. Claims receive `extraction_confidence: high` for text-in-image content, `medium` for interpreted visual features.

**Text-only track** — The LLM infers from three signals: (1) alt text from the source, (2) filename semantics, (3) surrounding prose context. Claims receive `extraction_confidence: medium` at best, `low` for inferred visual attributes.

Both tracks produce identical output: classification, description, and zero or more `extracted_claims`. The track is recorded in the annotation (`analysis_mode: multimodal | text-only`) so downstream verification applies appropriate scrutiny.

#### Image Annotations Schema

Annotations follow the append-only state model in `instance/state/image-annotations.yaml`:

```yaml
- raw_path: raw/assets/kafka-architecture-2026-05-01-a1b2c3d4.png
  content_hash: sha256:a1b2c3d4
  analyzed_at: '2026-05-02T09:00:00Z'
  analysis_mode: text-only
  classification: diagram
  description: >
    Architecture diagram showing Kafka cluster with 3 brokers.
    ZooKeeper ensemble connected for controller election.
  extracted_claims:
    - text: "Kafka clusters use ZooKeeper for controller election"
      confidence: high
      evidence: "Diagram label: 'ZooKeeper → Controller Election'"
    - text: "Consumers can read from in-sync replicas"
      confidence: medium
      evidence: "Arrow from consumer to replica broker, labeled 'fetch'"
  associated_raw: raw/articles/kafka-guide-2026-05-01-f8e7d6c5.md
```

Per-image fields: `raw_path`, `content_hash` (dedup key), `analyzed_at`, `analysis_mode` (`multimodal` | `text-only`), `classification` (one of eight taxonomy values), `description`, `extracted_claims[]` (each with `text`, `confidence`, `evidence`), and optional `associated_raw` linking to the parent text source.

#### Extraction Rules by Classification

| Classification | What Gets Extracted | Confidence | Example |
|---------------|-------------------|------------|---------|
| `subject-photo` | Visual attributes for description — no factual claims | N/A | Photo of Raspberry Pi → "40-pin GPIO header, 4× USB-A ports" |
| `diagram` | Components, named relationships, directional flows, labels | `high` per label | "Service A calls B via gRPC" from labeled arrow |
| `chart` | Axis labels, explicit data points, trend direction, units | `high` for labels, `medium` for interpolated | "Redis: 120k ops/sec" from bar label |
| `screenshot` | Visible text: UI labels, config values, version strings, errors | `high` (text-in-image) | "PostgreSQL 15.2" from version banner |
| `illustration` | Nothing unless labeled components present | — | Placed for understanding, not as source |
| `infographic` | Statistics, named comparisons, timeline events | Mixed | Explicit numbers `high`, visual relationships `medium` |
| `decorative` | Nothing — excluded from wiki pages | — | — |

#### Integration with Cite-Then-Claim

Image annotations become source excerpts in the existing cite-then-claim pipeline. During Step 4 page writing, the LLM treats `extracted_claims` from annotations identically to text excerpts from raw files:

1. Select an extracted claim from the image annotation
2. Generate the wiki claim grounded in that evidence
3. Insert a `[^src-N]` marker (using `config.source_authority.markers.prefix`)
4. In `## Sources`, reference the image path and describe the visual evidence

The provenance chain: **image → annotation → claim → `[^src-N]` marker → verification ledger**. In the ledger, image-sourced claims carry `source_media` (e.g., `image/diagram`) and `extraction_confidence` to distinguish them from text-sourced claims. These fields are additive and optional — existing entries remain valid.

#### Page Type Placement Rules

| Page Type | Hero Image | Diagrams | Charts |
|-----------|-----------|----------|--------|
| `entity` | `subject-photo` after TL;DR | Core Concepts / Key Features | Attributes / Why-When to Use |
| `concept` | — | Core Concepts | When to Use |
| `pattern` | — | Pattern Variants | Selection Criteria |
| `recipe` | — | Problem | Verification |
| `comparison` | — | — | Decision Matrix / dimension sections |
| `reference` | — | — | Quick Reference / Details |

Only `entity` pages receive a hero image. Step illustrations are placed inline within the step they illustrate, preserving source order.

#### Density Guardrails

1. **Max images per page** — `config.images.max_per_page`. When exceeding the cap, prioritize by knowledge value: diagrams/charts first, then subject-photos, then illustrations.
2. **Min prose per image** — `config.images.min_prose_per_image` words of prose per image. A 300-word page includes at most 2 images at the default threshold.
3. **No consecutive images** — Intervening prose required between every pair of images. Exception: sequential step-illustrations in `recipe` pages.

#### Concrete Example

**Input:** A Kafka article (3,200 words) with an architecture diagram and a throughput benchmark chart.

**Step 4a annotations (abbreviated):**

```yaml
- raw_path: raw/assets/kafka-architecture-2026-05-10-a1b2c3d4.png
  classification: diagram
  extracted_claims:
    - text: "Kafka uses ZooKeeper for controller election"
      confidence: high
      evidence: "Label: 'ZooKeeper → controller election'"

- raw_path: raw/assets/kafka-throughput-2026-05-10-7b3e2f1a.png
  classification: chart
  extracted_claims:
    - text: "Kafka achieves 2.1M messages/sec throughput"
      confidence: high
      evidence: "Bar label: '2.1M msgs/sec'"
```

**Compiled wiki page (excerpt):**

```markdown
### TL;DR

Kafka is a distributed event streaming platform optimized for
high-throughput, fault-tolerant message delivery[^src-1].

![Kafka cluster architecture](raw/assets/kafka-architecture-2026-05-10-a1b2c3d4.png)
*Figure 1: Three-broker cluster with ZooKeeper managing controller election.[^src-3]*

### Core Concepts

Kafka clusters rely on ZooKeeper for controller election and metadata
management[^src-3]. In throughput benchmarks, Kafka achieves approximately
2.1 million messages per second[^src-4].

![Throughput comparison](raw/assets/kafka-throughput-2026-05-10-7b3e2f1a.png)
*Figure 2: Kafka vs RabbitMQ vs ActiveMQ throughput.[^src-4]*

### Sources

[^src-1]: "distributed streaming platform designed for high-throughput" — raw/articles/kafka-internals-2026-05-10-f8e7d6c5.md
[^src-3]: Diagram label: "ZooKeeper → controller election" — raw/assets/kafka-architecture-2026-05-10-a1b2c3d4.png
[^src-4]: Chart bar label: "Kafka 2.1M msgs/sec" — raw/assets/kafka-throughput-2026-05-10-7b3e2f1a.png
```

The diagram is placed after TL;DR as the entity hero image. The chart is placed inline in Core Concepts adjacent to the throughput claim. Both carry `[^src-N]` markers tracing to `raw/assets/` paths, with ledger entries recording `source_media` type.

### Image Provenance & Verification

Images in `raw/assets/` participate in the same provenance and verification infrastructure as text sources. The tier hierarchy is about *where* a source came from, not *what format* it is — a photo archived in `raw/assets/` is Tier 1, identical in authority to a markdown file in `raw/articles/`. Two new optional ledger fields (`source_media`, `extraction_confidence`) let the verification system apply appropriate scrutiny to visual claims without requiring a parallel provenance infrastructure.

#### Image as Source Tier

An image captured during import and stored in `raw/assets/` is a **Tier 1 raw source file**. It flows through the same provenance chain as text:

```
wiki/animals/maine-coon.md
  → body text: "Males typically reach 18–25 pounds[^src-3]"
    → ## Sources: [^src-3]: Chart axis label "Male Maine Coon 18–25 lbs"
                            — raw/assets/maine-coon-size-chart-2026-05-01-b7c4e2a1.png
      → ledger: { id: src-3, source_ref: raw/assets/..., source_media: image/chart }
        → file: raw/assets/maine-coon-size-chart-2026-05-01-b7c4e2a1.png
```

The `[^src-N]` markers use the same prefix and numbering sequence as text-sourced claims — there is no separate namespace. The `source_media` field in the ledger distinguishes image from text sources. The tier value remains `raw`, not a new tier. The same image found via web search during verification would be Tier 3. The tier reflects provenance, not format.

#### Verification Ledger Schema Extension

Two new optional fields on claim entries in `instance/state/verifications.yaml`, following the additive pattern from [ADR-0041](../decisions/0041-per-claim-ledger-schema.md):

| Field | Type | Values | Purpose |
|-------|------|--------|---------|
| `source_media` | string \| null | `image/chart`, `image/diagram`, `image/photo`, `image/screenshot`, `image/infographic`, `null` (default) | Media classification of the claim's source |
| `extraction_confidence` | enum \| null | `high`, `medium`, `low`, `null` (text sources omit) | Reliability of knowledge extraction from visual source |

Both fields are optional and default to null. Existing entries without them parse cleanly — no migration.

```yaml
# instance/state/verifications.yaml — image-sourced claims
- verified_at: '2026-05-02T10:00:00Z'
  mode: semi
  page: maine-coon
  claims:
    - id: src-3
      claim: "males typically reaching 18–25 pounds"
      source_tier_used: raw
      source_ref: raw/assets/maine-coon-size-chart-2026-05-01-b7c4e2a1.png
      source_url: https://example.com/cat-breeds/maine-coon-sizes
      source_excerpt: "Chart axis label: Male Maine Coon 18–25 lbs"
      excerpt_hash: "sha256:d4e5f6..."
      source_media: image/chart           # new field
      extraction_confidence: high          # new field
      writer_verdict: confirmed
      final_verdict: confirmed
    - id: src-4
      claim: "tufted ears, a bushy tail, and a prominent ruff"
      source_tier_used: raw
      source_ref: raw/assets/maine-coon-photo-2026-05-01-3f8a1d2e.jpeg
      source_url: https://example.com/cat-breeds/maine-coon-gallery
      source_excerpt: "Photo shows: pointed ear tufts, long bushy tail, thick fur ruff at neck"
      excerpt_hash: "sha256:a1b2c3..."
      source_media: image/photo            # new field
      extraction_confidence: medium         # new field
      writer_verdict: confirmed
      final_verdict: confirmed
```

#### How source_media Gets Populated

The compile protocol records `source_media` when extracting a claim from an image during cite-then-claim (Step 4). The LLM classifies the image during its analysis pass and writes the media type into the ledger entry alongside the provisional `[^src-N]` marker. The verify protocol does the same when sourcing a claim from an image during source escalation — if a Tier 1 raw image confirms a claim, the verification entry records the image's media type.

The `source_media` value maps from the image annotation's `classification` field: `chart` → `image/chart`, `photo` → `image/photo`, `diagram` → `image/diagram`, etc.

#### Extraction Confidence Semantics

The `extraction_confidence` field encodes how reliably knowledge was extracted from a visual source. It applies only to image-sourced claims — text-sourced claims omit it.

| Level | Meaning | Examples |
|-------|---------|---------|
| `high` | Directly readable — literal text, explicit labels, unambiguous elements | Chart axis label ("18–25 lbs"), diagram component name, OCR-extracted text, screenshot content |
| `medium` | Requires interpretation but grounded in clear visual evidence | Photo showing physical attributes, chart trend, diagram relationship (A connects to B) |
| `low` | Requires significant inference from ambiguous visual evidence | Approximate values from unlabeled chart positions, subjective judgments, species identification from photo |

#### Verification Behavior for Image-Sourced Claims

The adversarial writer/critic/judge model is text-to-text: the writer reads a claim, reads a source, and assesses agreement. This degrades for images — the critic cannot independently re-read an image source with the same fidelity. The critic's rebuttal would rely on the same alt-text and annotation the writer used, not independent visual analysis.

**Explicit trade-off: image-sourced claims cannot receive the same verification scrutiny as text-sourced claims without a multimodal critic.** The `extraction_confidence` field makes this asymmetry visible:

- **`high`** — Claim can be `confirmed` by the image alone. Writer assessment is sufficient; full adversarial mode not triggered unless `risk_tier: critical`.

- **`medium`** — Claim is `confirmed` provisionally but flagged for Tier 2/3 text corroboration during verify. If corroborated, the claim gains a dual source chain. If not, it remains confirmed at medium extraction confidence — does not block promotion unless `risk_tier: critical`.

- **`low`** — Claim is effectively **unverifiable from the image alone**. Must be corroborated by a text source (Tier 2/3) to receive `confirmed`. Uncorroborated `low` claims are marked `unverifiable` and **block confidence promotion** to `high`, per [Promotion Criteria](confidence-state-machine.md#promotion-criteria).

When multimodal verification becomes available (v2), the critic gains independent image analysis and the `medium`/`low` gates can be relaxed.

#### Source Health Extension

Image source URLs participate in [Source Health Monitoring](confidence-state-machine.md#source-health-monitoring). `check-source-health.py` performs HTTP liveness checks on `source_url` values from image-sourced ledger entries, identical to text URLs.

| Category | Image behavior |
|----------|---------------|
| **Source gone** | Image URL returns 4xx/5xx → page flagged for re-verification |
| **Source redirected** | Log final URL, re-verify if destination differs |
| **Excerpt missing** | N/A — substring matching doesn't apply to binary content |
| **Image drift** | **Deferred (v2)** — perceptual hashing to detect upstream image replacement |

The `content_hash` in `imports.yaml` detects re-import of a changed image, but proactive upstream drift monitoring requires perceptual hashing (v2).

#### Query and Index Extensions

`query-provenance.py` handles image sources transparently — no schema change. The `source_media` and `extraction_confidence` fields appear in provenance records when present:

```yaml
# query-provenance.py --page maine-coon --claim-id src-3
page: maine-coon
claim_id: src-3
claim_text: "males typically reaching 18–25 pounds"
verdict: confirmed
source_chain:
  tier: raw
  raw_path: raw/assets/maine-coon-size-chart-2026-05-01-b7c4e2a1.png
  source_url: https://example.com/cat-breeds/maine-coon-sizes
  source_media: image/chart
  extraction_confidence: high
```

Image URLs appear in `by-source-url.yaml` alongside text URLs with no schema change. `build-index.py` generates reverse index entries from the verification ledger without distinguishing image from text sources — the `source_media` distinction lives in the ledger, not the index.

### Graceful Degradation

Not every LLM has multimodal capabilities. The platform detects this via a single config flag — `config.images.multimodal_available` — and adjusts behavior accordingly. Wiki pages are never broken by the absence of multimodal analysis; they are enriched by its presence.

#### Capability Detection

The flag `config.images.multimodal_available` defaults to `false`. The instance operator sets it to `true` when the operating LLM can accept image inputs. No runtime probing — the operator knows their model's capabilities.

#### Degradation Matrix

| Capability | Full Multimodal | Text-Only |
|-----------|----------------|-----------|
| Image capture to `raw/assets/` | ✅ | ✅ |
| Classification by role | ✅ from image content | ✅ from alt text + filename + context |
| Description / captioning | ✅ from image content | ✅ from alt text + surrounding prose |
| Knowledge extraction | ✅ claims from visual content | ❌ no extraction without visual access |
| `extraction_confidence` | high (text-in-image) or medium (interpreted) | low (inferred from context only) |
| Placement in wiki pages | ✅ with informed captions | ✅ with context-derived captions |

**Text-only mode** relies on three signals: alt text from the source HTML (preserved by Jina Reader), the image filename (often descriptive — `kafka-architecture-diagram.png`), and the surrounding prose (the paragraph before/after the image reference). These signals are sufficient for ~80% of images encountered in technical content.

**When all signals are absent** — no alt text, generic filename, no descriptive surrounding prose — the image is classified as `unknown`, included in the wiki page without a caption, and no claims are extracted from it. This is the honest floor: the platform acknowledges it cannot understand the image rather than guessing.

## Configuration

All image-related settings live under `config.images` in `defaults.yaml`. Instance operators override any subset in `instance/config.yaml` (standard deep merge).

```yaml
images:
  enabled: true                    # master switch — false skips all image processing
  multimodal_available: false      # operator sets true when LLM accepts image inputs
  capture:
    enabled: true                  # download images during import
    max_size_mb: 10                # skip images larger than this
    max_per_source: 20             # max images to capture per imported source
    min_dimensions: [100, 100]     # skip images smaller than WxH (filters icons/spacers)
    allowed_formats:               # accepted image formats
      - jpeg
      - png
      - webp
      - svg
      - gif
    timeout_seconds: 15            # per-image download timeout
  classify:
    filter_decorative: true        # exclude decorative images from wiki pages
    default_confidence: low        # extraction_confidence when no multimodal available
  compile:
    max_per_page: 6                # hard cap on images per wiki page
    min_words_per_image: 150       # minimum prose words per image (density guardrail)
```

| Key | Purpose |
|-----|---------|
| `enabled` | Master switch. When `false`, import skips image download, compile ignores image references. Existing pages with images are unaffected. |
| `multimodal_available` | Capability flag. Controls whether compile sends images to the LLM for visual analysis or relies on text-only signals. |
| `capture.enabled` | Allows disabling image download while keeping compile-time image handling for previously captured assets. |
| `capture.max_size_mb` | Prevents bloating `raw/assets/` with oversized images. Skipped images log a warning. |
| `capture.max_per_source` | Caps capture for image-heavy sources (e.g., 50-image tutorials). Prioritizes by document order. |
| `capture.min_dimensions` | Filters tracking pixels, spacer GIFs, and tiny icons that carry no knowledge value. |
| `capture.allowed_formats` | Restricts to web-standard image formats. Rejects uncommon formats that may not render. |
| `capture.timeout_seconds` | Per-image timeout. Failed downloads are skipped with a warning — import never fails due to an unreachable image. |
| `classify.filter_decorative` | When `true`, images classified as `decorative` are excluded from wiki pages. |
| `classify.default_confidence` | Baseline `extraction_confidence` for image-derived claims in text-only mode. |
| `compile.max_per_page` | Prevents image-heavy wiki pages. Excess images are dropped by relevance score. |
| `compile.min_words_per_image` | Density guardrail — ensures pages have substantive prose, not just image galleries. |

## Integration Points

### Protocol Changes

| Protocol | Change | Scope |
|----------|--------|-------|
| `import.md` | Add image download sub-step after fetch; record image assets in `imports.yaml` | Additive — new sub-step in Step 2/4 |
| `compile.md` | Add Step 4a (image analysis); extend cite-then-claim for image sources | Additive — new sub-step, prompt extension |
| `verify.md` | Recognize `source_media` and `extraction_confidence` in ledger entries; apply confidence-gated corroboration | Minor — field awareness in existing phases |

### New Scripts

| Script | Purpose |
|--------|---------|
| `check-images.py` | Validates image references in wiki pages: file exists in `raw/assets/`, alt text present, dimensions within bounds. Runs as part of `verify.sh`. |

### Extended Validators

| Validator | Extension |
|-----------|-----------|
| `check-frontmatter.py` | Accepts optional `media` field in `sources[]` entries; accepts `images_cited` field |

### Extended State Files

| State File | Extension |
|-----------|-----------|
| `imports.yaml` | Optional `assets` list per entry linking to captured images with `image_format`, `dimensions`, `associated_with` fields |
| `verifications.yaml` | `source_media` and `extraction_confidence` fields on claim entries (additive, optional — backward compatible) |
| `image-annotations.yaml` (new) | Structured text descriptions produced by compile Step 4a; keyed by `content_hash` for staleness detection |

### Scaffold Changes

`sprue init` must scaffold `raw/assets/` alongside the other `raw/` subdirectories. Currently `init.py` only creates the top-level `raw/` directory — add `raw/assets/` to `_INSTANCE_DIRS` so it exists before the first import.

## Migration

The design is fully additive and backward-compatible. Existing KBs continue to work without modification.

**Existing wiki pages (no images):**
- Fully valid. No frontmatter fields are added retroactively.
- Page type contracts make hero images optional, not mandatory.
- `check-images.py` only validates pages that contain image references; pages without them are skipped.

**Existing imports (no `assets` field in `imports.yaml`):**
- Parse cleanly. The `assets` field is optional.
- Compile Step 4a runs only when the raw source contains image references.

**Existing verification ledger entries:**
- `source_media` and `extraction_confidence` default to null. Text-sourced claims omit them.

**What does NOT happen automatically:**
- **No retroactive image capture.** The raw snapshot is immutable — the platform does not re-fetch existing sources to download images that were missed at original import time.
- **No automatic enrichment of old wiki pages.** The normal verify and enhance cadence does not retroactively add images to pages compiled before this feature existed.

**Enriching existing pages with images (manual workflow):**
- Re-import the source. The new import captures images per the new pipeline, creating a fresh raw file with `assets`.
- Re-compile the affected wiki page from the new raw. The new compilation treats the old wiki page as being superseded — the compile protocol's existing re-compile behavior handles this.
- This is an operator-initiated workflow, not an automatic backfill.

**Opt-in or opt-out at instance level:**
- New KBs created via `sprue init` get `config.images.enabled: true` (the default in `defaults.yaml`). They benefit from image support immediately on first import.
- Existing instances upgrading to a Sprue version with this feature inherit the default `true` as well, but because the feature only activates on *new* imports, existing content is unaffected. Operators who prefer text-only KBs can override to `false` in their instance `config.yaml`.

## Specs

- [Visual Knowledge](../specs/visual-knowledge.md) — images are first-class knowledge sources; capture, classification, and graceful degradation invariants

## Interfaces

| Artifact | Role |
|----------|------|
| `imports.yaml` | Records captured image assets alongside text sources |
| `verifications.yaml` | Stores `source_media` and `extraction_confidence` per image-derived claim |
| `image-annotations.yaml` | Structured image descriptions produced at compile time |
| `raw/assets/` | Immutable storage for captured image files |
| `check-images.py` | Validates image references, alt text, and file existence |
| `compile-attributed.md` prompt | Extended for image-aware cite-then-claim generation |
| `config.images.*` | All image pipeline configuration |

## Decisions

TBD — ADRs will be created during implementation:
- Capture pipeline architecture (download strategy, raw immutability for image URLs)
- Annotation schema (single ledger vs per-image sidecar files)
- Multimodal capability detection (config flag vs runtime probing)
