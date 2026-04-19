# Import Protocol

*Requires `AGENTS.md` and `.sprue/engine.md` in context (loaded via bootstrap).*

**Trigger:** "import", "save this", "capture", "bookmark", a bare URL, or a file path.

## Role

Fast, intelligent capture. Fetch content, save the original untouched to `raw/`, record classification metadata in `imports.yaml`, and stop. No compilation, no wiki pages, no linking.

IMPORT determines **content type** from the source format (trivial, no LLM needed) and extracts the **title**. Facet classification (see `.sprue/defaults.yaml` → `facets:`) is COMPILE's job — they require understanding the content.

---

## Steps

### 1. Dedup check

Read `instance/state/imports.yaml`. Check if the source URL already exists.

- **Exact URL match:** Report `📥 Already imported: <raw-path> (<age>). Re-import? [y/N]`
- **No match:** Proceed.

### 2. Fetch

Retrieve the content. Use the appropriate method per source type:

| Source type | Detection | Fetch method |
|---|---|---|
| Web page / article | HTTP URL, HTML content | `curl -s "https://r.jina.ai/<URL>"` for clean markdown |
| PDF | `.pdf` extension or `Content-Type` | Fetch binary, extract text (pdftotext or LLM) |
| Tweet / X thread | `x.com` or `twitter.com` URL | `curl -s "https://api.vxtwitter.com/<user>/status/<id>"` |
| YouTube | `youtube.com` or `youtu.be` URL | `yt-dlp --dump-json "<URL>"` for transcript |
| GitHub repo | `github.com` URL | Fetch README + key files via raw.githubusercontent.com |
| Local file | File path, no URL | Read directly from disk. If source is in `inbox/`, delete the original after successful import (move semantics). |
| Pasted content | No URL, inline text | Use as-is |

If fetch fails: `❌ Fetch failed: <reason>. URL saved to inbox/failed-imports.md for retry.`

### 3. Analyze & classify

Determine the following:

**Content type** (from source format — no LLM needed):

| Source | Content type |
|---|---|
| Blog post, web article, docs page | `article` |
| Academic paper, whitepaper, arxiv | `paper` |
| Tweet thread, forum discussion | `thread` |
| YouTube video, conference talk | `video` |
| Code snippet, gist, config example | `snippet` |
| GitHub README, project docs | `readme` |
| Tutorial, how-to guide | `tutorial` |

**Title** — extracted from content heading, metadata, or URL slug. No deep reading needed.

Content type and title are all IMPORT classifies. Facet classification (see `.sprue/defaults.yaml` → `facets:`) is COMPILE's job — they require understanding the content, which IMPORT doesn't do.

### 4. Save to raw/

Save the original content **untouched** to `raw/`. No headers, no frontmatter, no modifications. A PDF stays a PDF. Fetched markdown stays as fetched. The raw file is a faithful archive.

