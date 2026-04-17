---
feature: distribution
serves: docs/specs/platform-distribution.md
design: docs/design/sprue-distribution.md
status: planned
date: 2026-04-16
---
# Plan: Sprue Distribution Model

Implement the pip-installable distribution model per ADR-0033. Users will `pip install sprue`, run `sprue init`, and get a working KB instance with engine files copied locally as `.sprue/`.

## Success Criteria

```json
{
  "functional": [
    "pip install -e . installs the sprue CLI from a clean checkout",
    "sprue init <dir> scaffolds a complete, verify-passing instance",
    "sprue upgrade replaces .sprue/ atomically without touching instance content",
    "sprue verify works in both source-repo and user-instance contexts"
  ],
  "observable": [
    "Built wheel contains engine files, excludes instance/docs paths",
    "LLM agent reads .sprue/engine.md and boots the protocol chain",
    "schema_version mismatch produces a clear error at verify time"
  ],
  "pass_fail": [
    "sprue init in existing .sprue/ dir → error (without --force)",
    "sprue init --force in existing .sprue/ dir → success",
    "Every spec invariant in platform-distribution.md maps to ≥1 test"
  ]
}
```

## Tasks

### Phase A — Packaging Foundation

- [ ] T1: Create `pyproject.toml` with hatchling backend, PEP 621 metadata, `[project.scripts] sprue = "sprue.cli:main"`, `requires-python = ">=3.10"`, dependencies `[click, pyyaml]`, optional-dependencies for semantic search `[sentence-transformers, numpy]` → `pyproject.toml`
- [ ] T2: Create `src/sprue/` package layout — move engine files into `src/sprue/engine/` (protocols/, scripts/, prompts/, schemas/, profiles/, defaults.yaml, engine.md, README.md, verify.sh, reset.sh) → `src/sprue/engine/` (depends: T1)
- [ ] T3: Create `src/sprue/__init__.py` with `__version__` string → `src/sprue/__init__.py` (depends: T2)
- [ ] T4: Create `src/sprue/cli/__init__.py` — stub click group with `main()` entry point, subcommands registered in later tasks → `src/sprue/cli/__init__.py` (depends: T2)
- [ ] T5: Delete `requirements.txt` — all deps now in `pyproject.toml` → `requirements.txt` (depends: T1)
- [ ] T6: Add `[tool.hatch.build.targets.wheel] packages = ["src/sprue"]` to pyproject.toml, confirm `hatchling build` produces a wheel containing `src/sprue/engine/**` → `pyproject.toml` (depends: T2)
- [ ] T7: Verify `pip install -e .` succeeds and `sprue --help` prints the click group help → manual test (depends: T4, T6)

### Phase B — Engine Root Resolver

- [ ] T8: Create `src/sprue/engine_root.py` — single module exporting `engine_root() -> Path` (returns `.sprue/` in user instances, or `importlib.resources.files("sprue.engine")` in package-dev mode) and `instance_root() -> Path` (returns the instance directory containing wiki/, raw/, memory/) → `src/sprue/engine_root.py` (depends: T2)
- [ ] T9: Refactor `src/sprue/engine/scripts/config.py` — replace hardcoded `ROOT / "sprue" / "defaults.yaml"` with `engine_root() / "defaults.yaml"`, replace `ROOT / "instance" / "config.yaml"` with `instance_root() / "instance" / "config.yaml"` → `src/sprue/engine/scripts/config.py` (depends: T8)
- [ ] T10: Audit all Python scripts in `src/sprue/engine/scripts/` — catalog every hardcoded `sprue/` path reference (current count: ~19 files, ~100+ refs in scripts alone). Produce a checklist of files and line numbers → audit artifact in PR description (depends: T8)
- [ ] T11: Update all Python scripts to use `engine_root()` / `instance_root()` imports instead of hardcoded `sprue/` paths. Scripts that walk `wiki/` must use `instance_root()`, NOT `engine_root()` → `src/sprue/engine/scripts/*.py` (depends: T9, T10)
- [ ] T12: Update `src/sprue/engine/verify.sh` and `src/sprue/engine/reset.sh` — make paths relative within the engine directory or accept a root argument → `src/sprue/engine/verify.sh`, `src/sprue/engine/reset.sh` (depends: T8)
- [ ] T13: Update all protocol markdown files — replace `sprue/` path references with `.sprue/` (these are instructions the LLM reads in user instances where the directory IS `.sprue/`) → `src/sprue/engine/protocols/*.md` (depends: T2)
- [ ] T14: Update `src/sprue/engine/engine.md` — replace ~38 `sprue/` references with `.sprue/` equivalents → `src/sprue/engine/engine.md` (depends: T2)
- [ ] T15: Update `src/sprue/engine/prompts/*.md` — replace hardcoded `sprue/` paths → `src/sprue/engine/prompts/*.md` (depends: T2)
- [ ] T16: Run `bash src/sprue/engine/verify.sh` (or equivalent) — confirm all validators still pass after the path migration → manual test (depends: T11, T12, T13, T14, T15)

