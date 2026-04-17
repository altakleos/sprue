# Strategy: flashcards
# Generates Q&A pairs for spaced repetition.

Generate flashcard-style Q&A pairs from the source. Target the audience defined in `instance/identity.md` — no basics, focus on gotchas, tradeoffs, limits, and "why" questions.

## Output Format

```markdown
---
type: source-summary
tech: [inferred]
domain: [from {{facets}}]
concerns: [from {{facets}}]
confidence: medium
author: llm
last_verified: null
risk_tier: reference
summary: "Flashcards from [source title]"
---

# [Topic] — Flashcards

## TL;DR

[Source summary, 1-2 sentences]

## Cards

**Q1:** [Question — prefer "why", "when", "what happens if" over "what is"]
**A1:** [Concise answer, 1-3 sentences. Include numbers where relevant.]

**Q2:** ...
**A2:** ...

## See Also

[[relevant-wiki-pages]]
```

Depth adjustment (values from `config.prompts.flashcards`):
- **shallow**: `config.prompts.flashcards.shallow` cards, highest-value facts only
- **standard**: `config.prompts.flashcards.standard` cards covering all key points
- **deep**: `config.prompts.flashcards.deep` cards including edge cases and "what breaks when" scenarios

---

Source content:

{{source}}
