#!/usr/bin/env python3
"""Build machine-readable index files for LLM agent consumption.

Generates:
  wiki/.index/manifest.yaml      — slug → {title, type, facets..., confidence, summary, links_to, dir, updated}
  wiki/.index/by-{facet}.yaml    — one reverse index per facet
  wiki/.index/by-type.yaml       — type → [slugs]

Facet names are read dynamically from .sprue/defaults.yaml → facets:.
Run from repo root: python3 .sprue/scripts/build-index.py
"""

import os, re, subprocess, sys, yaml
from pathlib import Path
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load as load_config
from lib import SKIP_DIRS, SKIP_FILES as SKIP, parse_frontmatter, find_wiki_pages, normalize_relationship_types  # backwards compat

# T11: Route engine/instance paths through resolvers.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

WIKI = instance_root() / "wiki"
INDEX_DIR = WIKI / ".index"

_cfg = load_config()
FACETS = _cfg["facets"]
# The first facet is the broadest — used for sub-index page generation
PRIMARY_FACET = list(FACETS.keys())[0]

VALID_TYPES = set(_cfg["page_types"].keys())

ENTITY_TYPES_PATH = instance_root() / "instance" / "entity-types.yaml"
ENTITY_TYPES_RAW = yaml.safe_load(ENTITY_TYPES_PATH.read_text()) if ENTITY_TYPES_PATH.exists() else {}
ENTITY_REGISTRY = ENTITY_TYPES_RAW.get("entities", {})

RELATIONSHIP_TYPES = normalize_relationship_types(
    ENTITY_TYPES_RAW.get("relationship_types", {})
)
REL_DISPLAY_TO_SLUG = {}
for _slug, _cfg in RELATIONSHIP_TYPES.items():
    REL_DISPLAY_TO_SLUG[_cfg.get("display", "").lower()] = _slug
    REL_DISPLAY_TO_SLUG[_slug] = _slug



def extract_wikilinks(body):
    """Return sorted unique wikilink targets from body text."""
    return sorted(set(re.findall(r"\[\[([a-zA-Z0-9_-]+)\]\]", body)))


def extract_title(body):
    """Extract H1 title from body."""
    m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    return m.group(1).strip() if m else None


def git_updated(path):
    """Get last commit date for a file from git."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", str(path)],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            return result.stdout.strip()[:10]  # YYYY-MM-DD
    except Exception:
        pass
    return None


def relative_dir(path):
    """Get the wiki subdirectory (e.g., 'data', 'containers')."""
    rel = path.relative_to(WIKI)
    return str(rel.parent) if str(rel.parent) != "." else ""


def extract_sections(body):
    """Extract H2 section names with their line numbers."""
    sections = {}
    lines = body.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("## "):
            sections[line[3:].strip()] = i + 1  # 1-indexed
    return sections


def extract_attributes(body):
    """Extract key-value pairs from ## Attributes section."""
    m = re.search(r'^## Attributes\n(.*?)(?=^## |\Z)', body, re.MULTILINE | re.DOTALL)
    if not m:
        return {}
    attrs = {}
    for line in m.group(1).strip().split('\n'):
        am = re.match(r'^-\s+\*\*(.+?)\*\*:\s*(.+)', line.strip())
        if am:
            attrs[am.group(1).strip()] = am.group(2).strip()
    return attrs


def extract_relationships(body):
    """Extract typed relationships from ## Relationships section."""
    m = re.search(r'^## Relationships\n(.*?)(?=^## |\Z)', body, re.MULTILINE | re.DOTALL)
    if not m:
        return []
    relationships = []
    for line in m.group(1).strip().split('\n'):
        rm = re.match(r'^-\s+\*\*(.+?)\*\*:\s*(.+)', line.strip())
        if rm:
            rel_display = rm.group(1).strip()
            targets_raw = rm.group(2).strip()
            rel_slug = REL_DISPLAY_TO_SLUG.get(rel_display.lower(),
                                                rel_display.lower().replace(' ', '-'))
            wikilink_targets = re.findall(r'\[\[([a-zA-Z0-9_-]+)\]\]', targets_raw)
            plain = re.sub(r'\[\[[^\]]+\]\]', '', targets_raw)
            external = [t.strip().strip(',').strip()
                        for t in plain.split(',') if t.strip().strip(',').strip()]
            relationships.append({
                'type': rel_slug,
                'targets': wikilink_targets,
                'external': external,
            })
    return relationships