### Phase C — CLI Commands

- [ ] T17: Create `src/sprue/cli/init.py` — `sprue init <directory>` command: prompts for identity (one sentence), copies engine files from `importlib.resources.files("sprue.engine")` via `as_file()` + `shutil.copytree` into `<directory>/.sprue/`, creates `instance/identity.md`, `instance/config.yaml` (empty overrides), empty dirs (raw/, wiki/, notebook/, inbox/, memory/, state/), generates AGENTS.md, README.md, .gitignore from templates, writes `.sprue/.sprue-version` → `src/sprue/cli/init.py` (depends: T4, T8)
- [ ] T18: Create `src/sprue/templates/` — template files for AGENTS.md, README.md, .gitignore, instance/config.yaml, instance/identity.md with `{{variable}}` placeholders (no Jinja2) → `src/sprue/templates/` (depends: T2)
- [ ] T19: Implement init idempotency — `sprue init` checks for existing `.sprue/` directory, refuses with error message ("Instance already exists. Use `sprue upgrade` to update the engine, or `sprue init --force` to reinitialize."), `--force` flag overwrites → `src/sprue/cli/init.py` (depends: T17)
- [ ] T20: Implement non-interactive fallback — if stdin is not a TTY and no `--identity` flag provided, exit with usage hint → `src/sprue/cli/init.py` (depends: T17)
- [ ] T21: Create `src/sprue/cli/upgrade.py` — `sprue upgrade` command: compares installed package version vs `.sprue/.sprue-version`, copies new engine files to temp dir, replaces `.sprue/` contents via atomic rename, updates `.sprue-version`, checks `schema_version` compatibility, prints migration instructions if schema changed → `src/sprue/cli/upgrade.py` (depends: T8, T17)
- [ ] T22: Implement upgrade atomicity — write to temp dir first, rename to `.sprue/` only on success. If interrupted, original `.sprue/` remains intact. Handle error cases: no `.sprue/` dir → error, already up to date → message → `src/sprue/cli/upgrade.py` (depends: T21)
- [ ] T23: Create `src/sprue/cli/verify.py` — `sprue verify` command: resolves paths via `engine_root()`, delegates to `src/sprue/engine/scripts/verify.py`, forwards arguments (including `--file`), exits with verify.py's exit code → `src/sprue/cli/verify.py` (depends: T8, T11)
- [ ] T24: Register all subcommands (init, upgrade, verify) in the click group → `src/sprue/cli/__init__.py` (depends: T17, T21, T23)

### Phase D — Enforcement Mechanisms

- [ ] T25: Refactor existing `check_schema_version()` in `src/sprue/engine/scripts/check-config.py` (currently does exact-match against a hardcoded constant) to range-based validation — assert instance `schema_version` is within engine's supported range (read from `supported_schema_versions.min`/`max` in defaults.yaml). Fail with clear message if out of range → `src/sprue/engine/scripts/check-config.py` (depends: T9)
- [ ] T26: Add `supported_schema_versions` range to `src/sprue/engine/defaults.yaml` — e.g., `supported_schema_versions: {min: 1, max: 1}` → `src/sprue/engine/defaults.yaml` (depends: T2)
- [ ] T27: Create `src/sprue/engine/scripts/check-package-contents.py` — build-time validator that inspects the built wheel (or package directory) and asserts no instance paths (wiki/, raw/, memory/, instance/, docs/, notebook/, inbox/) are present → `src/sprue/engine/scripts/check-package-contents.py` (depends: T6)
- [ ] T28: Wire `check-package-contents` invocation into the CI workflow (T29 runs it against the built wheel). No separate `memory/rules.yaml` entry is needed in the platform repo — `memory/rules.yaml` is instance-side and not present here → CI gate only (depends: T27)

### Phase E — CI and Distribution

