#!/usr/bin/env python3
"""Placement signals — advisory reports of directory-placement health.

Emits four observations about wiki directory layout. Never fails the build;
always exits 0. Consumed by the LLM during maintain and enhance protocol
runs (not by memory/rules.yaml).

  S-1  Directory coherence   — Shannon entropy over primary-domain distribution
                                per directory; high entropy = dumping-ground smell.
  S-2  Placement outliers    — pages whose wikilink neighbors (inbound + outbound)
                                live mostly in a different directory.
  S-3  Size-band alerts      — directories above navigable_max (split candidates)
                                or below sparse_min (absorb candidates).
  S-4  Subdirectory emergence — for split-candidate dirs, proposes emergent subdir
                                names from shared secondary-domain clusters.

Source of truth: wiki/.index/manifest.yaml (dir, domain[], links_to[] per slug).
No filesystem walks, no markdown reparsing. Inbound edges computed by inverting
links_to across the manifest in one pass.

Output: human-readable tables by default; --json for LLM consumption (mirrors
the prioritize.py convention).

Usage:
  python3 .sprue/scripts/placement-signals.py          # human report
  python3 .sprue/scripts/placement-signals.py --json   # machine-readable

Exit: 0 always.
"""

import argparse
import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

# T11: Route engine/instance paths through resolvers.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

ROOT = instance_root()
WIKI = instance_root() / "wiki"
MANIFEST = instance_root() / "wiki" / ".index" / "manifest.yaml"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load as load_config


# ── Defaults (overridable via instance/config.yaml → placement:) ──

DEFAULTS = {
    "navigable_max": 50,
    "sparse_min": 3,
    "subdir_cluster_min": 5,
    "outlier_fraction_threshold": 0.7,
    "outlier_neighbor_min": 3,
}
SMALL_DIR_MIN = 3  # directories below this are skipped in S-1 (entropy meaningless)


# ── Config + manifest loading ──

def _load_placement_config() -> tuple[dict, set[str]]:
    cfg = load_config()
    p = cfg.get("placement", {}) or {}
    thresholds = {k: p.get(k, v) for k, v in DEFAULTS.items()}
    allowlist = set(p.get("allowlist", []) or [])
    return thresholds, allowlist


def load_manifest() -> dict:
    m = yaml.safe_load(MANIFEST.read_text()) or {}
    m.pop("_meta", None)
    return m


def check_manifest_freshness() -> str | None:
    """Warn if manifest is older than any content wiki page (stale index).

    Skips build-index.py outputs (overview.md, wiki/domains/*.md) which are
    written *after* manifest.yaml in the same run and would always appear newer.
    """
    if not MANIFEST.exists():
        return f"manifest not found at {MANIFEST} — run .sprue/scripts/build-index.py"
    m_mtime = MANIFEST.stat().st_mtime
    for p in WIKI.rglob("*.md"):
        rel = p.relative_to(WIKI).as_posix()
        if rel == "overview.md" or rel.startswith("domains/") or "/.index/" in str(p):
            continue
        if p.stat().st_mtime > m_mtime:
            return (f"manifest.yaml is older than at least one wiki page ({p.relative_to(ROOT)}). "
                    "Run .sprue/scripts/build-index.py before interpreting signals.")
    return None


def display_dir(d: str) -> str:
    """Render '' (root) as 'wiki/' for humans; everything else as 'wiki/<d>'."""
    return "wiki/" if d == "" else f"wiki/{d}"


# ── Shared graph data ──