**No injected metadata.** Do not prepend YAML frontmatter, source headers, or any metadata to the raw file. If the fetched content already contains YAML frontmatter from the source, preserve it as-is (it's part of the original). But never *add* frontmatter that wasn't in the source. All import metadata (source URL, title, content_type, hash) is recorded in `imports.yaml` only.

#### Directory structure

Organized by **content type** only. Domain is NOT encoded in the path (it's a classification opinion that may be wrong, and raw/ is immutable — a misclassified file would be stuck in the wrong folder forever).

```
raw/
├── articles/    # blog posts, web articles, docs pages
├── papers/      # academic papers, whitepapers, technical reports
├── threads/     # tweet threads, forum discussions
├── snippets/    # code snippets, config examples, gists
├── videos/      # transcripts from YouTube, conference talks
├── tutorials/   # how-to guides, walkthroughs
└── assets/      # binary files (images, original PDFs, diagrams)
```

#### Filename convention

`raw/<content-type>s/<slug>-<YYYY-MM-DD>-<hash8>.<ext>`

- `slug` — kebab-case, derived from title, max 50 chars
- `YYYY-MM-DD` — capture date
- `hash8` — first **8 characters** of SHA-256 of the file content (16^8 ≈ 4.3 billion values — collision probability at 1000 files is effectively zero)
- `ext` — original file extension (`.md` for text, `.pdf` for PDFs, `.jpeg` for images, etc.)

Examples:
- `raw/articles/jepsen-kafka-3-2026-04-10-a3f8c2d1.md`
- `raw/papers/raft-revisited-2026-04-10-c4d901e7.pdf`
- `raw/threads/react-server-components-2026-04-10-7b2e1fab.md`
- `raw/assets/llm-concepts-infographic-2026-04-10-1a2b3c4d.jpeg`

#### Collision handling

Before writing, check if the target path already exists. If it does (extremely unlikely with 8-char hash), append a counter: `-2`, `-3`, etc.

Create subdirectories as needed.

### 5. Capture images

For markdown sources, capture embedded images as immutable snapshots in `raw/assets/`. Images are first-class knowledge sources — they are captured during import with the same snapshot philosophy applied to text.

**Gate check:** If `config.images.enabled` is false OR `config.images.capture.enabled` is false OR the source is not `text/markdown` (e.g., PDF, video), skip to Step 6.

1. Run `extract-images.py <raw-file>` — outputs a JSON list of candidate images (URLs, alt text, sequence numbers) after applying filtering heuristics.
2. If candidates exceed `config.images.capture.max_per_source`, keep the first N by document order. Log: `⚠️ capped image list to <N> (source contains <M>)`.
3. For each candidate, invoke:
   ```
   download-image.py --url <url> --source-slug <slug> --sequence <n> --alt-text <text> --json
   ```
   Collect the JSON result (local path, size, content hash). A failed download emits a warning but does **not** fail the import — continue with the next candidate.
4. Rewrite the raw markdown:
   - For each successfully downloaded image, replace the remote URL with the local path (`raw/assets/<filename>`). Preserve the original URL in an HTML comment: `<!-- original: https://... -->`.
   - Failed downloads leave the remote URL unchanged (no rewrite).
5. Append an `assets` list to this source's `imports.yaml` entry (written in Step 6):
   ```yaml
   assets:
     - local_path: raw/assets/kafka-guide-1-7f2a3b4c.png
       original_url: https://example.com/arch.png
       alt_text: Architecture overview
       size_bytes: 245760
       content_hash: 'sha256:7f2a3b4c'
   ```
6. Emit summary: `✨ captured N/M images (K skipped)` — N successful, M candidates, K skipped (over cap or failed).

### 6. Update state

All classification metadata goes in `instance/state/imports.yaml`. This is the single source of truth for what IMPORT observed about the content.

Append to `instance/state/imports.yaml`:
```yaml
- source: "https://jepsen.io/analyses/kafka-3.0"
  raw: raw/articles/jepsen-kafka-3-2026-04-10-a3f8c2d1.md
  title: "Jepsen: Kafka 3.0"
  content_type: article
  content_hash: sha256:a3f8c2d1
  imported_at: "2026-04-10T19:30:00Z"
```

`instance/state/imports.yaml` is **append-only**. It records what IMPORT observed: source, location, format, and timestamp. Domain, topics, and aspects classification happen later in COMPILE.

Append to `memory/log.jsonl`:
```json
{"ts":"<ISO8601>","op":"import","title":"<title>","created":1,"modified":0,"deleted":0,"summary":"Imported <content-type> from <source> → <raw-path>"}
```

### 7. Feedback

One line. Don't interrupt the user's flow:

```
📥 "<Title>" (<content-type>, <words>w) → <raw-path>
```

For errors:
```
❌ Fetch failed: 404 Not Found. URL saved to inbox/failed-imports.md for retry.
```

For duplicates (after user confirms re-import):
```
📥 Re-imported: "<Title>" → <raw-path> (previous version kept)
```

---

## Batch mode

Multiple URLs in one message:

```
> import <url1> <url2> <url3>
```

Process each independently. One confirmation line per URL. Failures don't block other imports.

**Batch dedup:** Before processing the batch, load all existing source URLs from `instance/state/imports.yaml` into a seen-set. Before each item, check the seen-set — skip with `⏭️ Skipped (duplicate in batch): <url>` if already seen. Add each processed URL to the seen-set immediately after writing to `instance/state/imports.yaml`.

```
📥 "Jepsen: Kafka 3.0" (article, 4200w) → raw/articles/jepsen-kafka-3-2026-04-10-a3f8c2d1.md
📥 "Cell Architectures" (article, 2800w) → raw/articles/cell-architectures-2026-04-10-7b2e1fab.md
❌ https://broken.example.com — 404 Not Found
```

---

## Shortcut: `import --compile`

When the user says `import --compile <url>` or `ingest <url>`:

1. Run the full IMPORT protocol above
2. Immediately run COMPILE (read `.sprue/protocols/compile.md`) on just that one raw file
3. This is sugar for the common "save and process now" workflow

---

## What IMPORT does NOT do

- ❌ Create wiki pages
- ❌ Generate markdown summaries or compilations
- ❌ Add wiki frontmatter or section structure
- ❌ Create wikilinks
- ❌ Run verify.sh
- ❌ Analyze gaps or propose research
- ❌ Modify any existing files (except appending to state/log)
- ❌ Inject metadata into raw files

IMPORT saves originals untouched and records format metadata in `instance/state/imports.yaml`. Facet classification and wiki page generation happen in COMPILE.
