#!/usr/bin/env python3
"""Run all verification checks from memory/rules.yaml.

Rules are structured YAML: each entry has a `name` and either a
`command` (argv list — executed directly) or `shell` (bash source —
executed via `bash -c`). Optional `scope` is one of `page` (default;
per-page, compatible with --file mode) or `whole` (full-wiki, skipped
in --file mode). Rules that want a subset filter inside their shell
block using frontmatter — the rule DSL never reads filesystem paths
as a semantic claim.

Invocation compatible with the previous verify.sh:
  python3 sprue/scripts/verify.py                    # full-wiki sweep
  python3 sprue/scripts/verify.py --file <path>      # single-file mode
  python3 sprue/scripts/verify.py --json             # machine-readable report
  python3 sprue/scripts/verify.py --jobs 4           # parallel execution

Exit: 0 if no rule failed, 1 otherwise.
"""

import argparse
import json as jsonlib
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
RULES_FILE = ROOT / "memory" / "rules.yaml"
WIKI = ROOT / "wiki"
SKIP_DIRS = {".index", ".obsidian", "domains"}
SKIP_FILES = {"overview.md"}
RULE_TIMEOUT_SEC = 120


@dataclass
class Rule:
    name: str
    command: Optional[list[str]] = None
    shell: Optional[str] = None
    scope: str = "page"
    source: Optional[str] = None


@dataclass
class RuleResult:
    rule: Rule
    status: str  # "pass" | "fail" | "skip"
    violations: list[str] = field(default_factory=list)
    stderr: str = ""
    duration_ms: int = 0
    reason: Optional[str] = None
    crashed: bool = False
    timed_out: bool = False


def parse_rules(path: Path) -> list[Rule]:
    """Load rules from YAML. Raises SystemExit on unparseable input."""
    if not path.exists():
        return []
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"❌ {path} is not valid YAML — cannot run any rule.", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        print("   Lint with: python3 sprue/scripts/lint-rules.py", file=sys.stderr)
        sys.exit(1)
    if not isinstance(doc, list):
        return []
    rules: list[Rule] = []
    for entry in doc:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        rules.append(
            Rule(
                name=name,
                command=entry.get("command"),
                shell=entry.get("shell"),
                scope=entry.get("scope", "page"),
                source=entry.get("source"),
            )
        )
    return rules


def build_content_pages(target_file: Optional[str]) -> tuple[Path, list[str]]:
    """Build the canonical content-page list as a temp file; return (path, list)."""
    if target_file:
        pages = [target_file]
    else:
        pages = []
        for p in WIKI.rglob("*.md"):
            parts = p.relative_to(ROOT).parts
            if any(part in SKIP_DIRS for part in parts):
                continue
            if p.name in SKIP_FILES:
                continue
            pages.append(str(p.relative_to(ROOT)))
        pages.sort()

    fd, tmp = tempfile.mkstemp(suffix=".pages", text=True)
    os.close(fd)
    path = Path(tmp)
    path.write_text("\n".join(pages) + ("\n" if pages else ""), encoding="utf-8")
    return path, pages


def write_pages_tempfile(pages: list[str]) -> Path:
    fd, tmp = tempfile.mkstemp(suffix=".pages", text=True)
    os.close(fd)
    path = Path(tmp)
    path.write_text("\n".join(pages) + ("\n" if pages else ""), encoding="utf-8")
    return path


def run_rule(rule: Rule, content_pages_full: list[str], target_file: Optional[str]) -> RuleResult:
    """Execute a single rule."""
    # page or whole — use the full list built by build_content_pages()
    # (target_file mode shortcuts this to a single file in the shared path already)
    # Rules that want a subset filter inside their shell block using frontmatter;
    # path-based scope was deleted to keep filesystem out of the rule DSL.
    rule_tempfile: Optional[Path] = None
    content_pages_path = os.environ.get("CONTENT_PAGES", "")
    if not content_pages_path:
        # Caller didn't populate shared env; fall back to writing a tempfile
        rule_tempfile = write_pages_tempfile(content_pages_full)
        content_pages_path = str(rule_tempfile)

    env = {**os.environ, "CONTENT_PAGES": content_pages_path}

    if rule.command:
        argv = rule.command
    else:
        argv = ["bash", "-c", rule.shell or ""]

    start = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            env=env,
            capture_output=True,
            text=True,
            timeout=RULE_TIMEOUT_SEC,
            cwd=str(ROOT),
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        stdout = proc.stdout
        stderr = proc.stderr

        if not stdout.strip() and not stderr.strip():
            result = RuleResult(rule=rule, status="pass", duration_ms=duration_ms)
        elif not stdout.strip() and stderr.strip():
            result = RuleResult(
                rule=rule,
                status="fail",
                stderr=stderr,
                duration_ms=duration_ms,
                crashed=True,
            )
        else:
            violations = [l for l in stdout.splitlines() if l.strip()]
            result = RuleResult(
                rule=rule,
                status="fail",
                violations=violations,
                stderr=stderr,
                duration_ms=duration_ms,
            )
    except subprocess.TimeoutExpired:
        duration_ms = int((time.monotonic() - start) * 1000)
        result = RuleResult(
            rule=rule,
            status="fail",
            violations=[f"TIMEOUT after {RULE_TIMEOUT_SEC}s"],
            duration_ms=duration_ms,
            timed_out=True,
        )
    finally:
        if rule_tempfile is not None:
            try:
                rule_tempfile.unlink()
            except OSError:
                pass

    return result


