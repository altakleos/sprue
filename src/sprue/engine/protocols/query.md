# Query Operation

Triggered when the human asks a question about a technology.

## Steps

1. Read `wiki/.index/by-domain.yaml` or `wiki/.index/by-topic.yaml` to find relevant pages by topic
2. Read `wiki/.index/manifest.yaml` entries for those pages (check summaries for relevance)
3. Read the most relevant pages (prefer pages with `confidence: high`)
4. Synthesize an answer with [[wikilink]] citations
5. If the answer is valuable, offer to file it as a new wiki page (comparison, recipe, or concept)

**Fallback:** if the index files don't exist, read `wiki/overview.md` instead.

## Semantic Search

Preferred entry point for natural-language questions; faster and more accurate than tag-based lookup.

```bash
python3 .sprue/scripts/semantic-search.py "query" [--top N] [--threshold F] [--json]
```

**Contract:**
- Unit: H2 sections (not whole pages) — a page can surface multiple matching sections.
- Model: `all-MiniLM-L6-v2`, 384-dim embeddings, cosine similarity.
- Defaults: `--top 10`, `--threshold 0.25`. Threshold ≥0.4 is strong relevance; 0.25–0.4 is a loose fit; below 0.25 is dropped.
- Output (`--json`): list of `{slug, section, title, score}` sorted by score desc.
- Storage: reads `wiki/.index/search.db` (SQLite); falls back to `wiki/.index/embeddings.jsonl` if the DB is missing.
- Preconditions: embeddings must exist. If `search.db` and `embeddings.jsonl` are both absent, run `python3 .sprue/scripts/build-embeddings.py` (or `maintain rebuild-index`) first.

**Slug resolution:** results return slugs like `dsp-program`, not paths. Resolve with `find wiki -name "<slug>.md"` per AGENTS.md — wiki pages live in subdirectories, never assume `wiki/<slug>.md` directly.

**Score interpretation:** scores are noisy below 0.35. Combine top-K retrieval with a read of `wiki/.index/manifest.yaml` summaries to confirm relevance before citing.

## Query Plans

For common multi-hop questions: read `wiki/.index/query-plans.yaml` for curated reading paths. Match the user's question to a plan pattern, then read the `core_pages` + relevant `conditional_pages`.

## Provenance Check

When the user asks where a fact came from or what the source is for a specific claim, run a provenance query instead of searching the wiki.

1. Identify the page slug and claim ID (the `[^src-N]` marker on the claim)
2. Run `python3 .sprue/scripts/query-provenance.py --page <slug> --claim-id <id> --json`
3. Surface the `source_chain.tier`, `source_chain.source_url`, `source_chain.excerpt`, and `verification.verified_at` in the response
4. If no claim ID is visible, use `--page <slug> --all` and match by claim text

Trigger phrases: "where did this fact come from?", "what's the source for X?", "how was this verified?"

## Source Quality in Responses

When answering any question, include the source tier and verification date if the cited page has them. Pages with `source_quality: official` carry more weight than `source_quality: blog`. If `claims_unverifiable > 0`, note that some claims on the page lack external sourcing.

## Web Fetching

When you need to fetch content from a URL and direct fetching fails, use these workarounds in order:

1. **Twitter/X** — `curl -s "https://api.vxtwitter.com/{user}/status/{tweet_id}"` returns JSON with full tweet text, media, and metrics.
2. **Any web page** — `curl -s "https://r.jina.ai/{URL}"` returns clean markdown via Jina Reader. Free, no API key.
3. **YouTube** — `yt-dlp --dump-json "{URL}"` returns metadata + subtitles as JSON.
4. **Reddit** — append `.json` to any Reddit URL, or use `rdt-cli`.
5. **GitHub raw files** — `https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}`

See [[agent-web-fetching]] for the full reference.
