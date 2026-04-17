---
status: accepted
date: 2026-04-16
implements:
  - platform-distribution
  - platform-reusability
---
# Sprue Distribution Model

The platform is distributed as a pip-installable Python package. Installation provides a CLI for scaffolding and mechanical operations. The engine's markdown files are copied into each instance as a local `.sprue/` directory, keeping them readable by the LLM agent at runtime.

## Revision Note

This revision reconciles the automated-migration language between the spec and design. The previous spec stated "schema changes are backward-compatible or include automated migration," implying fully automated migration from day one. The revised spec (platform-distribution) now states: "Schema changes are backward-compatible within a compatibility window, or include migration tooling. Migration tooling may be automated or guided instructions produced by the CLI." This design implements that policy as follows: for v1, migration tooling takes the form of printed guided instructions; automated migration scripts may be added in later versions per the compatibility window policy. This is a deliberate simplification — full automated migration is deferred until the schema surface area justifies the investment.

## Specs

- [Platform Distribution](../specs/platform-distribution.md) — product invariants for distribution
- [Platform Reusability](../specs/platform-reusability.md) — domain-agnostic engine, identity-driven customization

## Context

The platform is 64% markdown (protocols, engine.md, prompts, defaults.yaml) and 20% Python (scripts). The primary consumer of the markdown is an LLM agent that reads files from disk. This creates a fundamental tension: pip packages install into site-packages (opaque to LLMs), but the LLM needs local, browsable files.

Three distribution models were evaluated:

**Pure pip** — everything in site-packages, accessed via `importlib.resources`. Clean install, standard tooling. But the LLM cannot browse site-packages to find engine.md, and path resolution in `config.py` breaks when scripts live in site-packages while content lives in the user's working directory.

**Git submodule** — engine as a submodule at `.sprue/` in each instance. Files are local and visible. But submodules are painful for non-git-expert users, and the update workflow is error-prone.

**Hybrid: pip CLI + local file copy** — pip installs a thin CLI; `sprue init` copies engine files into the instance. Files are local, LLM-readable, and the existing architecture is largely preserved. Upgrades are explicit via `sprue upgrade` (per spec invariant: engine upgrades are user-initiated). This is the Copier model — scaffold locally, track template version, update explicitly.

The hybrid model was chosen because it preserves the existing architecture, keeps files visible to the LLM, and makes upgrades deliberate rather than silent.

## Architecture

### Package Contents

The pip package (`pip install sprue`) contains:

- **CLI entry point** — `sprue` command with subcommands (`init`, `verify`, `status`, `upgrade`)
- **Engine bundle** — all files that get copied into instances (protocols, scripts, defaults.yaml, engine.md, prompts, schemas, profiles, verify.sh, reset.sh)
- **Templates** — scaffolding templates for instance files (AGENTS.md, README.md, identity.md, config.yaml, .gitignore)

The package does NOT contain: wiki content, raw sources, memory state, instance identity, ADRs, specs, design docs, or plans. Those belong to either the instance (content/state) or the source repo (contributor docs).

**Enforcement of "no instance content in engine" (per spec invariant):** The `pyproject.toml` package inclusion rules explicitly list only `src/sprue/` contents. An optional CI check (`scripts/check-package-contents.py`) asserts that no instance paths (`wiki/`, `raw/`, `memory/`, `instance/`) appear in the built wheel.

Engine files are included via hatchling's auto-inclusion of files within the package directory. The CLI uses `importlib.resources.files()` (Python 3.9+) to locate bundled files during `init` and `upgrade`, then copies them to the target directory. `pkg_resources` is not used — it is deprecated.

### Python Packaging

Per 2026 best practices (comparable to dbt-core and pre-commit packaging patterns):

- **Build backend**: hatchling. Chosen for clean `pyproject.toml` configuration and reliable non-Python file inclusion.
- **Runtime file access**: `importlib.resources.files("sprue.engine")` returns `Traversable` references to bundled files. Use `as_file()` context manager when a real filesystem path is needed for copying.
- **File inclusion**: Engine files live inside the package directory (`src/sprue/engine/`) so they are automatically included in wheels. No `data_files` (deprecated), no `MANIFEST.in` hacks.
- **Entry point**: `[project.scripts] sprue = "sprue.cli:main"`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "sprue"
requires-python = ">=3.10"
dependencies = ["click", "pyyaml"]