def build_manifest():
    pages = find_wiki_pages(WIKI)
    manifest = {}
    tag_index = defaultdict(list)
    type_index = defaultdict(list)
    # One reverse index per facet
    facet_indexes = {name: defaultdict(list) for name in FACETS}

    for path in pages:
        slug = path.stem
        fm, body = parse_frontmatter(path)
        title = extract_title(body) or slug.replace("-", " ").title()
        links = extract_wikilinks(body)
        updated = git_updated(path)
        sections = extract_sections(body)

        # Count lines in frontmatter to offset section line numbers
        text = path.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        fm_lines = fm_match.group(0).count("\n") if fm_match else 0
        sections = {k: v + fm_lines for k, v in sections.items()}

        entry = {
            "title": title,
            "type": fm.get("type", "unknown"),
            "confidence": fm.get("confidence", "unknown"),
            "decay_tier": fm.get("decay_tier", "stable"),
            "summary": fm.get("summary", ""),
            "links_to": links,
            "dir": relative_dir(path),
            "updated": updated,
            "sections": sections,
            "risk_tier": fm.get("risk_tier", "reference"),
            "last_verified": fm.get("last_verified"),
            "provenance": fm.get("provenance", "unknown"),
        }

        # Dynamically add each facet's values to the entry
        for facet_name in FACETS:
            vals = fm.get(facet_name, [])
            if not isinstance(vals, list):
                vals = [vals] if vals else []
            entry[facet_name] = vals
            for v in vals:
                facet_indexes[facet_name][v].append(slug)
                tag_index[f"{facet_name}:{v}"].append(slug)
                tag_index[v].append(slug)  # union view

        # Entity type enrichment from registry (check slug first, then topics)
        if slug in ENTITY_REGISTRY:
            entry["entity_type"] = ENTITY_REGISTRY[slug]
        else:
            for t in entry.get("topic", []):
                if t in ENTITY_REGISTRY:
                    entry["entity_type"] = ENTITY_REGISTRY[t]
                    break

        # Attributes and Relationships (entity pages only)
        if entry["type"] == "entity":
            attrs = extract_attributes(body)
            if attrs:
                entry["attributes"] = attrs
            rels = extract_relationships(body)
            if rels:
                entry["relationships"] = rels

        manifest[slug] = entry
        page_type = entry["type"]
        if page_type not in VALID_TYPES and page_type != "unknown":
            print(f"⚠️  Invalid type '{page_type}' in {slug} (not in .sprue/defaults.yaml → page_types:)")
        type_index[page_type].append(slug)

    # Sort all indexes
    for name in facet_indexes:
        facet_indexes[name] = {k: sorted(v) for k, v in sorted(facet_indexes[name].items())}
    tag_index = {k: sorted(v) for k, v in sorted(tag_index.items())}
    type_index = {k: sorted(v) for k, v in sorted(type_index.items())}

    # Build entity type and relationship indexes
    entity_type_index = defaultdict(list)
    relationship_index = defaultdict(lambda: defaultdict(list))
    for slug, entry in manifest.items():
        if "entity_type" in entry:
            entity_type_index[entry["entity_type"]].append(slug)
        for rel in entry.get("relationships", []):
            for target in rel["targets"]:
                relationship_index[rel["type"]][slug].append(target)
    entity_type_index = {k: sorted(v) for k, v in sorted(entity_type_index.items())}
    relationship_index = {k: dict(sorted(v.items())) for k, v in sorted(relationship_index.items())}

    return manifest, dict(tag_index), dict(type_index), facet_indexes, dict(entity_type_index), dict(relationship_index)


