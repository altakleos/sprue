# Strategy: raw_summary
# Minimal capture: TL;DR + bullet points. No wiki structure overhead.

Produce a minimal summary of this source. No full wiki page structure — just capture the key information fast.

## Output Format

```markdown
---
type: source-summary
tech: [inferred]
domain: [from {{facets}}]
concerns: []
confidence: medium
author: llm
last_verified: null
risk_tier: reference
summary: "[One sentence: what this source is about]"
---

# [Source Title]

## TL;DR

[2-3 sentences maximum]

## Key Points

- [Bullet point — most important takeaway]
- [Bullet point]
- [Bullet point]
- ...

## Source

[URL or file reference]
```

Ignore depth setting — this strategy is always minimal by design.

---

Source content:

{{source}}
