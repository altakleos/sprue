This is the Sprue platform repository. You are a contributor developing the engine.

On EVERY session start, before responding to any user message:
1. Read `AGENTS.md` — contributor boot document.
2. Read `docs/development-process.md` — the 6-layer stack and ADR-lite format.

Key rules:
- Follow the 6-layer stack: Specs → Design → ADRs → Plans → Protocols → Config/Validators.
- Protocol behavioral changes need an ADR-lite (ADR-0035). Architectural changes need a full ADR.
- Every change ends with `sprue verify` or `pytest`.
- Commit atomically. Push to feature branches. PR to main.

Layer gate (MANDATORY before writing code):
- Before modifying any file in `src/`, check: does a plan exist in `docs/plans/` for this work?
- If the task touches 3+ files or spans multiple layers → a plan is REQUIRED.
- If no plan exists → create one first, following the template in `docs/plans/README.md`.
- If a plan exists → read it, confirm which phase/task you are executing, and update it when done.

Publish workflow (when user says "publish"):
1. Bump version in `src/sprue/__init__.py` (e.g., 0.1.15a1 → 0.1.16a1).
2. Run `pytest -v -m "not slow"` to verify.
3. Build wheel: `python3 -m build --wheel` then `python3 src/sprue/engine/scripts/check-package-contents.py`.
4. Commit: `git commit -am "Bump version to X"` and `git push`.
5. Tag: `git tag vX && git push origin vX` — triggers the Release workflow.
6. Wait ~15s, then check: `gh run list --limit 2`.
7. The `publish` job requires environment approval. Approve it:
   ```
   gh api repos/altakleos/sprue/actions/runs/<RUN_ID>/pending_deployments
   ```
   Extract the environment ID, then:
   ```
   gh api repos/altakleos/sprue/actions/runs/<RUN_ID>/pending_deployments \
     --method POST \
     --field 'environment_ids[]=<ENV_ID>' \
     --field 'state=approved' \
     --field 'comment=<version>: <summary>'
   ```
8. Poll until publish completes: `gh run view <RUN_ID> --json jobs --jq '.jobs[] | {name, status, conclusion}'`
9. If the release fails: delete the tag (`git tag -d vX && git push origin --delete vX`), fix the issue, retag, and repeat from step 5.
10. Confirm: `pip install sprue==X --pre` or check PyPI.
