#!/usr/bin/env python3
"""Statically lint memory/rules.yaml for schema validity.

Does NOT execute rules; only validates shape. Invoked by verify.sh via a
self-referential rule so invalid rule edits surface before they would run.

Usage:
  python3 sprue/scripts/lint-rules.py
  python3 sprue/scripts/lint-rules.py --quiet   # errors only (if invoked from verify.sh)

Exit: 0 on clean, 1 on any schema violation.
"""

import sys
from pathlib import Path

import yaml

RULES_FILE = Path("memory/rules.yaml")
VALID_SCOPES_LITERAL = {"page", "whole"}


def lint() -> list[str]:
    errors: list[str] = []

    if not RULES_FILE.exists():
        errors.append(f"Rules file not found: {RULES_FILE}")
        return errors

    try:
        doc = yaml.safe_load(RULES_FILE.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        errors.append(f"YAML parse error: {e}")
        return errors

    if not isinstance(doc, list):
        errors.append(f"Root of {RULES_FILE} must be a list, got {type(doc).__name__}")
        return errors

    names_seen: dict[str, int] = {}
    for i, rule in enumerate(doc):
        if not isinstance(rule, dict):
            errors.append(f"Rule #{i}: must be a mapping")
            continue

        name = rule.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"Rule #{i}: missing or empty 'name'")
            continue

        if name in names_seen:
            errors.append(
                f"Rule '{name}': duplicate name (first at index {names_seen[name]})"
            )
        else:
            names_seen[name] = i

        has_command = "command" in rule
        has_shell = "shell" in rule
        if not has_command and not has_shell:
            errors.append(
                f"Rule '{name}': missing both 'command' and 'shell' — exactly one required"
            )
        elif has_command and has_shell:
            errors.append(
                f"Rule '{name}': has both 'command' and 'shell' — exactly one required"
            )

        if has_command:
            cmd = rule["command"]
            if (
                not isinstance(cmd, list)
                or not cmd
                or not all(isinstance(a, str) and a for a in cmd)
            ):
                errors.append(
                    f"Rule '{name}': 'command' must be a non-empty list of non-empty strings"
                )

        if has_shell:
            sh = rule["shell"]
            if not isinstance(sh, str) or not sh.strip():
                errors.append(f"Rule '{name}': 'shell' must be a non-empty string")

        scope = rule.get("scope", "page")
        if scope not in VALID_SCOPES_LITERAL:
            errors.append(
                f"Rule '{name}': invalid scope {scope!r} — must be 'page' or 'whole'"
            )

        source = rule.get("source")
        if source is not None and not isinstance(source, str):
            errors.append(f"Rule '{name}': 'source' must be a string if present")

        # Unknown fields warning (not fatal) — omitted to keep the linter strict-quiet

    return errors


def main() -> int:
    quiet = "--quiet" in sys.argv
    errors = lint()
    if errors:
        for e in errors:
            print(e)
        return 1
    if not quiet:
        # Count rules for the success summary
        try:
            count = len(yaml.safe_load(RULES_FILE.read_text(encoding="utf-8")) or [])
        except Exception:
            count = 0
        print(f"✅ {count} rules valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