- [ ] T29: Create `.github/workflows/verify.yml` — runs on push/PR: checkout, `pip install -e .`, run `sprue verify`, run `sprue init` in a tempdir and verify the scaffolded instance, run `check-package-contents.py` against built wheel → `.github/workflows/verify.yml` (depends: T23, T27)
- [ ] T30: Create `.github/workflows/release.yml` — runs on tag push: builds wheel via `hatchling build`, publishes to PyPI via trusted publishing → `.github/workflows/release.yml` (depends: T6)
- [ ] T31: Test full package build cycle — `hatchling build` produces wheel, wheel contains `sprue/engine/**`, wheel excludes `instance/`, `docs/`, `wiki/`, `raw/`, `memory/` → manual test (depends: T6, T27)

### Phase F — Dogfood and Docs

- [ ] T32: Dogfood test — `pip install -e .` in a clean venv, `sprue init test-kb` in a throwaway dir, confirm scaffolded instance passes `sprue verify`, confirm LLM agent can read `.sprue/engine.md` and follow the boot chain → manual test (depends: T24)
- [ ] T33: Update `README.md` Quick Start section — replace current instructions with `pip install sprue` / `sprue init my-kb` / `cd my-kb` flow → `README.md` (depends: T24)
- [ ] T34: Update `AGENTS.md` — fix any path references broken by the `sprue/` → `src/sprue/engine/` restructure, update Repository Map, update Key Commands to reference `sprue verify` CLI alongside `bash .sprue/verify.sh` → `AGENTS.md` (depends: T13, T14)
- [ ] T35: Verify `bash sprue/verify.sh` still passes in the source repo (platform-dev mode). Document any exceptions for platform-repo mode vs instance mode → manual test (depends: T16, T34)

## Acceptance Criteria

