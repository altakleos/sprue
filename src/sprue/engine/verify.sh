#!/bin/bash
# verify.sh — thin wrapper; all logic lives in sprue/scripts/verify.py.
# Preserves the `bash sprue/verify.sh ...` invocation surface used across
# protocols. Arguments are forwarded unchanged.
cd "$(dirname "$0")/.." || exit 1
exec python3 sprue/scripts/verify.py "$@"