def build_graph(manifest: dict) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Return (outbound, inbound) adjacency dicts keyed by slug.

    Outbound = manifest[slug].links_to (already computed by build-index.py).
    Inbound = inverted in one pass; neighbors filtered to slugs present in manifest.
    """
    outbound = {slug: list(entry.get("links_to") or []) for slug, entry in manifest.items()}
    inbound: dict[str, list[str]] = defaultdict(list)
    slugs = set(manifest)
    for src, targets in outbound.items():
        for tgt in targets:
            if tgt in slugs:
                inbound[tgt].append(src)
    return outbound, dict(inbound)


def pages_by_dir(manifest: dict, allowlist: set[str]) -> dict[str, list[str]]:
    """Group slugs by directory, excluding allowlisted directories."""
    by_dir: dict[str, list[str]] = defaultdict(list)
    for slug, entry in manifest.items():
        d = entry.get("dir", "")
        full = display_dir(d)
        if full in allowlist:
            continue
        by_dir[d].append(slug)
    return dict(by_dir)


# ── S-1: Directory coherence ──

def s1_coherence(manifest: dict, by_dir: dict[str, list[str]]) -> list[dict]:
    """Compute normalized Shannon entropy of primary-domain distribution per dir."""
    out = []
    for d, slugs in by_dir.items():
        if len(slugs) < SMALL_DIR_MIN:
            continue
        primaries = []
        no_domain = 0
        for s in slugs:
            doms = manifest[s].get("domain") or []
            if doms:
                primaries.append(doms[0])
            else:
                no_domain += 1
        if not primaries:
            continue
        counts = Counter(primaries)
        total = sum(counts.values())
        H = -sum((c / total) * math.log2(c / total) for c in counts.values())
        # Normalize by max possible entropy: log2(|distinct values|)
        max_H = math.log2(len(counts)) if len(counts) > 1 else 1.0
        H_norm = H / max_H if max_H > 0 else 0.0
        dominant = counts.most_common(3)
        out.append({
            "dir": display_dir(d),
            "page_count": len(slugs),
            "entropy_normalized": round(H_norm, 3),
            "dominant_domains": [[name, count] for name, count in dominant],
            "pages_without_domain": no_domain,
        })
    out.sort(key=lambda x: (-x["entropy_normalized"], -x["page_count"]))
    return out


# ── S-2: Placement outliers ──

def s2_outliers(manifest: dict, outbound: dict[str, list[str]], inbound: dict[str, list[str]],
                allowlist: set[str], thresholds: dict) -> list[dict]:
    """Flag pages whose neighbor graph lives majority-elsewhere."""
    min_neighbors = thresholds["outlier_neighbor_min"]
    min_fraction = thresholds["outlier_fraction_threshold"]
    out = []
    for slug, entry in manifest.items():
        current = entry.get("dir", "")
        if display_dir(current) in allowlist:
            continue
        neighbors = set(outbound.get(slug, [])) | set(inbound.get(slug, []))
        neighbors.discard(slug)
        if len(neighbors) < min_neighbors:
            continue
        # Map neighbors to their dirs (skip neighbors that slipped out of manifest)
        dir_counts: Counter = Counter()
        for n in neighbors:
            n_entry = manifest.get(n)
            if n_entry is None:
                continue
            dir_counts[n_entry.get("dir", "")] += 1
        if not dir_counts:
            continue
        total = sum(dir_counts.values())
        elsewhere = total - dir_counts.get(current, 0)
        fraction = elsewhere / total
        if fraction < min_fraction:
            continue
        suggested, _ = dir_counts.most_common(1)[0]
        if suggested == current:
            # Mode is own dir — not a real outlier (should not happen given fraction>=min, but defend)
            continue
        top_dirs = [[display_dir(d), c] for d, c in dir_counts.most_common(5)]
        out.append({
            "slug": slug,
            "current_dir": display_dir(current),
            "suggested_dir": display_dir(suggested),
            "neighbor_count": total,
            "fraction_elsewhere": round(fraction, 3),
            "top_neighbor_dirs": top_dirs,
        })
    out.sort(key=lambda x: (-x["fraction_elsewhere"], -x["neighbor_count"]))
    return out


# ── S-3: Size bands ──

def s3_size_bands(by_dir: dict[str, list[str]], thresholds: dict) -> dict:
    nav_max = thresholds["navigable_max"]
    sparse = thresholds["sparse_min"]
    splits = [{"dir": display_dir(d), "count": len(slugs), "threshold": nav_max}
              for d, slugs in by_dir.items() if len(slugs) > nav_max]
    absorbs = [{"dir": display_dir(d), "count": len(slugs), "threshold": sparse}
               for d, slugs in by_dir.items() if len(slugs) < sparse]
    splits.sort(key=lambda x: -x["count"])
    absorbs.sort(key=lambda x: x["count"])
    return {"split_candidates": splits, "absorb_candidates": absorbs}


# ── S-4: Subdirectory emergence ──

def s4_subdir_proposals(manifest: dict, by_dir: dict[str, list[str]], split_candidates: list[dict],
                        thresholds: dict) -> list[dict]:
    cluster_min = thresholds["subdir_cluster_min"]
    out = []
    # Map split-candidate display_dirs back to the raw dir key
    display_to_raw = {display_dir(d): d for d in by_dir}
    for cand in split_candidates:
        raw = display_to_raw.get(cand["dir"])
        if raw is None:
            continue
        # Collect secondary-domain values per page
        secondary_counts: Counter = Counter()
        secondary_pages: dict[str, list[str]] = defaultdict(list)
        for slug in by_dir[raw]:
            doms = manifest[slug].get("domain") or []
            for sec in doms[1:]:  # skip primary
                secondary_counts[sec] += 1
                secondary_pages[sec].append(slug)
        # Propose any secondary value meeting the cluster threshold
        for sec, count in secondary_counts.most_common():
            if count < cluster_min:
                break
            out.append({
                "parent": cand["dir"],
                "proposed_name": sec,
                "cluster_size": count,
                "shared_secondary_domain": sec,
                "sample_pages": sorted(secondary_pages[sec])[:5],
            })
    return out


# ── Summary ──

def build_summary(coh: list, outliers: list, size_bands: dict, subdirs: list, dir_count: int) -> dict:
    high_entropy = sum(1 for e in coh if e["entropy_normalized"] >= 0.7)
    return {
        "directories_analyzed": dir_count,
        "high_entropy_dirs": high_entropy,
        "outliers_flagged": len(outliers),
        "split_candidates": len(size_bands["split_candidates"]),
        "absorb_candidates": len(size_bands["absorb_candidates"]),
        "subdir_proposals": len(subdirs),
    }


# ── Output rendering ──

def render_json(report: dict) -> None:
    print(json.dumps(report, indent=2, sort_keys=False))


def render_human(report: dict, stale: str | None) -> None:
    print(f"Placement signals — generated {report['generated_at']}")
    if stale:
        print(f"  ⚠️  {stale}")
    print()

    s = report["summary"]
    print(f"Summary: {s['directories_analyzed']} directories analyzed · "
          f"{s['high_entropy_dirs']} high-entropy · {s['outliers_flagged']} outliers · "
          f"{s['split_candidates']} splits · {s['absorb_candidates']} absorbs · "
          f"{s['subdir_proposals']} subdir proposals")
    print()

    coh = report["signals"]["directory_coherence"]
    if coh:
        print(f"── S-1  Directory coherence (top 10, ranked by entropy) ───────────")
        print(f"  {'dir':<28} {'pages':>5}  {'H_norm':>7}  dominant_domains")
        for e in coh[:10]:
            doms = ", ".join(f"{n}({c})" for n, c in e["dominant_domains"])
            print(f"  {e['dir']:<28} {e['page_count']:>5}  {e['entropy_normalized']:>7.3f}  {doms}")
        print()

    out = report["signals"]["outliers"]
    if out:
        print(f"── S-2  Placement outliers (top 15, ranked by fraction) ───────────")
        print(f"  {'slug':<38} {'current':<20} {'suggested':<20} {'n':>3} frac")
        for o in out[:15]:
            print(f"  {o['slug'][:36]:<38} {o['current_dir'][:18]:<20} "
                  f"{o['suggested_dir'][:18]:<20} {o['neighbor_count']:>3} {o['fraction_elsewhere']:.2f}")
        print()

    sb = report["signals"]["size_bands"]
    if sb["split_candidates"]:
        print(f"── S-3a Split candidates (page_count > navigable_max) ─────────────")
        for e in sb["split_candidates"]:
            print(f"  {e['dir']:<28} {e['count']:>4} pages   (threshold: {e['threshold']})")
        print()
    if sb["absorb_candidates"]:
        print(f"── S-3b Absorb candidates (page_count < sparse_min) ───────────────")
        for e in sb["absorb_candidates"]:
            print(f"  {e['dir']:<28} {e['count']:>4} pages   (threshold: {e['threshold']})")
        print()

    subs = report["signals"]["subdir_proposals"]
    if subs:
        print(f"── S-4  Subdirectory emergence proposals ──────────────────────────")
        for e in subs:
            samples = ", ".join(e["sample_pages"][:3])
            more = f" +{len(e['sample_pages']) - 3}" if len(e["sample_pages"]) > 3 else ""
            print(f"  {e['parent']}/ → {e['proposed_name']}/  ({e['cluster_size']} pages)")
            print(f"     samples: {samples}{more}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    stale = check_manifest_freshness()
    thresholds, allowlist = _load_placement_config()
    manifest = load_manifest()

    by_dir = pages_by_dir(manifest, allowlist)
    outbound, inbound = build_graph(manifest)

    coh = s1_coherence(manifest, by_dir)
    outliers = s2_outliers(manifest, outbound, inbound, allowlist, thresholds)
    size_bands = s3_size_bands(by_dir, thresholds)
    subdirs = s4_subdir_proposals(manifest, by_dir, size_bands["split_candidates"], thresholds)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "stale_manifest_warning": stale,
        "config": thresholds,
        "signals": {
            "directory_coherence": coh,
            "outliers": outliers,
            "size_bands": size_bands,
            "subdir_proposals": subdirs,
        },
        "summary": build_summary(coh, outliers, size_bands, subdirs, len(by_dir)),
    }

    if args.json:
        render_json(report)
    else:
        render_human(report, stale)
    return 0


if __name__ == "__main__":
    sys.exit(main())
