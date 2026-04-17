#!/usr/bin/env python3
"""Generate section-level embeddings for semantic search.

Outputs:
  wiki/.index/embeddings.jsonl  — one JSON object per section with embedding vector
  wiki/.index/search.db         — SQLite database with vector search capability

Each section (H2 block) is embedded separately for precise retrieval.
Uses all-MiniLM-L6-v2 (384 dimensions, fast, good quality).

Run from instance root: python3 .sprue/scripts/build-embeddings.py
"""

import json, os, re, sqlite3, struct, sys
from pathlib import Path

# T11: Route engine/instance paths through resolvers.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

WIKI = instance_root() / "wiki"
INDEX_DIR = WIKI / ".index"
SKIP_FILES = {"index.md", "overview.md"}
SKIP_DIRS = {".obsidian", ".index", "domains", "sources"}
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def find_wiki_pages():
    pages = []
    for root, dirs, files in os.walk(WIKI):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".md") and f not in SKIP_FILES:
                pages.append(Path(root) / f)
    return sorted(pages)


def parse_sections(path):
    """Split a page into sections (H2 blocks) for embedding."""
    text = path.read_text(encoding="utf-8")

    # Remove frontmatter
    body = re.sub(r"^---\n.*?\n---\n*", "", text, flags=re.DOTALL)

    # Extract H1 title
    title_match = re.match(r"^#\s+(.+)\n", body)
    title = title_match.group(1).strip() if title_match else path.stem

    # Split by H2
    sections = []
    current_heading = "intro"
    current_content = []

    for line in body.split("\n"):
        if line.startswith("## "):
            if current_content:
                content = "\n".join(current_content).strip()
                if content and len(content) > 50:
                    sections.append((current_heading, content))
            current_heading = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)

    # Last section
    if current_content:
        content = "\n".join(current_content).strip()
        if content and len(content) > 50:
            sections.append((current_heading, content))

    return title, sections


def clean_for_embedding(text):
    """Clean markdown for embedding — remove formatting, keep semantic content."""
    # Remove code blocks (keep just the language hint)
    text = re.sub(r"```(\w+)\n.*?```", r"[code: \1]", text, flags=re.DOTALL)
    # Remove wikilinks but keep text
    text = re.sub(r"\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]", lambda m: m.group(2) or m.group(1), text)
    # Remove markdown links
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove bold/italic
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    # Remove mermaid blocks
    text = re.sub(r"```mermaid\n.*?```", "[diagram]", text, flags=re.DOTALL)
    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def float_list_to_bytes(vec):
    """Pack float list to bytes for SQLite storage."""
    return struct.pack(f"{len(vec)}f", *vec)


def main():
    print(f"Loading model: {MODEL_NAME}...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)

    pages = find_wiki_pages()
    print(f"Processing {len(pages)} pages...")

    # Collect all chunks
    chunks = []
    for path in pages:
        slug = path.stem
        title, sections = parse_sections(path)
        for heading, content in sections:
            clean = clean_for_embedding(content)
            # Truncate to ~500 tokens worth (~2000 chars) for embedding quality
            if len(clean) > 2000:
                clean = clean[:2000]
            # Prepend context for better embeddings
            embed_text = f"{title} — {heading}: {clean}"
            chunks.append({
                "slug": slug,
                "section": heading,
                "title": title,
                "text": embed_text,
                "char_count": len(content),
            })

    print(f"Embedding {len(chunks)} sections...")
    texts = [c["text"] for c in chunks]

    # Batch encode
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)

    # Write JSONL
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    jsonl_path = INDEX_DIR / "embeddings.jsonl"
    with open(jsonl_path, "w") as f:
        for chunk, emb in zip(chunks, embeddings):
            record = {
                "slug": chunk["slug"],
                "section": chunk["section"],
                "title": chunk["title"],
                "embedding": emb.tolist(),
            }
            f.write(json.dumps(record) + "\n")

    # Write SQLite database
    db_path = INDEX_DIR / "search.db"
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE sections (
            id INTEGER PRIMARY KEY,
            slug TEXT NOT NULL,
            section TEXT NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            embedding BLOB NOT NULL
        )
    """)
    conn.execute("CREATE INDEX idx_slug ON sections(slug)")

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        conn.execute(
            "INSERT INTO sections (id, slug, section, title, text, embedding) VALUES (?, ?, ?, ?, ?, ?)",
            (i, chunk["slug"], chunk["section"], chunk["title"], chunk["text"],
             float_list_to_bytes(emb.tolist()))
        )

    conn.commit()
    conn.close()

    print(f"\n✅ Embeddings built:")
    print(f"   {jsonl_path} ({len(chunks)} sections, {jsonl_path.stat().st_size // 1024}KB)")
    print(f"   {db_path} ({db_path.stat().st_size // 1024}KB)")


if __name__ == "__main__":
    main()