[project.scripts]
sprue = "sprue.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/sprue"]
```

### Instance Layout

After `sprue init my-kb`:

```
my-kb/
  .sprue/                  ← engine files (copied from package, managed by sprue upgrade)
    engine.md
    defaults.yaml
    protocols/
    scripts/
    prompts/
    schemas/
    profiles/
    verify.sh
    reset.sh
    README.md
    .sprue-version         ← tracks which package version was copied
  instance/
    identity.md            ← user's one-sentence identity (prompted during init)
    config.yaml            ← empty (platform defaults apply)
  wiki/
  raw/
  notebook/
  inbox/
  memory/
  AGENTS.md                ← generated, points to .sprue/engine.md
  README.md                ← generated from identity
  .gitignore               ← generated, ignores inbox/*, build artifacts
```

The `.sprue/` directory is hidden (convention: "managed by the tool"). The LLM reads `.sprue/engine.md` and `.sprue/protocols/*.md` as local files. Note: `ls` won't show `.sprue/` by default and some editors hide dotfiles — this is an intentional signal that the directory is tool-managed, but users should be told about it during init.

Per spec invariant (git-committable engine files): `.sprue/` is committed to git. This ensures instances are portable (clone and run) and upgrades are visible in version history. The trade-off is noisier diffs on upgrade — acceptable because upgrades are infrequent and deliberate.

### Source Repo vs Distributed Instances

The source repo (`lastmile-kb`) keeps `sprue/` as a visible top-level directory for development. Distributed instances use `.sprue/` (hidden). The mapping:

| Source repo | Distributed instance |
|---|---|
| `sprue/` (visible, editable) | `.sprue/` (hidden, managed) |
| `docs/` (contributor docs) | Not present |
| `instance/` (this KB's config) | `instance/` (user's config) |
| `wiki/`, `raw/`, etc. (this KB's content) | `wiki/`, `raw/`, etc. (user's content) |

The source repo is both a development workspace for the platform AND a running KB instance. Contributors work on `sprue/` directly. The `sprue init` command reads from the installed package, not from the source repo.

### Dual Entry Points

**CLI mode** — for mechanical operations:

```bash
sprue init my-kb           # scaffold a new instance
sprue verify               # run all validation rules
sprue status               # show KB stats, compile queue, inbox count
sprue upgrade              # update .sprue/ to latest package version
```

**Agent mode** — for knowledge work:

The LLM agent reads `AGENTS.md` → `.sprue/engine.md` → dispatches to `.sprue/protocols/*.md`. All intelligent operations (compile, expand, query, verify content) run through the agent. The agent calls `.sprue/scripts/*.py` and `bash .sprue/verify.sh` as subroutines.

The division: CLI handles what can be computed; the agent handles what requires understanding. Both share the same config loader and defaults.

### Config Resolution

`config.py` resolves two roots:

- **Engine root** — `.sprue/` in the instance directory. Contains `defaults.yaml` and all platform files.
- **Instance root** — the instance directory itself. Contains `instance/config.yaml`, `wiki/`, `raw/`, `memory/`.

The deep-merge model is unchanged: `defaults.yaml` (from `.sprue/`) merged with `config.yaml` (from `instance/`), instance wins. Scripts find their root by walking up from their own location (`.sprue/scripts/` → `.sprue/` → instance root).

### Upgrade Model

Upgrades use an overwrite-with-warning model and are always user-initiated (per spec invariant: explicit upgrade). When the user runs `sprue upgrade`:

- The CLI compares the installed package version against `.sprue/.sprue-version`.
- If newer, it copies new engine files to a temporary directory first, then replaces `.sprue/` contents. If the copy fails or is interrupted, the original `.sprue/` remains intact (per spec invariant: upgrade atomicity).
- Any locally modified files (detected via content hash comparison against the previous version's known hashes) trigger a warning listing the modified files, so the user can review the diff in git.
- `.sprue-version` is updated.
- `sprue verify` runs automatically to confirm the upgrade didn't break anything.
- If `schema_version` in `defaults.yaml` changed, the CLI produces migration tooling. For v1, migration tooling takes the form of printed guided instructions; automated migration scripts may be added in later versions per the compatibility window policy. This is a deliberate v1 simplification.

This is simpler than a full 3-way merge. Users who haven't modified `.sprue/` files get clean upgrades. Users who have local modifications get warned and can use `git diff` to reconcile. A full 3-way merge can be added later if user demand warrants it.

### Schema Compatibility

Per spec invariant (version compatibility contract): the engine declares a `schema_version` in `defaults.yaml`, incremented independently of the package version (SemVer). Major = breaking schema changes, Minor = new features, Patch = fixes.

**Enforcement of schema backward-compat (per spec invariant):** `check-config.py` can include a schema compatibility assertion that validates the instance's `schema_version` against the engine's supported range. This catches version mismatches at `sprue verify` time rather than at runtime failure.

### Migration Surface

Moving from the current `sprue/` layout to `.sprue/` in distributed instances requires updating path references. The current codebase has ~76 hardcoded `sprue/` references across:

- 18 Python scripts (path construction, comments, docstrings, error messages)
- 15 protocols (instructions like `bash sprue/verify.sh`, `read sprue/engine.md`)
- ~38 references in engine.md
- ~5 references in AGENTS.md

These references must be parameterized or updated to use `.sprue/` in distributed instances. The implementation plan must account for this migration surface. Options: (a) make all paths relative within `.sprue/` so the directory name doesn't matter, (b) update all references to `.sprue/` and use symlinks in the source repo, (c) use a path variable resolved at runtime.

### Spec Invariant Coverage

| Spec Invariant | How Addressed |
|---|---|
| Installable without cloning | `pip install sprue` |
| Single-command init passes verify | `sprue init my-kb` prompts for identity only; runs `sprue verify` post-init |
| Defaults produce valid instance | Empty `config.yaml` generated, defaults.yaml provides all values |
| Optional/minimal instance config | Deep-merge model, instance overrides only what differs |
| Upgrades preserve instance content | `.sprue/` is engine-only; `instance/`, `wiki/`, `raw/`, `memory/` are never touched by upgrade |
| Upgrade atomicity | Temp-dir write + atomic replace; interrupted upgrade preserves previous state |
| Explicit upgrade | No auto-upgrade code path; `sprue upgrade` is the only mechanism |
| Schema compatibility window | `schema_version` in defaults.yaml; `check-config.py` validates range |
| Artifact integrity | Reproducible hatchling builds; diffable against source repo tags |
| Init idempotency | `sprue init` refuses if `.sprue/` exists; requires `--force` to overwrite |
| Engine contains no instance content | Package inclusion rules in `pyproject.toml` + optional CI check |
| Multiple instances coexist | Each instance has its own `.sprue/` directory; no shared state between instances; single pip install serves all |
| CLI + agent dual entry points | CLI for mechanical ops, agent for knowledge work |
| Engine files locally readable by LLM | `.sprue/` is a local directory with plain files |
| No network requests | CLI commands are offline after pip install; `sprue upgrade` requires a prior `pip install --upgrade` (no phone-home) |
| Instances are portable | `.sprue/` committed to git; clone the repo and the engine is present; same sprue version must be installed for CLI commands |
| Git-committable engine files | All `.sprue/` files are plain text; users commit to preserve engine-version reproducibility |

### Packaging

- **Package name**: `sprue` on PyPI
- **Build backend**: hatchling (see Python Packaging section above)
- **Python**: ≥3.10
- **Runtime dependencies**: `pyyaml`, `click`
- **Optional dependencies**: `sentence-transformers`, `numpy` (for semantic search)
- **Entry point**: `[project.scripts] sprue = "sprue.cli:main"` in `pyproject.toml`
- **Engine files**: inside `src/sprue/engine/` — bundled automatically by hatchling wheel build
- **Runtime access**: `importlib.resources.files("sprue.engine")` — no `pkg_resources`
- **Template rendering**: simple `{{variable}}` string substitution (no Jinja2 dependency)
- **Versioning**: SemVer. `schema_version` in defaults.yaml increments independently (only on config structure changes)

### Error Handling

- `sprue init` in a directory with existing `.sprue/` → error: "Instance already exists. Use `sprue upgrade` to update the engine, or `sprue init --force` to reinitialize." (Per spec invariant: init idempotency.)
- `sprue upgrade` with no `.sprue/` → error: "Not a sprue instance. Run `sprue init` first."
- `sprue upgrade` when package version matches `.sprue-version` → message: "Already up to date."
- `sprue verify` outside a sprue instance → error: "No .sprue/ directory found. Run from inside a sprue instance."
- `sprue init` with no identity provided → prompt interactively; if non-interactive (piped), error with usage hint.

## Interfaces

| Component | Reads | Writes |
|---|---|---|
| `sprue init` | Package bundle, user input (identity) | `.sprue/`, `instance/`, `AGENTS.md`, `README.md`, `.gitignore`, empty dirs |
| `sprue upgrade` | Package bundle, `.sprue/.sprue-version` | `.sprue/` contents, `.sprue-version` |
| `sprue verify` | `.sprue/scripts/verify.py`, `memory/rules.yaml`, `wiki/` | stdout (pass/fail report) |
| `sprue status` | `instance/state/`, `wiki/.index/manifest.yaml`, `inbox/` | stdout (stats report) |
| LLM agent | `AGENTS.md` → `.sprue/engine.md` → `.sprue/protocols/` | `wiki/`, `raw/`, `instance/state/`, `memory/` |
| `config.py` | `.sprue/defaults.yaml`, `instance/config.yaml` | nothing (pure reader) |

## Decisions

- [ADR-0006: Configuration Layering](../decisions/0006-configuration-layering.md)
- [ADR-0007: Platform/Instance Architecture](../decisions/0007-platform-instance-architecture.md)
- [ADR-0030: Rename platform/ to sprue/, Split Contributor Docs](../decisions/0030-rename-platform-to-sprue-split-docs.md)
- [ADR-0031: Product Name — Sprue](../decisions/0031-product-name-sprue.md)
