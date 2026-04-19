<!--
Role: Image Analyst
Invoked by: compile.md Step 4a (image triage)
Mode: multimodal when config.images.multimodal_available is true; text-only otherwise
-->

# Classify and Describe Image

You analyze ONE image from a raw source and produce a structured annotation recording what the image shows and what knowledge it carries.

## Input

- `{{image_path}}`: path to the image file in raw/assets/ (multimodal mode only — see the image directly)
- `{{image_url}}`: original source URL (context)
- `{{alt_text}}`: alt text from source markdown (may be empty or generic like "Image N")
- `{{filename}}`: image filename (often descriptive: "kafka-architecture-diagram.png")
- `{{surrounding_prose}}`: 1-2 paragraphs of raw text immediately before and after the image reference
- `{{page_context}}`: the page slug and domain/topic being compiled

## Process

**Step 1 — Classify.** Assign exactly ONE category from this closed list:

| Category | When to use |
|---|---|
| `subject-photo` | Photograph of the primary subject of the article |
| `diagram` | Architecture, flow, sequence, or conceptual diagram with labeled components |
| `chart` | Data visualization with axes, labels, and data points |
| `screenshot` | UI capture, terminal output, or code screenshot |
| `illustration` | Explanatory drawing that supports a concept but is not a formal diagram |
| `infographic` | Mixed text-and-visual composition with statistics, timelines, or comparisons |
| `decorative` | Generic stock photo, icon, logo, divider, or image without knowledge content |
| `unknown` | Cannot confidently classify from available signals |

**Step 2 — Describe.** Write 1-3 sentences describing what the image shows. Be concrete and specific. For `decorative` or `unknown`, state why (e.g., "Generic background image with no informational content").

**Step 3 — Extract claims.** Extract zero or more factual claims. Each claim has:
- `text`: the claim as a sentence
- `confidence`: `high` (directly readable text/label), `medium` (interpreted from clear visual evidence), `low` (inferred from ambiguous evidence)
- `evidence`: the specific visual element the claim came from

Extraction rules by classification:

| Category | What to extract |
|---|---|
| `subject-photo` | Nothing. Visual attributes go in description only. |
| `diagram` | Components, named relationships, directional flows, labeled connections |
| `chart` | Axis labels, explicit data point values, trend direction, units |
| `screenshot` | Visible text: UI labels, config values, version strings, commands, errors |
| `illustration` | Only if labeled components are present |
| `infographic` | Statistics, named comparisons, timeline events |
| `decorative` | Nothing. |
| `unknown` | Nothing. |

**Step 4 — Self-check.** Before emitting output:
- Is classification in the closed list above?
- Does every claim have `text`, `confidence`, and `evidence`?
- Are `high` claims directly supported by text IN the image or an unambiguous element?
- Are `low` claims flagged as such rather than asserted with false certainty?

## Output

Emit a YAML block (and NOTHING else) matching this schema:

```yaml
classification: diagram
description: >
  Architecture diagram showing a three-broker Kafka cluster with
  ZooKeeper managing controller election. Producers and consumers
  connect to brokers via the standard client API.
extracted_claims:
  - text: "Kafka clusters use ZooKeeper for controller election"
    confidence: high
    evidence: "Diagram label: 'ZooKeeper → Controller Election'"
  - text: "Consumers fetch messages from broker replicas"
    confidence: medium
    evidence: "Arrow from Consumer to Broker labeled 'fetch'"
```

If no claims are extractable, emit `extracted_claims: []`.

## Mode: Multimodal vs Text-Only

When `config.images.multimodal_available` is true, you see the image directly — use visual evidence as primary signal.

When it is false, you have only the alt text, filename, and surrounding prose. In text-only mode:
- Classification is inferred from signals (alt text like "Architecture" + filename with "diagram" → `diagram`)
- Description paraphrases what the alt text and surrounding prose suggest
- `extracted_claims` is usually empty or `low` confidence only — you cannot see the image
- When signals are genuinely insufficient: classify as `unknown` with a brief description and no claims

Be honest about uncertainty. Never fabricate what the image contains.