- [ ] AC1: `pip install -e .` succeeds from a clean checkout with no errors — **spec: installable without cloning**
- [ ] AC2: `sprue init test-kb` produces a directory containing `.sprue/`, `instance/identity.md`, `instance/config.yaml`, `raw/`, `wiki/`, `notebook/`, `inbox/`, `memory/`, `state/`, `AGENTS.md`, `README.md`, `.gitignore` — **spec: single-command init**
- [ ] AC3: `sprue verify` in the freshly init'd directory passes with zero violations — **spec: defaults produce valid instance**
- [ ] AC4: `sprue init test-kb` in a directory with existing `.sprue/` fails with error message containing "already exists" — **spec: init idempotency**
- [ ] AC5: `sprue init test-kb --force` in a directory with existing `.sprue/` succeeds and overwrites — **spec: init idempotency (force override)**
- [ ] AC6: `sprue upgrade` in an init'd directory replaces `.sprue/` contents; `instance/`, `wiki/`, `raw/`, `memory/`, `state/` are byte-identical before and after — **spec: upgrades preserve instance content**
- [ ] AC7: Kill `sprue upgrade` mid-execution (e.g., SIGTERM during copy) — the instance remains usable with the previous `.sprue/` intact — **spec: upgrade atomicity**
- [ ] AC8: `sprue verify` works in both source-repo mode (this repo, `sprue/` layout) and instance mode (a `sprue init`'d directory, `.sprue/` layout) — **spec: CLI + agent dual entry points**
- [ ] AC9: Built wheel (from `hatchling build`) contains `sprue/engine/` files; does NOT contain `instance/`, `docs/`, `wiki/`, `raw/`, `memory/`, `notebook/`, `inbox/` — `check-package-contents.py` passes — **spec: engine contains no instance content**
- [ ] AC10: An instance's `config.yaml` with `schema_version: 999` causes `sprue verify` to fail with a schema compatibility error — **spec: schema compatibility window**
- [ ] AC11: LLM agent reading `.sprue/engine.md` from a user instance can follow the boot chain: `AGENTS.md` → `.sprue/engine.md` → `.sprue/protocols/` — all paths resolve — **spec: engine files locally readable by LLM**
- [ ] AC12: `sprue upgrade` when package version matches `.sprue-version` prints "Already up to date" and exits 0 — **spec: explicit upgrade**
- [ ] AC13: `sprue upgrade` when `schema_version` has changed prints migration instructions to stdout — **spec: schema compatibility window (migration tooling)**
- [ ] AC14: Multiple `sprue init` invocations in different directories produce independent instances sharing the same pip-installed engine — **spec: multiple instances coexist**
- [ ] AC15: `bash sprue/verify.sh` passes in the source repo (or documented exception for platform-repo mode) — **backwards compatibility**
- [ ] AC16: Every spec invariant in `docs/specs/platform-distribution.md` maps to at least one AC above or a passing test — **traceability**
- [ ] AC17: Copy a `sprue init`'d directory to a second machine with the same engine version installed and run `sprue verify` — passes without reconfiguration — **spec: portability**
- [ ] AC18: `find <instance>/.sprue -type f` returns only plain-text files (no binaries); `git add .sprue/` produces human-readable diffs — **spec: git-committable engine files**
- [ ] AC19: `grep -rE '^import (requests|urllib|http|socket|aiohttp|httpx)' src/sprue/` returns zero matches outside explicitly allowed modules (documented exceptions listed in the spec's Enforcement table) — **spec: no network requests**

## Testing

Tests live in `tests/` at the repo root. Framework: `pytest` (added as a dev dependency in T1 via `[project.optional-dependencies] dev = ["pytest", "pytest-click"]`).

- Integration tests spawn `sprue init` / `sprue upgrade` / `sprue verify` via `subprocess` and `click.testing.CliRunner`, operating on temp directories via `pytest.fixture(tmp_path)`.
- AC7 (kill mid-upgrade) uses `subprocess.Popen` + `SIGTERM` with assertions on post-kill `.sprue/` integrity.
- AC9 (wheel contents) runs `hatchling build` in a tempdir and uses `zipfile.ZipFile` to inspect the produced wheel.
- AC11 (LLM boot chain) is validated by a test that reads `.sprue/engine.md` and asserts referenced files exist at expected paths.
- Manual test ACs (T7, T16, T31, T32, T35) are run by the implementing agent with output captured in the PR description.

## Non-Goals

These are explicitly out of scope for this plan:

- **Automated migration scripts.** v1 prints guided instructions when `schema_version` changes. Automated migration is deferred per ADR-0033 until the schema surface area justifies the investment.
- **PyPI publishing of v1.** The release workflow (T30) is scaffolded but actual PyPI publication is deferred until dogfooding (T32) passes and the maintainer explicitly tags a release.
- **3-way merge on upgrade.** `sprue upgrade` overwrites `.sprue/` wholesale. Users who modified engine files use `git diff` to reconcile. A smarter merge can be added later if user demand warrants it (design doc acknowledges this trade-off).
- **`sprue status` command.** Referenced in the design doc's CLI section but not required by any spec invariant. Deferred to a separate plan.
- **Windows support.** Shell scripts (verify.sh, reset.sh) assume Unix. Windows compatibility is a separate effort.
- **Namespace packages or plugin architecture.** The engine is a single package. Extensibility is not a v1 goal.

## Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Engine root refactor (~549 path refs across ~72 files; scripts + protocols + engine.md + prompts) breaks validators or protocols silently | High — broken paths cause runtime failures the LLM cannot diagnose | Medium | Route ALL path resolution through `engine_root()` / `instance_root()` (T8). Never find-and-replace raw strings. Run full verify suite after each batch of file updates (T16). Audit (T10) produces a complete checklist before any bulk changes. |
| `importlib.resources.files()` returns `Traversable` not `Path` — `shutil.copytree` may not accept it directly | Medium — blocks init command | Low | Use `as_file()` context manager to materialize to a real filesystem path before copying (per design doc). Test this in T17 before building on it. |
| Source repo verify.sh breaks after restructure | High — blocks all development | Medium | Keep verify.sh working throughout by updating it incrementally (T12). T16 is a gate — do not proceed to Phase C until verify passes. |
| Atomic upgrade via rename fails on cross-filesystem moves (e.g., temp on different mount) | Medium — upgrade leaves partial state | Low | Use `tempfile.mkdtemp(dir=instance_root)` to ensure temp dir is on the same filesystem as `.sprue/`. Test in T22. |
| Click dependency conflicts with user's existing environment | Low — click is widely compatible | Low | Pin minimum version only (`click>=8.0`), no upper bound. Document in pyproject.toml. |

## Dependency Graph

```
Phase A: T1 → T2 → T3, T4, T5, T6 → T7
Phase B: T8 → T9, T8 → T10, T9 + T10 → T11 → T16
         T8 → T12 → T16
         T2 → T13, T14, T15 → T16
Phase C: T4 + T8 → T17 → T18, T19, T20
         T8 + T17 → T21 → T22
         T8 + T11 → T23
         T17 + T21 + T23 → T24
Phase D: T9 → T25, T2 → T26, T6 → T27 → T28
Phase E: T23 + T27 → T29, T6 → T30, T6 + T27 → T31
Phase F: T24 → T32, T24 → T33, T13 + T14 → T34, T16 + T34 → T35
```

Phases are sequential: A before B, B before C, D can overlap with C. E depends on C+D. F is last.
