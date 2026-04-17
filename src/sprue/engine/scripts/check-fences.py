#!/usr/bin/env python3
"""Validate code fences in wiki pages.

Checks:
1. Bare opening fences (``` without language specifier)
2. Mismatched fence counts (odd number of ``` lines)
3. Bare language markers outside code blocks (missing ``` prefix)
4. Bare language markers inside code blocks (broken closing fence)

Run: python3 .sprue/scripts/check-fences.py
"""

import os, re, sys
from pathlib import Path

# T11: Route engine/instance paths through resolvers.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

WIKI = instance_root() / "wiki"
SKIP_DIRS = {".obsidian", ".index", "domains", "sources"}

LANGUAGES = {
    "python", "java", "rust", "go", "typescript", "javascript", "bash",
    "kotlin", "scala", "groovy", "hcl", "proto", "protobuf", "rego",
    "ruby", "swift", "cpp", "csharp", "php", "lua", "zig",
    "dockerfile", "nginx", "haproxy", "graphql", "http", "tla", "zed",
    "yaml", "json", "toml", "ini", "xml", "csv", "sql", "text",
    "mermaid", "markdown", "md", "redis", "shell", "sh", "dart",
}

violations = []

for root, dirs, files in os.walk(WIKI):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if not f.endswith(".md") or f == "overview.md":
            continue
        path = Path(root, f)
        lines = path.read_text().split("\n")

        # Check 1: mismatched fence count
        fence_count = sum(1 for l in lines if l.strip().startswith("```"))
        if fence_count % 2 != 0:
            violations.append(f"MISMATCHED FENCES ({fence_count}): {path}")

        # Check 2-4: bare openers and bare language markers
        in_code = False
        code_lang = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("```"):
                if in_code:
                    in_code = False
                    code_lang = None
                else:
                    in_code = True
                    code_lang = stripped[3:].strip()
                    # Check 2: bare opening fence (no language)
                    if not code_lang:
                        violations.append(f"{path}:{i+1}: bare opening fence (no language)")
                continue

            # Check 3-4: bare language markers
            if stripped in LANGUAGES and len(stripped) > 1:
                if in_code:
                    nxt = lines[i + 1].strip() if i < len(lines) - 1 else ""
                    if not nxt or nxt.startswith(("-", "#", "*")) or (nxt[0:1].isupper() and not nxt.startswith(("A[", "B[", "C["))):
                        violations.append(f"{path}:{i+1}: bare marker '{stripped}' inside {code_lang} block")
                else:
                    violations.append(f"{path}:{i+1}: bare language marker '{stripped}' outside code block")

if violations:
    for v in violations:
        print(v)
    sys.exit(1)
