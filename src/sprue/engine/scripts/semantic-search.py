#!/usr/bin/env python3
"""Semantic search over wiki sections using pre-computed embeddings.

Usage:
  python3 .sprue/scripts/semantic-search.py "your query here" [--top N] [--threshold FLOAT]

Examples:
  python3 .sprue/scripts/semantic-search.py "how to handle database connection pooling in Java Spring"
  python3 .sprue/scripts/semantic-search.py "exactly once delivery kafka" --top 5
  python3 .sprue/scripts/semantic-search.py "kubernetes pod won't start" --top 10 --threshold 0.3
"""

import json, struct, sys, argparse
import numpy as np
from pathlib import Path

# T11: Route engine/instance paths through resolvers.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

INDEX_DIR = instance_root() / "wiki" / ".index"
DB_PATH = INDEX_DIR / "search.db"
JSONL_PATH = INDEX_DIR / "embeddings.jsonl"
EMBEDDING_DIM = 384


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def bytes_to_floats(blob):
    n = len(blob) // 4
    return struct.unpack(f"{n}f", blob)


def search_sqlite(query_embedding, top_k=5, threshold=0.25):
    """Search using SQLite database."""
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute("SELECT slug, section, title, text, embedding FROM sections").fetchall()
    conn.close()

    results = []
    for slug, section, title, text, emb_blob in rows:
        emb = np.array(bytes_to_floats(emb_blob))
        score = cosine_similarity(query_embedding, emb)
        if score >= threshold:
            results.append({
                "slug": slug,
                "section": section,
                "title": title,
                "score": float(score),
            })

    results.sort(key=lambda x: -x["score"])
    return results[:top_k]


def search_jsonl(query_embedding, top_k=5, threshold=0.25):
    """Fallback: search using JSONL file."""
    results = []
    with open(JSONL_PATH) as f:
        for line in f:
            record = json.loads(line)
            emb = np.array(record["embedding"])
            score = cosine_similarity(query_embedding, emb)
            if score >= threshold:
                results.append({
                    "slug": record["slug"],
                    "section": record["section"],
                    "title": record["title"],
                    "score": float(score),
                })

    results.sort(key=lambda x: -x["score"])
    return results[:top_k]


def main():
    parser = argparse.ArgumentParser(description="Semantic search over wiki")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--top", type=int, default=10, help="Number of results")
    parser.add_argument("--threshold", type=float, default=0.25, help="Minimum similarity")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_emb = model.encode(args.query)

    if DB_PATH.exists():
        results = search_sqlite(query_emb, args.top, args.threshold)
    elif JSONL_PATH.exists():
        results = search_jsonl(query_emb, args.top, args.threshold)
    else:
        print("Error: No embedding index found. Run .sprue/scripts/build-embeddings.py first.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        if not results:
            print("No results above threshold.")
            return
        print(f"Top {len(results)} results for: \"{args.query}\"\n")
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.3f}] {r['slug']} → {r['section']}")
            print(f"     {r['title']}")


if __name__ == "__main__":
    main()
