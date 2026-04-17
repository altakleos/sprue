# Release Playbook

Operational procedures for releasing Sprue and handling incidents.

## Normal Release

1. Ensure `main` is green (CI verified across Python 3.10–3.13).
2. Tag a semver release from `main`:
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```
3. The `release.yml` workflow triggers. It:
   - Runs the full verify gate (pytest + smoke test + wheel build + package-contents check)
   - Pauses on the `pypi` GitHub Environment for your manual approval
   - On approval, publishes wheel + sdist to PyPI via OIDC trusted publishing
4. Verify the release is live:
   ```bash
   pip index versions sprue
   ```
5. Create a GitHub Release on the tag with notes.

**Tag patterns the workflow matches:** `v1.2.3`, `v0.1.0-alpha`, `v0.1.0-rc.1`, `v0.1.0a1`, `v0.1.0b2`.

## Pre-release (alpha / beta / rc)

Same flow as normal release with a prerelease suffix:

```bash
git tag v0.2.0-alpha
git push origin v0.2.0-alpha
```

Users must pass `--pre` to pip to install prereleases:

```bash
pip install sprue --pre
```

## Yanking a Bad Release

A **yank** hides a release from `pip install sprue` (without a pinned version) but leaves it installable for anyone who pinned to that specific version. Yank when a release has a correctness bug but is not actively harmful.

1. Log in to PyPI: https://pypi.org/manage/project/sprue/releases/
2. Find the release, click **Options → Yank**
3. Enter a short reason (shown to users who pinned to the yanked version)
4. Confirm

**When to yank vs delete:** Always yank first. Delete only if the release contains secrets or malicious code (deletion is permanent and breaks anyone with a pinned version). PyPI does not allow re-uploading a deleted version.

## Issuing a Patch

After yanking (or instead of yanking for quick fixes):

1. Fix on `main` via a normal PR (follow the 6-layer stack in `AGENTS.md`).
2. Bump the version in `src/sprue/__init__.py`:
   ```python
   __version__ = "0.1.2"  # was 0.1.1
   ```
3. Commit, tag, push — same flow as Normal Release.
4. If the previous release was yanked, optionally update the yank message to point at the fix version.

## Incident Response

### Release workflow failed before publish

The `verify` job failed. Fix the failure, push a new commit to main, delete the bad tag, re-tag:

```bash
git tag -d v0.1.1                 # delete local
git push origin :v0.1.1           # delete remote
# ... fix and push to main ...
git tag v0.1.1
git push origin v0.1.1
```

### Release workflow failed at publish step

- Check the Actions UI for the specific error.
- Common causes:
  - PyPI trusted publisher not configured → configure at https://pypi.org/manage/account/publishing/ and re-run the workflow
  - Environment `pypi` not approved → click **Review deployments** in the Actions UI
  - Version already exists on PyPI → PyPI forbids re-uploading the same version; bump and re-tag
- The workflow is idempotent: re-running after a transient failure is safe because PyPI refuses duplicate uploads rather than creating conflicts.

### Corrupt wheel discovered in production

1. **Yank immediately** (see Yanking a Bad Release above).
2. Fix, bump version, release as a patch.
3. Announce on the GitHub Release page for the yanked version — link to the fix.

### PyPI account compromised

1. Reset PyPI password and 2FA from a clean device.
2. Review trusted publishers: https://pypi.org/manage/project/sprue/settings/publishing/ — remove any unfamiliar entries.
3. Review PyPI account activity for unauthorized publishes. Yank anything unauthorized.
4. Rotate any GitHub personal access tokens.
5. Open a GitHub issue or security advisory to disclose.

## Upgrade Cleanup (M5)

`sprue upgrade` sweeps stale `.sprue.old.*` and `tmp*` directories from a prior interrupted run on every invocation. No manual cleanup is needed after a SIGKILL'd upgrade — the next `sprue upgrade` run (including an "already up to date" no-op) reclaims them automatically.

## Rollback: Users on a Bad Version

A user who installed a bad release can downgrade:

```bash
pip install 'sprue==0.1.0' --force-reinstall --pre
```

Their `.sprue/` directory was left untouched by the bad CLI (per upgrade atomicity), so their instance content is intact. If they ran `sprue upgrade` mid-flight on a broken version, the atomic-swap guarantees the previous `.sprue/` is preserved.

## Pre-release Checklist

Before tagging:

- [ ] CI green on `main`
- [ ] `CHANGELOG.md` updated (if maintained)
- [ ] Version bumped in `src/sprue/__init__.py`
- [ ] `docs/plans/` has no `status: in-progress` plans that should block
- [ ] `pytest` passes locally
- [ ] `python -m build && python src/sprue/engine/scripts/check-package-contents.py` passes
- [ ] GitHub Environment `pypi` reviewers still exist and are reachable

## Approving PyPI Publish from the Terminal

The `pypi` GitHub Environment requires reviewer approval. The `gh` CLI
cannot approve deployments directly, but the API can:

```bash
# Find the run ID for the release
gh run list --workflow=release.yml --limit 3

# Check pending deployment (confirms it's waiting)
gh api repos/altakleos/sprue/actions/runs/<RUN_ID>/pending_deployments

# Approve
gh api repos/altakleos/sprue/actions/runs/<RUN_ID>/pending_deployments \
  --method POST \
  --field 'environment_ids[]=14249430246' \
  --field 'state=approved' \
  --field 'comment=Ship it'
```

The environment ID `14249430246` is stable (the `pypi` environment).
Only the run ID changes per release.

## References

- Distribution spec: [docs/specs/platform-distribution.md](../specs/platform-distribution.md)
- Release workflow: [.github/workflows/release.yml](../../.github/workflows/release.yml)
- PyPI trusted publisher setup: [ADR-0033](../decisions/0033-sprue-distribution-model.md)
- PyPI yank documentation: https://pypi.org/help/#yanked
