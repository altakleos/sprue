# Knowledge Base

{{identity}}

## Quick Start

Point your LLM agent at this directory and tell it to read `AGENTS.md`.

## Structure

| Directory | Purpose |
|---|---|
| `raw/` | Source material (immutable after import) |
| `wiki/` | Compiled knowledge pages |
| `notebook/` | Your own writing (never touched by the LLM) |
| `memory/` | Agent memory — learned rules, corrections, logs |
| `.sprue/` | Engine files (managed by `sprue upgrade`) |

---
Built with [Sprue](https://github.com/altakleos/sprue).
