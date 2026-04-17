#!/usr/bin/env python3
"""check-package-contents.py — assert built wheel contains no instance content.

Enforces spec invariant: "Engine contains no instance content."
Invoked by CI (Phase E T29) as a build gate.

Usage:
  python3 check-package-contents.py [WHEEL_PATH]
  python3 check-package-contents.py dist/sprue-0.1.0-py3-none-any.whl
  python3 check-package-contents.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

FORBIDDEN_SEGMENTS = {
    "instance", "wiki", "raw", "memory", "notebook",
    "inbox", "state", "docs", ".yolo-sisyphus",
}
FORBIDDEN_ROOT_FILES = {"AGENTS.md"}  # top-level only — templates/AGENTS.md is OK


def find_latest_wheel() -> Path | None:
    dist = Path("dist")
    if not dist.is_dir():
        return None
    wheels = sorted(dist.glob("*.whl"), key=lambda p: p.stat().st_mtime)
    return wheels[-1] if wheels else None


def check_wheel(wheel_path: Path) -> list[str]:
    violations = []
    with zipfile.ZipFile(wheel_path) as wf:
        for name in wf.namelist():
            parts = name.split("/")
            # Root-level file check
            if len(parts) == 1 and parts[0] in FORBIDDEN_ROOT_FILES:
                violations.append(name)
                continue
            # Path segment check (skip wheel metadata dirs like *.dist-info)
            for seg in parts:
                if seg in FORBIDDEN_SEGMENTS:
                    violations.append(name)
                    break
    return violations


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("wheel", nargs="?", help="Path to wheel file")
    p.add_argument("--json", action="store_true", help="Machine-readable output")
    args = p.parse_args()

    wheel = Path(args.wheel) if args.wheel else find_latest_wheel()
    if wheel is None or not wheel.exists():
        print(f"Error: wheel not found ({wheel})", file=sys.stderr)
        return 2

    violations = check_wheel(wheel)
    if args.json:
        print(json.dumps({"wheel": str(wheel), "violations": violations}, indent=2))
    else:
        with zipfile.ZipFile(wheel) as wf:
            n = len(wf.namelist())
        if violations:
            print(
                f"❌ Package contents: {len(violations)} forbidden path(s) in {wheel.name}:",
                file=sys.stderr,
            )
            for v in violations:
                print(f"  {v}", file=sys.stderr)
        else:
            print(f"✅ Package contents: OK ({n} files, no instance paths) in {wheel.name}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
