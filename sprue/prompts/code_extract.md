# Strategy: code_extract
# Pulls out code examples with context. Skips prose analysis.

Extract every code example, configuration snippet, CLI command, and technical pattern from the source. For each:

1. Preserve the code exactly (don't rewrite or "improve" it)
2. Add a one-line purpose comment if missing
3. Note the language/runtime/framework
4. Add context: what problem does this solve, when would you use it

## Output Format

```markdown
---
type: recipe
tech: [inferred]
domain: [from {{facets}}]
concerns: [from {{facets}}]
confidence: medium
author: llm
last_verified: null
risk_tier: reference
summary: "Code examples from [source title]: [what they demonstrate]"
---

# [Topic] — Code Examples

## TL;DR

[What these examples demonstrate, 1-2 sentences]

## Examples

### [Example 1 Title — what it does]

**When to use:** [one line]

\`\`\`language
// purpose comment
[code]
\`\`\`

**Gotcha:** [if any sharp edge exists in this code]

### [Example 2 Title]
...

## See Also

[[relevant-wiki-pages]]
```

Depth adjustment (values from `config.prompts.code_extract`):
- **shallow**: top `config.prompts.code_extract.shallow` most useful examples
- **standard**: `config.prompts.code_extract.standard` — all examples with context
- **deep**: `config.prompts.code_extract.deep` — all examples plus inferred patterns and edge cases

---

Source content:

{{source}}
