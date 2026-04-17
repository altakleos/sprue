# Changelog

All notable changes to Sprue are recorded here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning
per [PEP 440](https://peps.python.org/pep-0440/).

## [0.1.1a1] — 2026-04-17

### Added
- `check-sources.py` validator enforcing ADR-0028 provenance (LLM-authored
  `provenance: sourced` pages must declare non-empty `sources:` frontmatter).
- `lib.py` shared utilities module (`SKIP_DIRS`, `SKIP_FILES`,
  `parse_frontmatter`, `find_wiki_pages`, `normalize_relationship_types`).
- `docs/operations/release-playbook.md` — operational procedures for
  releases, yanks, and incidents.
- Stale-artifact sweep in `sprue upgrade` — cleans leftover `.sprue.old.*`
  and `tmp*` dirs from SIGKILL-interrupted prior runs.
- "How Plans Are Executed" section in `docs/development-process.md`
  documenting the streaming / decision / destructive execution modes.

### Changed
- `SKIP_DIRS` unified across all 9 engine scripts — fixes the drift where
  `check-frontmatter.py` and `verify.py` saw different page sets than the
  other 7 scripts.
- `sprue upgrade` now uses range-based schema compatibility
  (`supported_schema_versions` window) with graceful fallback to exact
  match for engines that predate the window declaration.
- `sprue upgrade` refuses to operate on a symlinked `.sprue/` directory
  (prevents silently trashing shared engine targets).
- README install flow now reflects live PyPI availability;
  `pip install sprue --pre` is the primary install path.

### Fixed
- `pyproject.toml` project URLs corrected to `github.com/altakleos/sprue`.
- `validate-raw.py` stale path reference (`ops/state/imports.yaml` →
  `instance/state/imports.yaml`).
- `check-config.py` now validates `supported_schema_versions.min <= max`.

### Deprecated
- `verify-content.py` emits a `DeprecationWarning` at import; replaced by
  the LLM-driven verify protocol (`.sprue/protocols/verify.md`).

## [0.1.0] — 2026-04-16

Initial alpha release.

### Added
- `pip install sprue` distribution model (ADR-0033): hatchling-built wheel
  with `importlib.resources` at runtime, CLI entry point via click.
- `sprue init <dir>` — scaffolds a complete KB instance with engine files
  at `.sprue/`, identity prompt, template rendering, and instance
  directories.
- `sprue upgrade [dir]` — atomic engine replacement via same-filesystem
  temp dir + double-rename with rollback. Preserves instance content.
- `sprue verify` — pass-through to the engine's rule-based validator.
- `src/sprue/engine_root.py` — four-priority resolver for engine and
  instance paths (env var, `.sprue/`, source repo, installed wheel).
- `check-package-contents.py` — build-time validator asserting wheels
  contain no instance paths (`wiki/`, `raw/`, `memory/`, etc.).
- CI workflow across Python 3.10–3.13 with pip caching; release workflow
  via PyPI trusted publishing (OIDC, no secrets).
- Pytest test suite covering init, upgrade, schema validation, package
  contents, and CLI integration.

### Structure
- `src/sprue/engine/` — domain-agnostic engine (protocols, scripts,
  prompts, schemas, profiles, defaults.yaml, engine.md).
- `src/sprue/templates/` — instance scaffolding templates for
  `sprue init`.
- `docs/` — six-layer stack artifacts (specs, design, decisions, plans).