def build_raw_by_slug(manifest, compilations):
    """Reverse index: current wiki slug → sorted unique raw file paths.

    Filters to slugs present in the current manifest (drops orphaned
    compilation rows from deleted or merged pages). Deduplicates raws
    across recompile history.
    """
    accum = defaultdict(set)
    for entry in compilations or []:
        raw = entry.get("raw")
        if not raw:
            continue
        for slug in entry.get("wiki", []) or []:
            if slug in manifest:
                accum[slug].add(raw)
    return {slug: sorted(raws) for slug, raws in sorted(accum.items())}


def write_yaml(data, path, header=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if header:
            f.write(header)
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=True, width=120)


def _build_domain_page(domain, slugs, manifest, inbound):
    """Generate a single domain page: Start Here + Decisions & Recipes + All Pages by importance."""
    count = len(slugs)
    ranked = sorted(slugs, key=lambda s: -inbound.get(s, 0))

    # Type counts
    type_mix = defaultdict(int)
    for s in slugs:
        type_mix[manifest[s].get("type", "concept")] += 1

    # Actionable pages (comparisons + recipes)
    actionable = [s for s in ranked if manifest[s].get("type") in ("comparison", "recipe")]

    lines = [f"---\ntitle: \"{domain}\"\n---\n"]
    lines.append(f"# {domain}\n")
    type_stats = ", ".join(f"{c} {t}s" for t, c in sorted(type_mix.items()) if c > 0)
    lines.append(
        f"**{count} pages** — {type_stats}. "
        f"[[overview|← Overview]]\n"
    )

    # Start Here — top 5 by inbound links (skip for tiny domains)
    if count > 5:
        lines.append("## Start Here\n")
        for i, s in enumerate(ranked[:5], 1):
            summary = manifest[s].get("summary", "")
            ptype = manifest[s].get("type", "")
            lines.append(f"{i}. [[{s}]] `{ptype}` — {summary}")
        lines.append("")

    # Decisions & Recipes — promoted for quick access
    if actionable:
        lines.append("## Decisions & Recipes\n")
        for s in actionable:
            summary = manifest[s].get("summary", "")
            ptype = manifest[s].get("type", "")
            lines.append(f"- [[{s}]] `{ptype}` — {summary}")
        lines.append("")

    # All Pages — single flat list sorted by importance, type as badge
    lines.append("## All Pages\n")
    for s in ranked:
        summary = manifest[s].get("summary", "")
        ptype = manifest[s].get("type", "")
        lines.append(f"- [[{s}]] `{ptype}` — {summary}")
    lines.append("")

    return "\n".join(lines) + "\n"


