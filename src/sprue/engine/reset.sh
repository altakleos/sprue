#!/usr/bin/env bash
# sprue/reset.sh — Mechanical KB reset. Deletes content, state, and domain config by level.
# Called by the LLM via sprue/protocols/reset.md protocol. Do not run without reading that protocol first.
#
# Usage:
#   bash sprue/reset.sh --level soft|standard|hard              # dry-run (default)
#   bash sprue/reset.sh --level soft|standard|hard --confirm    # execute
#
# Levels (each is a strict superset of the previous):
#   soft     — wiki + indexes + compile/verify state. Raw preserved. "Recompile from scratch."
#   standard — + raw, memory, all state, domain config files. "Start over, same engine."
#   hard     — + identity, config overrides, enhance agents. "New domain entirely."
set -euo pipefail

LEVEL=""
CONFIRM=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --level) LEVEL="$2"; shift 2 ;;
    --confirm) CONFIRM=true; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$LEVEL" ]] || [[ ! "$LEVEL" =~ ^(soft|standard|hard)$ ]]; then
  echo "Usage: bash sprue/reset.sh --level soft|standard|hard [--confirm]"
  exit 1
fi

# ── Safety checks ────────────────────────────────────────────
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "ERROR: Not a git repo. Refusing to reset without git as safety net."
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: Dirty working tree. Commit or stash changes before reset."
  echo "       This ensures the git tag captures the true pre-reset state."
  exit 1
fi

# ── Count what exists ────────────────────────────────────────
count_files() { find "$1" -type f 2>/dev/null | wc -l | tr -d ' '; }
count_or_zero() { if [[ -d "$1" ]]; then count_files "$1"; else echo "0"; fi; }

WIKI_PAGES=$(find wiki -name '*.md' -type f 2>/dev/null | wc -l | tr -d ' ')
WIKI_INDEX=$(count_or_zero "wiki/.index")
WIKI_OBSIDIAN=$(count_or_zero "wiki/.obsidian")
RAW_FILES=$(count_or_zero "raw")
MEMORY_FILES=$(count_or_zero "memory")
ARCHIVE_FILES=$(count_or_zero "instance/archive")

STATE_FILES=0
[[ -f instance/state/compilations.yaml ]] && ((STATE_FILES++)) || true
[[ -f instance/state/verifications.yaml ]] && ((STATE_FILES++)) || true
if [[ "$LEVEL" != "soft" ]]; then
  [[ -f instance/state/imports.yaml ]] && ((STATE_FILES++)) || true
  [[ -f instance/state/expansions.yaml ]] && ((STATE_FILES++)) || true
fi

# ── Dry-run inventory ────────────────────────────────────────
echo ""
echo "═══ KB Reset — level: $LEVEL ═══"
echo ""
echo "Will DELETE:"
echo "  wiki pages:        $WIKI_PAGES files"
echo "  wiki/.index:       $WIKI_INDEX files"
echo "  wiki/.obsidian:    $WIKI_OBSIDIAN files"
echo "  wiki subdirs:      (all empty dirs removed)"
echo "  state ledgers:     $STATE_FILES files"

if [[ "$LEVEL" != "soft" ]]; then
  echo "  raw/:              $RAW_FILES files"
  echo "  memory/:           $MEMORY_FILES files"
  echo "  instance/archive/:      $ARCHIVE_FILES files"
  echo ""
  echo "Will CLEAR (truncate to empty):"
  echo "  instance/entity-types.yaml"
  echo "  instance/sources.yaml"
  echo "  instance/backfill-backlog.md"
  echo "  instance/scaling-plan.md"
  echo "  instance/config.yaml → overrides section"
fi

if [[ "$LEVEL" == "hard" ]]; then
  echo "  instance/identity.md"
  echo "  instance/config.yaml → enhance agents section"
fi

echo ""
echo "Will PRESERVE:"
echo "  sprue/engine.md, protocols, scripts, prompts, pipeline"
echo "  sprue/defaults.yaml"
echo "  instance/config.yaml (structure + tuning parameters)"
echo "  notebook/"
echo "  inbox/ (user drop zone, not version-controlled)"
echo "  .git, .kiro/, AGENTS.md, README.md"
if [[ "$LEVEL" == "soft" ]]; then
  echo "  raw/ (all source material)"
  echo "  memory/ (learned rules, corrections)"
  echo "  instance/state/imports.yaml, expansions.yaml"
fi
echo ""

if [[ "$CONFIRM" != true ]]; then
  echo "DRY RUN — no changes made."
  echo "To execute: bash sprue/reset.sh --level $LEVEL --confirm"
  exit 0
fi

# ── Create git tag ───────────────────────────────────────────
TAG="pre-reset/$(date -u +%Y-%m-%dT%H-%M-%S)"
git tag "$TAG"
echo "✅ Created git tag: $TAG"
echo "   To recover: git checkout $TAG"
echo ""

# ── Execute: Soft ────────────────────────────────────────────
# Wiki content and indexes
find wiki -type f -name '*.md' -delete 2>/dev/null || true
rm -rf wiki/.index wiki/.obsidian
# Remove empty wiki subdirs (but keep wiki/ itself)
find wiki -mindepth 1 -type d -empty -delete 2>/dev/null || true

# Compile and verify state
rm -f instance/state/compilations.yaml instance/state/verifications.yaml

echo "  ✓ wiki/ cleared"
echo "  ✓ compile/verify state cleared"

# ── Execute: Standard (superset of soft) ─────────────────────
if [[ "$LEVEL" == "standard" || "$LEVEL" == "hard" ]]; then
  # Raw sources
  find raw -mindepth 1 -delete 2>/dev/null || true

  # Remaining state ledgers
  rm -f instance/state/imports.yaml instance/state/expansions.yaml

  # Memory
  find memory -type f -delete 2>/dev/null || true

  # Archive
  find instance/archive -type f -delete 2>/dev/null || true

  # Clear domain-specific files (truncate, don't delete)
  > instance/entity-types.yaml
  > instance/sources.yaml
  > instance/backfill-backlog.md
  > instance/scaling-plan.md

  # Clear config.yaml overrides section
  # Replace everything between the overrides: line and the next section marker
  sed -i.bak '/^overrides:/,/^# ── /{
    /^overrides:/c\
overrides:\
  # Add domain-specific term mappings here after identity is set.\
  # Example: redis: valkey (fork preference), ai: llm (domain merge)
    /^# ── /!d
  }' instance/config.yaml
  rm -f instance/config.yaml.bak

  echo "  ✓ raw/ cleared"
  echo "  ✓ all state ledgers cleared"
  echo "  ✓ memory/ cleared"
  echo "  ✓ domain config files cleared"
  echo "  ✓ config.yaml overrides reset"
fi

# ── Execute: Hard (superset of standard) ─────────────────────
if [[ "$LEVEL" == "hard" ]]; then
  # Clear identity
  > instance/identity.md

  # Clear enhance agents — replace with placeholder
  sed -i.bak '/^enhance:/,/^# ── /{
    /^enhance:/c\
enhance:\
  agents: []\
  # Define domain-specific enhance agents after identity is set.
    /^# ── /!d
  }' instance/config.yaml
  rm -f instance/config.yaml.bak

  echo "  ✓ identity cleared"
  echo "  ✓ enhance agents cleared"
fi

echo ""
echo "═══ Reset complete ═══"
echo ""
echo "Recovery:  git checkout $TAG"
echo "Next:      set identity in instance/identity.md, then start importing"
