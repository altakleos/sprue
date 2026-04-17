#!/usr/bin/env python3
"""Confidence decay — smooth sigmoid degradation, no cliff effects.

Fixes over the previous exponential model:
  1. Sigmoid curve (not exponential) — gradual S-curve transition, not a cliff.
  2. Per-page jitter from slug hash — spreads downgrades across days.
  3. Never-verified penalty — unverified pages start at 80% freshness, not 100%.
  4. Author multiplier — LLM content decays 1.5× faster than human.
  5. Reads domain/tech fields (not old tags field).

Half-lives and risk_tier multipliers live in instance/config.yaml.

Usage:
  python3 .sprue/scripts/decay.py              # Report only
  python3 .sprue/scripts/decay.py --apply      # Apply downgrades to files
"""

import re, sys, math, hashlib, yaml
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load as load_config

# T11: Route engine/instance paths through resolvers.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

WIKI = instance_root() / "wiki"
MANIFEST = WIKI / ".index" / "manifest.yaml"
DEFAULT_HALF_LIFE = 365

# Freshness thresholds: high ≥ 60, medium ≥ 30, low < 30
HIGH_FLOOR = 60
MEDIUM_FLOOR = 30

# Never-verified pages start at 80% freshness (20% penalty)
UNVERIFIED_PENALTY = 0.20

# Author speed: >1 = faster decay, <1 = slower
AUTHOR_SPEED = {"llm": 1.5, "hybrid": 1.0, "human": 0.75}

# Jitter: ±30% for unverified (spread the cliff), ±10% for verified (tight reset)
JITTER_UNVERIFIED = 0.30
JITTER_VERIFIED = 0.10


def load_facets():
    config = load_config()
    return config.get("half_life_tiers", {}), config.get("risk_tier_multipliers", {})


def slug_jitter(slug, half_life, verified):
    """Deterministic per-page jitter in days, derived from slug hash."""
    h = int(hashlib.md5(slug.encode()).hexdigest()[:8], 16)
    norm = (h / 0xFFFFFFFF) * 2 - 1  # [-1, 1]
    frac = JITTER_VERIFIED if verified else JITTER_UNVERIFIED
    return norm * frac * half_life


def get_half_life(decay_tier, risk_tier, half_lives, multipliers):
    """Half-life from decay_tier × risk_tier multiplier."""
    base = half_lives.get(decay_tier, DEFAULT_HALF_LIFE)
    return max(30, base * multipliers.get(risk_tier, 1.0))


def sigmoid_freshness(days, half_life):
    """Sigmoid decay: 100 at day 0, 50 at half_life, ~0 at 2× half_life.
    k=3.5/hl gives a transition window spanning ~60% of the half-life."""
    k = 3.5 / half_life
    return 100.0 / (1.0 + math.exp(k * (days - half_life)))


def read_author(slug):
    """Read author field from page frontmatter."""
    for p in WIKI.glob(f"**/{slug}.md"):
        try:
            m = re.search(r"^author:\s*(\w+)", p.read_text(encoding="utf-8")[:500], re.MULTILINE)
            return m.group(1) if m else "llm"
        except Exception:
            pass
    return "llm"


def apply_downgrade(path, new_confidence):
    text = path.read_text(encoding="utf-8")
    new = re.sub(r"^(confidence:\s*)\w+", f"\\g<1>{new_confidence}", text, count=1, flags=re.MULTILINE)
    if new != text:
        path.write_text(new, encoding="utf-8")


def main():
    apply = "--apply" in sys.argv
    now = datetime.now()

    if not MANIFEST.exists():
        print("Error: manifest.yaml not found. Run: python3 .sprue/scripts/build-index.py"); sys.exit(1)

    half_lives, multipliers = load_facets()
    manifest = yaml.safe_load(MANIFEST.read_text()) or {}
    manifest.pop("_meta", None)
    downgrades = []

    for slug, meta in sorted(manifest.items()):
        confidence = meta.get("confidence", "unknown")
        if confidence not in ("high", "medium"):
            continue

        last_verified = meta.get("last_verified")
        updated = meta.get("updated")
        verified = bool(last_verified and str(last_verified) != "null")

        ref_date = None
        if verified:
            ref_date = datetime.fromisoformat(str(last_verified))
        elif updated:
            ref_date = datetime.fromisoformat(str(updated))
        if not ref_date:
            continue

        days = (now - ref_date).days
        decay_tier = meta.get("decay_tier", "stable")
        risk_tier = meta.get("risk_tier", "reference")
        hl = get_half_life(decay_tier, risk_tier, half_lives, multipliers)

        # Author multiplier: LLM pages decay faster
        author = read_author(slug)
        hl = hl / AUTHOR_SPEED.get(author, 1.0)
        hl = max(20, hl)  # absolute floor

        # Per-page jitter to prevent mass-downgrade days
        jitter = slug_jitter(slug, hl, verified)
        effective_hl = max(hl * 0.5, hl + jitter)

        # Compute freshness via sigmoid
        freshness = sigmoid_freshness(days, effective_hl)

        # Never-verified penalty: start at 80%, not 100%
        if not verified:
            freshness *= (1.0 - UNVERIFIED_PENALTY)

        # Determine target confidence (only downgrade, never upgrade)
        if freshness >= HIGH_FLOOR:
            target = confidence
        elif freshness >= MEDIUM_FLOOR:
            target = "medium"
        else:
            target = "low"

        rank = {"high": 2, "medium": 1, "low": 0}
        if rank.get(target, 0) < rank.get(confidence, 0):
            downgrades.append({
                "slug": slug, "current": confidence, "proposed": target,
                "freshness": freshness, "hl": effective_hl, "days": days,
                "author": author, "verified": verified, "decay_tier": decay_tier,
            })

    if not downgrades:
        print("✅ No confidence downgrades needed."); return

    print(f"{'Applied' if apply else 'Proposed'} confidence downgrades: {len(downgrades)}")
    for d in downgrades[:20]:
        v = "✓" if d["verified"] else "✗"
        print(f"  {d['slug']}: {d['current']}→{d['proposed']} "
              f"(fresh={d['freshness']:.0f}% hl={d['hl']:.0f}d age={d['days']}d {v} {d['author']})")
        if apply:
            for p in WIKI.glob(f"**/{d['slug']}.md"):
                apply_downgrade(p, d["proposed"]); break
    if len(downgrades) > 20:
        print(f"  ... and {len(downgrades) - 20} more")
    if not apply:
        print(f"\nRun with --apply to apply these changes.")


if __name__ == "__main__":
    main()
