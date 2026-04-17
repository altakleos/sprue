# ═══════════════════════════════════════════════════════════════════════════════
# Compilation Prompts — .sprue/prompts/README.md
# ═══════════════════════════════════════════════════════════════════════════════
#
# Each file in this directory is a prompt template for a compile.strategy.
# The agent reads the appropriate template during the compile stage.
#
# Variables available in templates:
#   {{source}}    — the fetched source content
#   {{contract}}  — the page type section contract from .sprue/engine.md
#   {{audience}}  — the audience description from instance/identity.md
#   {{facets}}    — the controlled vocabularies from .sprue/defaults.yaml → facets:
#   {{depth}}     — shallow | standard | deep
#
# To add a custom strategy:
#   1. Create .sprue/prompts/my-strategy.md
#   2. Use it: compile.strategy: my-strategy (in pipeline.yaml or --compile.strategy)
#
# Built-in strategies:
#   wiki_page.md    — default full wiki page (delegates to .sprue/engine.md contracts)
#   key_claims.md   — extract numbered claims with evidence strength
#   concept_map.md  — structured concept → relationship → concept map
#   code_extract.md — pull out code examples with context
#   flashcards.md   — Q&A pairs for spaced repetition
#   raw_summary.md  — minimal TL;DR + bullets
#
# Verify roles (used by .sprue/protocols/verify.md --adversarial):
#   verify-writer.md — single-pass claim assessment
#   verify-critic.md — adversarial rebuttal of writer's verdict
#   verify-judge.md  — tie-breaker between writer and critic
