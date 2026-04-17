#!/bin/bash
# verify.sh — thin wrapper; all logic lives in .sprue/scripts/verify.py.
# Preserves the `bash .sprue/verify.sh ...` invocation surface used across
# protocols. Arguments are forwarded unchanged.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/scripts/verify.py" "$@"
