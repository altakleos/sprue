# AGENTS.md — Sprue-Powered Knowledge Base

This is a Sprue-powered knowledge base.

## Identity

{{identity}}

## How to Operate

1. Read `.sprue/engine.md` — your primary operational reference.
2. Read `instance/identity.md` — domain scope and voice.
3. Follow the protocols in `.sprue/protocols/` for each operation.

## Core Commands

| Command | What it does |
|---|---|
| `import <url>` | Fetch a source, save to `raw/`, stop. Does NOT compile. |
| `ingest <url>` | Fetch a source, save to `raw/`, compile to `wiki/` (composite of import + compile) |
| `compile` | Process queued raw files into wiki pages |
| `query <question>` | Answer from wiki knowledge |
| `maintain` | Lint, upgrade quality, check health |

Commands are matched LITERALLY on the leading verb. `import` and `ingest` are different commands; do not interpret one as the other.

## Directory Ownership

- `.sprue/` — engine-owned. Do not edit.
- `instance/`, `wiki/`, `raw/`, `notebook/`, `memory/` — user/LLM-owned.

---
Sprue v{{sprue_version}}
