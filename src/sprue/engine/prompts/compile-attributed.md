# Compile: Attributed Page Generation
# Cite-then-claim constrained generation for sourced pages.
# Invoked during .sprue/protocols/compile.md Step 4 (page writing).

You are compiling a wiki page from raw source material. Every verifiable factual claim you write must be grounded in a specific excerpt from the raw source — not your training knowledge. Select the excerpt first, then write the claim.

## Input

- `{{raw_files}}` — one or more raw source files to compile from
- `{{slug}}` — target wiki page slug
- `{{page_type}}` — page type and section contract to follow
- `{{manifest_context}}` — existing pages, facets, and link targets
- `{{image_annotations}}` — annotations from `image-annotations.yaml` for images in the current raw source (may be empty). Each annotation has: `raw_path`, `classification`, `description`, `extracted_claims[]` (each with `text`, `confidence`, `evidence`)

## Process

For each verifiable claim (version numbers, defaults, limits, behavioral assertions, security properties):

1. **Select the excerpt.** Find the specific sentence in the raw source that states the fact.
2. **Write the claim.** Generate your sentence grounded in that excerpt — do not embellish beyond what the source says.
3. **Insert the marker.** Append `[^src-N]` immediately after the claim, numbering sequentially from 1.
4. **Record the source.** Save the excerpt and raw file path for the Sources section.

Claims that synthesize across multiple source sections with no single supporting excerpt: write without a marker. These count toward `claims_unverifiable`. Non-verifiable content (opinions, tautologies, hedged guidance) does not need markers.

### Image-sourced claims

When `{{image_annotations}}` is non-empty, treat each annotation's `extracted_claims` as citable excerpts — identical to text excerpts. The annotation's `description` is background context only; do not cite it. Apply the same four steps above: select the claim from the annotation, write grounded in its `evidence`, insert `[^src-N]` in the same numbering sequence as text citations, and record the image's `raw_path` in the Sources section. Skip annotations classified as `decorative` or `unknown` — they carry no citable knowledge.

### Image placement in body

When citing an image-sourced claim, you may place the image near the claim:

```markdown
![<description>](<raw_path>)
*Figure N: <description>.[^src-N]*
```

The caption references the same marker as the claim it illustrates. If the image supports multiple claims, the caption cites the most prominent one. Entity pages: place a `subject-photo` hero image directly after TL;DR with a descriptive caption. Diagrams and charts go inline in the relevant section.

### Classification → source_media mapping

| Annotation classification | `source_media` value |
|---------------------------|----------------------|
| `subject-photo` | `image/photo` |
| `diagram` | `image/diagram` |
| `chart` | `image/chart` |
| `screenshot` | `image/screenshot` |
| `illustration` | `image/illustration` |
| `infographic` | `image/infographic` |
| `decorative` | *(skip — do not cite)* |
| `unknown` | *(skip — do not cite)* |

## Rules

- **Excerpt first, claim second.** Never write a claim then hunt for a source. The excerpt drives the claim.
- **One excerpt per marker.** Each `[^src-N]` traces to exactly one passage — do not combine excerpts.
- **Verbatim excerpts.** Record the source's actual words, not a paraphrase. Keep to 1–2 sentences.
- **No fabricated precision.** If the source says "up to 200K" do not write "exactly 200,000."
- **Target >80% coverage.** At least 80% of verifiable claims should carry markers. 100% is not required.

## Sources Section

After all page content, append `## Sources` (before `## See Also` if present) with footnote definitions:

```markdown
## Sources

[^src-1]: "exact excerpt from source" — raw/filename.md
[^src-2]: "exact excerpt from source" — raw/filename.md
```

For image-sourced claims, the footnote references the annotation's `evidence` and the image's `raw_path`:

```markdown
[^src-3]: Diagram label: "ZooKeeper → controller election" — raw/assets/kafka-architecture-1-a1b2c3d4.png
```

## Verification Ledger

Image-sourced claims carry two additional fields in `instance/state/verifications.yaml`:

- `source_media` — mapped from the annotation's classification (see table above)
- `extraction_confidence` — copied from the annotation claim's `confidence` field
- `source_ref` — the annotation's `raw_path` (the `raw/assets/` image file)
- `source_url` — the image's `original_url` from `imports.yaml`
- `source_excerpt` — the annotation's `evidence` field

Text-sourced claims omit `source_media` and `extraction_confidence` (they remain null/absent).

## Example

**Raw source** (`raw/articles/kafka-guide.md`):
> The default retention period is 7 days (168 hours). A single cluster supports up to 200,000 partitions.

**Resulting wiki text:**

```markdown
Kafka defaults to 7-day log retention[^src-1]. A single cluster supports up to 200,000 partitions[^src-2].

## Sources

[^src-1]: "The default retention period is 7 days (168 hours)" — raw/articles/kafka-guide.md
[^src-2]: "A single cluster supports up to 200,000 partitions" — raw/articles/kafka-guide.md
```

**With image annotation** (annotation for `raw/assets/kafka-throughput-1-7b3e2f1a.png`, classification: `chart`, extracted claim: "Kafka achieves 2.1M messages/sec", confidence: `high`, evidence: "Bar label: 2.1M msgs/sec"):

```markdown
In throughput benchmarks, Kafka achieves approximately 2.1 million messages per second[^src-3].

![Throughput comparison](raw/assets/kafka-throughput-1-7b3e2f1a.png)
*Figure 1: Kafka vs RabbitMQ vs ActiveMQ throughput.[^src-3]*

## Sources

[^src-1]: "The default retention period is 7 days (168 hours)" — raw/articles/kafka-guide.md
[^src-2]: "A single cluster supports up to 200,000 partitions" — raw/articles/kafka-guide.md
[^src-3]: Bar label: "2.1M msgs/sec" — raw/assets/kafka-throughput-1-7b3e2f1a.png
```
