# Compile: Attributed Page Generation
# Cite-then-claim constrained generation for sourced pages.
# Invoked during .sprue/protocols/compile.md Step 4 (page writing).

You are compiling a wiki page from raw source material. Every verifiable factual claim you write must be grounded in a specific excerpt from the raw source — not your training knowledge. Select the excerpt first, then write the claim.

## Input

- `{{raw_files}}` — one or more raw source files to compile from
- `{{slug}}` — target wiki page slug
- `{{page_type}}` — page type and section contract to follow
- `{{manifest_context}}` — existing pages, facets, and link targets

## Process

For each verifiable claim (version numbers, defaults, limits, behavioral assertions, security properties):

1. **Select the excerpt.** Find the specific sentence in the raw source that states the fact.
2. **Write the claim.** Generate your sentence grounded in that excerpt — do not embellish beyond what the source says.
3. **Insert the marker.** Append `[^src-N]` immediately after the claim, numbering sequentially from 1.
4. **Record the source.** Save the excerpt and raw file path for the Sources section.

Claims that synthesize across multiple source sections with no single supporting excerpt: write without a marker. These count toward `claims_unverifiable`. Non-verifiable content (opinions, tautologies, hedged guidance) does not need markers.

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
