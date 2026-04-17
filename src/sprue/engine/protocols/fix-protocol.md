# Content Fix Protocol

How the LLM agent verifies and fixes wiki content using prepared context.
This runs as part of the `maintain` operation, after `lint` and `verify-content`.

## Prerequisites

1. Run `python3 .sprue/scripts/verify-content.py` to extract claims from pages
2. Run `python3 .sprue/scripts/fix-content.py --tier critical` (or other filter) to fetch authoritative sources and prepare context files
3. Context files are in `wiki/.index/fix-context/{slug}.md`

## Agent Workflow

For each context file in `wiki/.index/fix-context/`:

### Step 1: Read the context file

It contains:
- Extracted claims with line numbers and types
- Fetched authoritative source content
- Active corrections from `memory/corrections.md`
- The full current page content

### Step 2: Compare each claim against the authoritative source

For each extracted claim, determine:

- **confirmed** — the authoritative source explicitly supports this claim
- **contradicted** — the authoritative source says something different (this is a fix candidate)
- **stale** — the claim references a specific version or date that may have changed
- **unverifiable** — the authoritative source doesn't address this claim

**Rules:**
- Only mark `contradicted` if you have a specific quote from the authoritative source that disagrees
- When in doubt, mark `unverifiable` — never guess
- Temporal claims (version numbers, "since version X", "as of") are `stale` unless the source confirms the current version

### Step 3: Apply fixes for contradicted claims

For each `contradicted` claim:

1. **Cite the evidence.** Quote the authoritative source excerpt that contradicts the claim.
2. **Surgical edit only.** Fix the specific sentence or value. Never rewrite entire sections.
3. **Add inline citation.** After the fixed claim, add the source: `([source](url))`.
4. **Log the fix.** Append to `wiki/.index/fix-log.jsonl`:
   ```json
   {"date":"YYYY-MM-DD","page":"slug","section":"## Section","old":"wrong claim","new":"correct claim","source":"url","evidence":"quote from source","error_type":"stale_version|wrong_default|magnitude|inverted_boolean|conflated|hallucinated"}
   ```
5. **Add a correction.** Append to `memory/corrections.md` so the retirement lifecycle can track whether the LLM reproduces the error on future writes:
   ```
   - **page / topic**: Do not claim [old]. The correct value is [new].
     wrong: [old claim]
     right: [new claim]
     probe: [distinctive token from new claim — version number, proper noun, rare phrase]
     source: [url]
     added: YYYY-MM-DD
     passes: 0
   ```
   The `probe` is load-bearing: `check-constraints.py` verifies it is *present* on scoped pages, catching the failure mode where a fix deletes the wrong claim without adding the correct content. Pick a token that would survive a reasonable paraphrase.

### Step 4: Handle stale claims

For claims marked `stale`:
- If the authoritative source confirms the current value → mark as `confirmed`, no fix needed
- If the source shows a different current value → fix it (same as `contradicted`)
- If the source doesn't address it → add a `> ⚠️ **Unverified**:` callout before the claim

### Step 5: Update page metadata

After fixing a page:
- Set `last_verified: YYYY-MM-DD` (today's date) in frontmatter
- Adjust `confidence` based on results:
  - All claims confirmed → keep current confidence
  - Some claims fixed with authoritative sources → keep `high` (now corrected with evidence)
  - Unverifiable claims remain → set `medium`
  - Major structural issues found → set `low`

### Step 6: Respect active corrections

Before writing any content, check `memory/corrections.md` for active corrections on this page.
Every active correction must be satisfied in the final content. If a fix would reintroduce a
corrected error, the correction takes precedence.

### Step 7: Check correction retirement

After updating a page with active corrections, evaluate each correction:
- Does the new content naturally satisfy the correction (without the correction being explicitly enforced)?
- If yes, increment `passes` on the correction
- After 3 consecutive passes, the correction is eligible for retirement

## What NOT to Do

- **Never fix without evidence.** If you can't point to a specific source excerpt, don't change the claim.
- **Never rewrite entire pages.** Surgical edits only. The page structure and voice should be preserved.
- **Never mark a page as verified if sources weren't fetched.** `last_verified` means "checked against authoritative sources," not "an LLM read it."
- **Never present LLM reasoning as verification.** If the fix is based on your training data rather than a fetched source, say so explicitly and set confidence accordingly.
- **Never silently drop unverifiable claims.** Flag them visibly so the reader knows.

## Integration with Maintenance

In `.sprue/protocols/maintain.md`, the verify-and-fix cycle runs after lint:

```
lint → verify-content (extract claims) → fix-content (fetch sources) → agent fixes → rebuild-index
```

The agent processes fix context files in risk-tier order: critical → operational → conceptual → reference.

## Audit Trail

Every fix is logged to `wiki/.index/fix-log.jsonl`. This log IS the verification record —
it's more useful than a `reviewed: true` flag because it records what was checked, against
what source, and what changed. The log is append-only and never pruned.