def build_overview(manifest, by_type, facet_indexes):
    """Generate wiki/overview.md — fixed-size navigation hub that doesn't grow with page count.

    Also generates wiki/.index/domain-*.md sub-indexes for the primary facet.
    """
    total = len(manifest)
    now = datetime.now().strftime("%Y-%m-%d")

    # Inbound link counts for ranking
    inbound = defaultdict(int)
    for entry in manifest.values():
        for target in entry.get("links_to", []):
            inbound[target] += 1

    # Directory counts
    dir_counts = defaultdict(int)
    for entry in manifest.values():
        top_dir = entry["dir"].split("/")[0] if entry["dir"] else "root"
        dir_counts[top_dir] += 1

    # Top pages per dir by inbound link count — computed signal, not curated prose.
    # The reader (LLM agent) gets actually-useful navigation hints derived from
    # the wiki's own link graph.
    dir_top_pages = defaultdict(list)
    for slug, entry in manifest.items():
        if slug == "_meta":
            continue
        d = entry.get("dir", "").split("/")[0] if entry.get("dir") else "root"
        dir_top_pages[d].append((inbound.get(slug, 0), slug))

    type_counts = {t: len(slugs) for t, slugs in by_type.items()}

    # Primary facet sorted by size (for sub-index pages and Browse section)
    primary_index = facet_indexes[PRIMARY_FACET]
    primary_sorted = sorted(primary_index.items(), key=lambda x: -len(x[1]))

    # Recently updated (top 10)
    recent = sorted(
        ((slug, e) for slug, e in manifest.items() if e.get("updated")),
        key=lambda x: x[1]["updated"] or "", reverse=True
    )[:10]

    # ── Generate task-oriented per-primary-facet pages ──
    domain_dir = WIKI / "domains"
    domain_dir.mkdir(exist_ok=True)

    for value, slugs in primary_sorted:
        page = _build_domain_page(value, slugs, manifest, inbound)
        (domain_dir / f"domain-{value}.md").write_text(page, encoding="utf-8")

    # ── Build overview.md (fixed size ~150 lines) ──
    TOP_N = 5  # pages to preview per primary facet value

    lines = [
        "---\ntitle: Knowledge Base Overview\n---\n",
        "# Knowledge Base Overview\n",
        f"**{total} pages** · "
        + " · ".join(f"{c} {t}s" for t, c in sorted(type_counts.items()) if c > 0),
        f"Generated {now}\n",
    ]

    # ── Agent Quick Start ──
    facet_files = " or ".join(f"`wiki/.index/by-{name}.yaml`" for name in FACETS)
    lines += [
        "## Agent Quick Start\n",
        f"1. **Find pages**: {facet_files}",
        f"2. **Check relevance**: `wiki/.index/manifest.yaml` → summary, {PRIMARY_FACET}, sections",
        "3. **Read the page**: prefer `confidence: high`\n",
        "**Also**: `query-plans.yaml` for curated paths · "
        "`python3 .sprue/scripts/semantic-search.py \"query\"` for semantic search · "
        "`by-type.yaml` for recipes/comparisons\n",
    ]

    # ── Directories ──
    # Emergent: dir set from manifest, top pages from the link graph. No
    # curated prose anywhere — readers derive scope from page summaries
    # via the manifest or semantic-search.
    lines += [
        "## Directories\n",
        "_To learn what a directory contains, sample page summaries from `wiki/.index/manifest.yaml` or run `python3 .sprue/scripts/semantic-search.py \"<query>\"`._\n",
        "| Directory | Pages | Top pages (by inbound links) |",
        "|-----------|-------|------------------------------|",
    ]
    for d, count in sorted(dir_counts.items(), key=lambda x: (-x[1], x[0])):
        top = sorted(dir_top_pages.get(d, []), reverse=True)[:3]
        top_links = " · ".join(f"[[{slug}]]" for _, slug in top) if top else ""
        lines.append(f"| {d}/ | {count} | {top_links} |")

    # ── Recently Updated ──
    if recent:
        lines += ["", "## Recently Updated\n"]
        for slug, entry in recent:
            summary = entry.get("summary", "")
            if len(summary) > 100:
                summary = summary[:97] + "..."
            lines.append(f"- [[{slug}]] — {summary} *({entry['updated']})*")

    # ── Browse by each bounded facet (those with hard_max) ──
    for facet_name, facet_cfg in FACETS.items():
        if not facet_cfg.get("hard_max"):
            continue  # unbounded facets (e.g. topics) are too large for overview
        idx = facet_indexes[facet_name]
        sorted_items = sorted(idx.items(), key=lambda x: -len(x[1]))

        if facet_name == PRIMARY_FACET:
            # Primary facet: show top pages per value with links to sub-index
            lines += ["", f"## Browse by {facet_name.title()}\n"]
            for value, slugs in sorted_items:
                count = len(slugs)
                ranked = sorted(slugs, key=lambda s: -inbound.get(s, 0))
                top_slugs = ranked[:TOP_N]
                top_links = ", ".join(f"[[{s}]]" for s in top_slugs)
                more = f" + {count - TOP_N} more" if count > TOP_N else ""
                lines.append(
                    f"**[[domain-{value}|{value}]]** ({count}) — "
                    f"{top_links}{more}"
                )
        else:
            # Other bounded facets: compact listing
            lines += ["", f"## Cross-Cutting {facet_name.title()}\n"]
            links = []
            for value, slugs in sorted_items:
                links.append(f"**{value}** ({len(slugs)})")
            lines.append(" · ".join(links))

    # ── Comparisons (slug-only, one line) ──
    comp_slugs = sorted(by_type.get("comparison", []))
    lines += [
        "",
        f"## Comparisons ({len(comp_slugs)})\n",
        ", ".join(f"[[{s}]]" for s in comp_slugs),
    ]

    # ── Recipes (slug-only, one line) ──
    recipe_slugs = sorted(by_type.get("recipe", []))
    lines += [
        "",
        f"## Recipes ({len(recipe_slugs)})\n",
        ", ".join(f"[[{s}]]" for s in recipe_slugs),
    ]

    lines.append("")
    (WIKI / "overview.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


COMPILATIONS_PATH = instance_root() / "instance" / "state" / "compilations.yaml"


def load_compilations():
    """Load the compile ledger. Tolerate missing file (fresh KB)."""
    if not COMPILATIONS_PATH.exists():
        return []
    return yaml.safe_load(COMPILATIONS_PATH.read_text()) or []


def main():
    manifest, by_tag, by_type, facet_indexes, entity_type_index, relationship_index = build_manifest()
    compilations = load_compilations()
    raw_by_slug = build_raw_by_slug(manifest, compilations)

    meta = {
        "_meta": {
            "generated": datetime.now().isoformat()[:19],
            "total_pages": len(manifest),
            "pages_without_summary": sum(1 for v in manifest.values() if not v["summary"]),
        }
    }

    write_yaml(
        {**meta, **manifest},
        INDEX_DIR / "manifest.yaml",
        "# Machine-readable wiki manifest for LLM agents\n# Auto-generated by .sprue/scripts/build-index.py — do not edit\n\n"
    )
    write_yaml(
        by_type,
        INDEX_DIR / "by-type.yaml",
        "# Reverse index: type → [page slugs]\n# Auto-generated by .sprue/scripts/build-index.py — do not edit\n\n"
    )

    # One reverse index file per facet
    for facet_name, idx in facet_indexes.items():
        write_yaml(
            idx,
            INDEX_DIR / f"by-{facet_name}.yaml",
            f"# Reverse index: {facet_name} → [page slugs]\n# Auto-generated by .sprue/scripts/build-index.py — do not edit\n\n"
        )

    # Entity type and relationship indexes
    if entity_type_index:
        write_yaml(
            entity_type_index,
            INDEX_DIR / "by-entity-type.yaml",
            "# Reverse index: entity_type → [page slugs]\n# Auto-generated by .sprue/scripts/build-index.py — do not edit\n\n"
        )
    if relationship_index:
        write_yaml(
            relationship_index,
            INDEX_DIR / "by-relationship.yaml",
            "# Relationship graph: rel_type → {source: [targets]}\n# Auto-generated by .sprue/scripts/build-index.py — do not edit\n\n"
        )

    write_yaml(
        raw_by_slug,
        INDEX_DIR / "by-slug-raws.yaml",
        "# Reverse index: slug → [raw file paths that contributed]\n# Filtered against current manifest; orphaned compilation rows are dropped.\n# Auto-generated by .sprue/scripts/build-index.py — do not edit\n\n"
    )

    build_overview(manifest, by_type, facet_indexes)

    entities_typed = sum(1 for v in manifest.values() if isinstance(v, dict) and "entity_type" in v)
    print(f"✅ Index built: {len(manifest)} pages")
    print(f"   manifest.yaml:   {INDEX_DIR / 'manifest.yaml'}")
    for facet_name in FACETS:
        print(f"   by-{facet_name}.yaml: {INDEX_DIR / f'by-{facet_name}.yaml'}")
    print(f"   by-type.yaml:    {INDEX_DIR / 'by-type.yaml'}")
    if entity_type_index:
        print(f"   by-entity-type:  {len(entity_type_index)} kinds, {entities_typed} entities typed")
    if relationship_index:
        edges = sum(len(targets) for sources in relationship_index.values() for targets in sources.values())
        print(f"   by-relationship: {len(relationship_index)} rel types, {edges} edges")
    dropped = sum(1 for row in compilations for s in (row.get("wiki") or []) if s not in manifest)
    print(f"   by-slug-raws:    {len(raw_by_slug)} slugs indexed ({dropped} orphaned compilation refs dropped)")
    print(f"   overview.md:     wiki/overview.md")
    print(f"   Pages without summary: {meta['_meta']['pages_without_summary']}")


if __name__ == "__main__":
    main()
