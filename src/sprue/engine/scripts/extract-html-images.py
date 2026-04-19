#!/usr/bin/env python3
"""extract-html-images.py — list image URLs from a web page's HTML.

Fallback for import Step 5 when Jina Reader is unavailable and the
primary fetch (e.g., web_fetch) returns prose without ![alt](src)
references. Fetches the page HTML directly via urllib, parses out
<img> tags, and emits them as markdown image lines the import can
append to the raw file so Step 5 sees something to capture.

Keeps the raw file valid markdown: each emitted line is a standalone
markdown image reference, suitable for extract-images.py to consume.

Usage:
  python3 .sprue/scripts/extract-html-images.py <URL>          # human
  python3 .sprue/scripts/extract-html-images.py <URL> --markdown  # `![alt](src)` per line
  python3 .sprue/scripts/extract-html-images.py <URL> --json      # structured
"""
from __future__ import annotations

import argparse
import json as jsonlib
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

_USER_AGENT = "Sprue/1.0 (image extractor)"
_TIMEOUT = 15


class _ImgParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.images: list[dict] = []
        self._in_script = 0
        self._in_style = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "noscript"):
            self._in_script += 1
            return
        if tag == "style":
            self._in_style += 1
            return
        if tag != "img" or self._in_script or self._in_style:
            return
        attrs_dict = {k: (v or "") for k, v in attrs}
        # Prefer srcset's largest candidate if present, else src, else data-src.
        src = attrs_dict.get("src") or attrs_dict.get("data-src") or ""
        srcset = attrs_dict.get("srcset", "")
        if srcset:
            candidates = [p.strip().split(" ")[0] for p in srcset.split(",") if p.strip()]
            if candidates:
                src = candidates[-1]  # last is typically largest
        if not src or src.startswith("data:"):
            return
        self.images.append({"src": src, "alt": attrs_dict.get("alt", "")})

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "noscript"):
            self._in_script = max(0, self._in_script - 1)
        elif tag == "style":
            self._in_style = max(0, self._in_style - 1)


def _fetch(url: str) -> str:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=_TIMEOUT, context=ctx) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _resolve(base: str, src: str) -> str:
    return urllib.parse.urljoin(base, src)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("url", help="Web page URL to extract images from")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--markdown", action="store_true", help="Markdown ![alt](src) per line")
    args = parser.parse_args()

    try:
        html = _fetch(args.url)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        msg = {"error": "fetch_failed", "url": args.url, "detail": str(exc)}
        print(jsonlib.dumps(msg) if args.json else f"fetch failed: {exc}", file=sys.stderr)
        return 1

    parser_obj = _ImgParser()
    try:
        parser_obj.feed(html)
    except Exception as exc:
        msg = {"error": "parse_failed", "url": args.url, "detail": str(exc)}
        print(jsonlib.dumps(msg) if args.json else f"parse failed: {exc}", file=sys.stderr)
        return 1

    images = []
    seen = set()
    for img in parser_obj.images:
        abs_url = _resolve(args.url, img["src"])
        if abs_url in seen:
            continue
        seen.add(abs_url)
        images.append({"src": abs_url, "alt": img["alt"]})

    if args.json:
        print(jsonlib.dumps({"images": images}, indent=2))
    elif args.markdown:
        for img in images:
            alt = img["alt"].replace("]", " ").replace("[", " ").strip() or "Image"
            print(f"![{alt}]({img['src']})")
    else:
        for img in images:
            print(f"{img['src']}\t{img['alt']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
