# Reset

Return the KB to a blank slate. Three levels, each a strict superset of the previous.

**Trigger:** "reset", "start over", "wipe", "clean slate", "new domain"

## Levels

| Level | What it does | Use when |
|---|---|---|
| `soft` | Wipe wiki + indexes + compile/verify state. Raw and memory preserved. | Recompile everything from scratch |
| `standard` | + raw, memory, all state, domain config (entity-types, sources, backlog, scaling plan, config overrides) | Start over with the same engine |
| `hard` | + identity, enhance agents | Repurpose the engine for a completely different domain |

**Always preserved:** engine protocols, scripts, prompts, pipeline config, defaults.yaml, config.yaml structure/tuning, notebook/, .git.

## Protocol

### 1. Determine level

Map user intent to level. If ambiguous, ask.

- "recompile" / "rebuild wiki" → `soft`
- "start over" / "wipe everything" → `standard`
- "new domain" / "different KB" / "repurpose" → `hard`

### 2. Show inventory (dry-run)

```bash
bash sprue/reset.sh --level <level>
```

Present the output to the user. This shows exactly what will be deleted, cleared, and preserved.

### 3. Confirm

Ask the user to type the level name to confirm. Do NOT accept "yes" or "y" — require the exact word (`soft`, `standard`, or `hard`). This prevents accidental execution.

> Type **soft**, **standard**, or **hard** to confirm. This is irreversible beyond git history.

### 4. Execute

```bash
bash sprue/reset.sh --level <level> --confirm
```

The script creates a git tag `pre-reset/<timestamp>` before deleting anything. Report the tag name to the user.

### 5. Post-reset

- For `hard` reset: prompt the user to write a new identity in `instance/identity.md`.
- For all levels: suggest running `status` to confirm clean state.
- Remind: `git checkout <tag>` recovers the pre-reset state.

## Recovery

```bash
# See all pre-reset snapshots
git tag -l 'pre-reset/*'

# Restore to pre-reset state
git checkout <tag>

# Or just inspect what was deleted
git diff <tag>..HEAD --stat
```

## Constraints

- **Never reset without explicit user confirmation.** Always run dry-run first.
- **Never initiate a reset autonomously.** The user must ask for it.
- **Never delete notebook/.** Sacred across all levels.
- **Dirty working tree blocks reset.** Uncommitted changes must be committed or stashed first, so the git tag captures the true state.
