This is a Sprue-powered knowledge base. You operate it by following protocols.

On EVERY session start, before responding to any user message:
1. Read `.sprue/engine.md` — your primary operational reference.
2. Read `instance/identity.md` — domain scope and voice.

Commands you must recognize (read the protocol before executing). Match the user's LITERAL leading verb — do NOT interpret one verb as another:
- `import <url>` → `.sprue/protocols/import.md` (fetch + save to raw/ only — STOP after capture)
- `ingest <url>` → `.sprue/protocols/import.md` then `.sprue/protocols/compile.md` (composite: fetch + compile to wiki/)
- `ingest <url> --deep` → import.md then compile.md then `.sprue/protocols/expand.md`
- `compile` → `.sprue/protocols/compile.md`
- `expand` or `expand into <topic>` → `.sprue/protocols/expand.md`
- `enhance` → `.sprue/protocols/enhance.md`
- `maintain` → `.sprue/protocols/maintain.md`
- `verify` → `.sprue/protocols/verify.md`
- `query <question>` → `.sprue/protocols/query.md`

Key directories: `raw/` (immutable sources), `wiki/` (compiled pages), `instance/` (identity + config), `.sprue/` (engine — don't edit), `memory/` (rules + corrections).

Full details: read `AGENTS.md` and `.sprue/engine.md`.
