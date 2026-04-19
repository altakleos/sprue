# Strategy: wiki_page
# Default compilation strategy. Produces a full wiki page following the
# page type contract from .sprue/defaults.yaml → page_types:.

Transform the source into a wiki page for the audience described in `instance/identity.md`.

## Instructions

1. **Pick the page type** from `.sprue/defaults.yaml` → `page_types:` that best fits the source content. Read the `description` field to decide — it explains what each type is for.
2. **Follow the section contract** for that type exactly. Every listed section must appear. Do not add extra top-level sections.
3. **Assign frontmatter** per `.sprue/engine.md` schema:
   - `confidence: medium` (default) or `low` (speculative/opinion). **Never `high`** — reserved for verify.
   - `author: llm`, `last_verified: null`, `provenance: sourced`.
   - Facets from {{facets}}.
4. **Write for the audience** in {{audience}} — skip basics they already know, focus on gotchas, tradeoffs, and practical detail.
5. **Link liberally** with `[[wikilinks]]` to existing pages on first meaningful mention.
6. **Include a mermaid diagram** when the topic involves a flow, lifecycle, or decision tree.
7. **Preserve numbers exactly** — latencies, limits, thresholds, versions from the source.

## Depth: {{depth}}

Word targets come from the page type's `size_profile` in `instance/config.yaml` → `size_profiles`.

- **shallow**: TL;DR + one key insight per section. Target the profile's `min_words`.
- **standard**: Full treatment of each section. Concrete examples. Target the midpoint between `min_words` and `max_words`.
- **deep**: Exhaustive. Edge cases, failure modes, version-specific behavior. Target up to `max_words`.

## Output Format

```markdown
---
type: <from .sprue/defaults.yaml → page_types:>
domain: [<values>]
topic: [<values>]
aspect: [<values>]
confidence: medium
decay_tier: <fast|medium|stable|glacial>
author: llm
provenance: sourced
last_verified: null
risk_tier: <critical|operational|conceptual|reference>
summary: "<one sentence>"
---

# [Page Title]

## TL;DR

[2-3 sentences]

## [Remaining sections per type contract]

...

## See Also

- [[related-page]]
```

For `entity` type pages, also populate `## Attributes` (Kind required, plus other applicable attributes) and `## Relationships` (typed edges using `[[wikilinks]]`). Read `instance/entity-types.yaml` for allowed kinds and relationship types.

## Image Placement

When `{{image_annotations}}` is non-empty, place images from the source's annotations into the page. Images with classification `decorative` or `unknown` are never placed.

### Placement by page type

| Page type | Hero image | Inline placement |
|-----------|-----------|------------------|
| entity | `subject-photo` after H1, before TL;DR | Diagrams in Core Concepts/Key Features; charts in Attributes or Why/When to Use |
| concept | — | Diagrams in Core Concepts |
| pattern | — | Diagrams in Pattern Variants |
| recipe | — | Step illustrations inline with steps |
| comparison | — | Charts in Decision Matrix or dimension sections |
| reference | — | Charts in Quick Reference or detail tables |
| decision | — | Rare — only if source has relevant diagram |
| opinion | — | Avoid unless source has supporting chart |
| question | — | Usually none |

### Hero image (entity pages only)

Select the annotation classified `subject-photo`. If multiple, pick the one whose description best matches the page's primary subject. Place immediately after the H1 title and before TL;DR with a descriptive caption.

### Density guardrails

- Cap total images at `config.images.compile.max_per_page` (default 6).
- At least `config.images.compile.min_words_per_image` words of prose per image (default 150).
- No two consecutive images without intervening prose (exception: sequential step illustrations in recipe pages).
- When exceeding the cap, prioritize by knowledge value: diagrams/charts → subject-photos → illustrations. Drop any remaining.

### Image syntax

```markdown
![alt text](raw_path)
*Figure N: description.[^src-N]*
```

Omit the `[^src-N]` marker when the image is illustrative only (no claim): `*Figure N: description.*`

---

Source content:

{{source}}

Image annotations (may be empty):

{{image_annotations}}