def print_human(results: list[RuleResult], page_count: int, target_file: Optional[str]) -> tuple[int, int, int, int]:
    if target_file:
        print(f"=== Verifying: {target_file} ===")
    else:
        print(f"=== KB Verification Sweep ({page_count} content pages) ===")
    print()

    passed = failed = skipped = 0
    total = len(results)

    for r in results:
        if r.status == "skip":
            skipped += 1
            continue
        if r.status == "pass":
            passed += 1
            print(f"✅ {r.rule.name}")
            print()
            continue
        failed += 1
        print(f"❌ {r.rule.name}")
        if r.crashed:
            err_head = "\n".join(r.stderr.splitlines()[:3])
            print(f"   ERROR: {err_head}")
        else:
            for line in r.violations[:5]:
                print(f"   {line}")
            if len(r.violations) > 5:
                print(f"   ... and {len(r.violations) - 5} more")
        print()

    print(f"=== Results: {passed} passed, {failed} failed, {skipped} skipped (of {total} rules) ===")
    return passed, failed, skipped, total


def print_json(results: list[RuleResult], page_count: int, target_file: Optional[str]) -> tuple[int, int, int, int]:
    passed = sum(1 for r in results if r.status == "pass")
    failed = sum(1 for r in results if r.status == "fail")
    skipped = sum(1 for r in results if r.status == "skip")
    total = len(results)
    mode = "single-file" if target_file else "whole-wiki"
    report = {
        "summary": {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": total,
            "mode": mode,
            "page_count": page_count,
            "target_file": target_file,
        },
        "rules": [
            {
                "name": r.rule.name,
                "status": r.status,
                "scope": r.rule.scope,
                "violations": r.violations,
                "duration_ms": r.duration_ms,
                "stderr": r.stderr,
                "reason": r.reason,
                "crashed": r.crashed,
                "timed_out": r.timed_out,
            }
            for r in results
        ],
    }
    print(jsonlib.dumps(report, indent=2))
    return passed, failed, skipped, total


def main() -> int:
    parser = argparse.ArgumentParser(description="Run verification checks from memory/rules.yaml")
    parser.add_argument("--file", dest="target_file", default=None, help="Verify a single file instead of the full wiki")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON report")
    parser.add_argument("--jobs", type=int, default=1, help="Parallel workers (default 1, sequential)")
    args = parser.parse_args()

    if args.target_file and not Path(args.target_file).is_file():
        print(f"File not found: {args.target_file}", file=sys.stderr)
        return 1

    rules = parse_rules(RULES_FILE)
    if not rules:
        if args.json:
            print(jsonlib.dumps({"summary": {"passed": 0, "failed": 0, "skipped": 0, "total": 0}, "rules": []}))
        else:
            print("No rules file found or no rules parsed.")
        return 0

    content_pages_file, content_pages_list = build_content_pages(args.target_file)
    page_count = len(content_pages_list)

    # Populate env for `page`-scope and `whole`-scope rules — they share this path
    os.environ["CONTENT_PAGES"] = str(content_pages_file)

    # Classify each rule: skip or run
    pending: list[tuple[int, Rule]] = []
    results_by_rule: dict[int, RuleResult] = {}
    for idx, rule in enumerate(rules):
        if args.target_file and rule.scope == "whole":
            results_by_rule[idx] = RuleResult(
                rule=rule,
                status="skip",
                reason="whole-scope rule skipped in --file mode",
            )
        else:
            pending.append((idx, rule))

    # Execute
    if args.jobs > 1 and pending:
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = {pool.submit(run_rule, rule, content_pages_list, args.target_file): idx for idx, rule in pending}
            for fut in futures:
                idx = futures[fut]
                results_by_rule[idx] = fut.result()
    else:
        for idx, rule in pending:
            results_by_rule[idx] = run_rule(rule, content_pages_list, args.target_file)

    try:
        content_pages_file.unlink()
    except OSError:
        pass

    results = [results_by_rule[i] for i in range(len(rules))]

    if args.json:
        passed, failed, skipped, total = print_json(results, page_count, args.target_file)
    else:
        passed, failed, skipped, total = print_human(results, page_count, args.target_file)

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
