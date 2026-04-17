# Strategy: key_claims
# Extracts verifiable claims with evidence ratings.

Extract every distinct technical claim from the source below. For each claim:

1. State the claim as a single sentence
2. Rate evidence strength: **strong** (benchmarks, measurements, RFC), **moderate** (authoritative docs, expert consensus), **weak** (opinion, anecdote, single source)
3. Note any conditions or caveats
4. If the claim includes a number (latency, throughput, cost, limit), preserve it exactly

## Output Format

```markdown
---
type: source-summary
tech: [inferred from content]
domain: [from {{facets}}]
concerns: [from {{facets}}]
confidence: medium
author: llm
last_verified: null
risk_tier: reference
summary: "Key claims extracted from [source title]"
---

# [Source Title] — Key Claims

## TL;DR

[2-3 sentence summary of what the source argues]

## Claims

1. **[Claim]** — Evidence: strong/moderate/weak
   - Context: [when this applies]
   - Caveat: [limitations]

2. ...

## Relevance

[How these claims connect to existing wiki knowledge. Add [[wikilinks]].]

## What It Changes

[Which existing wiki pages might need updating based on these claims.]
```

Depth adjustment (values from `config.prompts.key_claims`):
- **shallow**: top `config.prompts.key_claims.shallow` claims only
- **standard**: `config.prompts.key_claims.standard` — all claims with moderate+ evidence
- **deep**: `config.prompts.key_claims.deep` — every claim including weak evidence, with full context

---

Source content:

{{source}}
