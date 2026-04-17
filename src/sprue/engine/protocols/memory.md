# Memory Protocol (Self-Evolution)

The agent learns from corrections across sessions. Four files in `memory/`:

| File | Purpose | When to read |
|---|---|---|
| `memory/rules.yaml` | Structural rules from repeated corrections (executable, schema-validated by `.sprue/scripts/lint-rules.py`). Max `config.memory.max_rules` rules. Each has a `name` and either `command: [argv]` or `shell: <bash>`. Optional `scope: page (default) | whole`. Rules never filter by filesystem path — subset selection uses frontmatter. | **Before every operation** |
| `memory/corrections.md` | Active factual corrections the LLM must follow when writing. | **Before every write operation** |
| `memory/corrections.jsonl` | Raw correction log. Append when the human corrects you. | On correction |
| `memory/evolution-log.md` | Audit trail of rule promotions, prunings, and graduations. | During evolve |

## On Correction

When the human corrects you:

1. Fix the content.
2. Classify: `structural` (formatting, sections, process) or `factual` (wrong claim, outdated info).
3. Append to `memory/corrections.jsonl`:
   ```json
   {"date":"YYYY-MM-DD","op":"...","correction":"what was wrong","fix":"correct behavior","pattern":"name","times":1,"kind":"structural|factual"}
   ```
   If the same pattern exists, increment `times`.
4. **Structural + `times: config.memory.promotion_threshold`**: auto-promote to `memory/rules.yaml` as a new entry. Use `command: [argv]` for a pure script invocation; use `shell: <bash>` for bash pipelines that iterate `$CONTENT_PAGES`. Add `scope: whole` if the rule needs full-wiki context (skipped in `--file` mode). Rules never filter by filesystem path — to restrict to a subset of pages (e.g., only recipes), read the frontmatter `type:` field inside the shell block and `continue` on non-matches. Run `python3 .sprue/scripts/lint-rules.py` after editing.
5. **Factual** (always, at `times: 1`): append to `memory/corrections.md` with wrong claim, correct claim, `probe:` (a distinctive token from the correct claim that must appear on scoped pages), source, and `passes: 0`. The probe closes the correction loop — `check-constraints.py` flags pages where the wrong text was deleted but the correct content was never added. If no distinctive token exists, the correction is too vague; rephrase `right:` to contain one.

## On Any Wiki Write

Read `memory/corrections.md` and ensure all active corrections for the target page/topic are respected.

## Correction Retirement

After updating a page with active corrections, check if new content naturally satisfies each one. If yes, increment `passes`. After `config.memory.retirement_passes` consecutive passes, move to the `<!-- retired -->` block in `corrections.md` with date and reason. Revive if the wrong claim reappears.

## On Lint

Run `bash .sprue/verify.sh` as the first step. Report violations before other findings.
