#!/usr/bin/env python3
"""download-image.py — download a single image to raw/assets/.

Fetches, validates, deduplicates (SHA-256), and writes per the Visual
Knowledge naming convention.  Called per image by the import protocol.
"""
from __future__ import annotations

import argparse
import hashlib
import json as jsonlib
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

_CTX = ssl.create_default_context()


def _error(msg: str, url: str, as_json: bool) -> int:
    if as_json:
        print(jsonlib.dumps({"error": msg, "url": url}))
    else:
        print(f"❌ {msg}: {url}", file=sys.stderr)
    return 1


def _ext_from_url(url: str) -> str | None:
    part = url.split("?")[0].split("#")[0].rsplit("/", 1)[-1]
    return part.rsplit(".", 1)[-1].lower() if "." in part else None


def _ext_from_ct(ct: str) -> str:
    sub = ct.split("/")[-1].split(";")[0].strip().lower()
    return {"jpeg": "jpg", "svg+xml": "svg"}.get(sub, sub)


def _fetch(url: str, timeout: int, max_redir: int, max_bytes: int) -> tuple[bytes, str]:
    class _Redir(urllib.request.HTTPRedirectHandler):
        def __init__(self): self.count = 0
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            self.count += 1
            if self.count > max_redir:
                raise ValueError("too_many_redirects")
            return super().redirect_request(req, fp, code, msg, headers, newurl)
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_CTX), _Redir())
    req = urllib.request.Request(url, headers={"User-Agent": "Sprue/1.0"})
    resp = opener.open(req, timeout=timeout)
    ct = resp.headers.get("Content-Type", "")
    if not ct.startswith("image/"):
        raise ValueError("invalid_content_type")
    data = resp.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError("size_exceeded")
    return data, ct


def _fetch_retry(url: str, timeout: int, max_redir: int, max_bytes: int) -> tuple[bytes, str]:
    for attempt in range(2):
        try:
            return _fetch(url, timeout, max_redir, max_bytes)
        except urllib.error.HTTPError as e:
            if attempt == 0 and (e.code == 429 or e.code >= 500): continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == 0: continue
            raise
    raise RuntimeError("unreachable")


def main() -> int:
    ap = argparse.ArgumentParser(description="Download a single image to raw/assets/.")
    ap.add_argument("--url", required=True, help="Image URL to fetch")
    ap.add_argument("--source-slug", required=True, help="Slug from parent source")
    ap.add_argument("--sequence", required=True, type=int, help="1-indexed position")
    ap.add_argument("--alt-text", default="", help="Alt text for metadata")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()

    cfg = config.load()
    cap = cfg.get("images", {}).get("capture", {})
    timeout = cap.get("timeout_seconds", 15)
    max_bytes = cap.get("max_bytes", 10485760)
    max_redir = cap.get("max_redirects", 3)
    allowed = set(cap.get("allowed_extensions", ["png", "jpg", "jpeg", "gif", "svg", "webp"]))

    # Fetch with retry
    try:
        data, ct = _fetch_retry(args.url, timeout, max_redir, max_bytes)
    except urllib.error.HTTPError as e:
        return _error(f"http_error_{e.code}", args.url, args.json)
    except (TimeoutError, urllib.error.URLError) as e:
        return _error("timeout" if isinstance(e, TimeoutError) else "network_error",
                       args.url, args.json)
    except ValueError as e:
        return _error(str(e), args.url, args.json)

    # Extension: prefer URL, fall back to Content-Type
    ext = _ext_from_url(args.url) or _ext_from_ct(ct)
    if ext not in allowed:
        return _error("unsupported_extension", args.url, args.json)

    # Hash, filename, destination
    hash8 = hashlib.sha256(data).hexdigest()[:8]
    filename = f"{args.source_slug}-{args.sequence}-{hash8}.{ext}"
    dest = config.instance_root() / "raw" / "assets" / filename

    # Dedup: skip write if file already exists (same hash → same content)
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    result = {"local_path": f"raw/assets/{filename}", "original_url": args.url,
              "alt_text": args.alt_text, "size_bytes": len(data), "content_hash": hash8}
    if args.json:
        print(jsonlib.dumps(result, indent=2))
    else:
        s = "exists" if dest.exists() else "saved"
        print(f"📥 {s}: {result['local_path']} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
