#!/usr/bin/env python3
"""extract-images.py — scan raw markdown for image candidates.

Finds markdown image references, applies filtering heuristics from
config.images.capture, and outputs candidate images for download.
This is step 1 of the image import pipeline (T2.1); downloading is T2.2.

Usage:
  python3 .sprue/scripts/extract-images.py path/to/raw/file.md
  python3 .sprue/scripts/extract-images.py path/to/raw/file.md --json
"""
from __future__ import annotations

import argparse
import base64
import json as jsonlib
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load as load_config

_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_PIXEL_RE = re.compile(r"1x1|2x1|1x2")


def _ext_from_url(url: str) -> str:
    """Extract lowercase extension from a URL path or data URI."""
    if url.startswith("data:"):
        # data:image/png;base64,... → png
        mime = url.split(";")[0].split("/")[-1] if "/" in url else ""
        return mime.lower()
    return Path(urlparse(url).path).suffix.lstrip(".").lower()


def _data_uri_bytes(url: str) -> int:
    """Estimate decoded size of a data URI."""
    if not url.startswith("data:"):
        return 0
    _, _, encoded = url.partition(",")
    try:
        return len(base64.b64decode(encoded, validate=True))
    except Exception:
        return len(encoded) * 3 // 4  # rough estimate


def _check_skip(url: str, cfg: dict) -> str | None:
    """Return skip reason string, or None if the image is accepted."""
    cap = cfg.get("images", {}).get("capture", {})
    tracking = cap.get("tracking_domains", [])
    allowed = [e.lower() for e in cap.get("allowed_extensions", [])]
    min_data = cap.get("min_data_uri_bytes", 1024)

    # Tracking domains (substring match)
    for td in tracking:
        if td in url:
            return f"tracking_domain ({td})"

    # Tracking pixel dimension hints
    if _PIXEL_RE.search(url):
        return "tracking_pixel"

    # Data URI size check
    if url.startswith("data:") and _data_uri_bytes(url) < min_data:
        return "data_uri_too_small"

    # Extension filter
    ext = _ext_from_url(url)
    if ext and allowed and ext not in allowed:
        return f"extension_not_allowed ({ext})"
    if not ext and not url.startswith("data:"):
        return "no_extension"

    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("file", type=Path, help="Path to a raw markdown file")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"Error: {args.file} not found or not a file", file=sys.stderr)
        return 2

    try:
        text = args.file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {args.file}: {e}", file=sys.stderr)
        return 2

    cfg = load_config()
    matches = _IMAGE_RE.findall(text)
    accepted = []

    for seq, (alt, url) in enumerate(matches, 1):
        reason = _check_skip(url, cfg)
        if args.json:
            if reason is None:
                accepted.append({"sequence": seq, "url": url, "alt_text": alt})
        else:
            line = f"seq={seq} alt='{alt}' url='{url}'"
            if reason:
                line += f" SKIPPED ({reason})"
            print(line)
            if reason is None:
                accepted.append({"sequence": seq, "url": url, "alt_text": alt})

    if args.json:
        print(jsonlib.dumps(accepted, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
