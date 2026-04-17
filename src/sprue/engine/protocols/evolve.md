# Evolve Operation

Triggered when the human says "evolve", "review learnings", "what have you learned", or similar.

## Steps

1. Read `memory/corrections.jsonl`. Find patterns (same correction 2+ times).
2. Promote to `memory/rules.yaml` as a new entry (use `command: [argv]` for script invocations or `shell: <bash>` for pipelines). Validate with `python3 sprue/scripts/lint-rules.py`.
3. Prune rules that passed verification for 5+ lint cycles.
4. Propose graduating stable rules to AGENTS.md.
5. Log all decisions to `memory/evolution-log.md`.

**Never re-propose previously rejected rules.**
