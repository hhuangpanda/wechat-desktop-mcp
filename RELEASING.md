# Releasing

The version comes from the git tag. No files need a version bump.

1. Commit and push to `main`, and wait for the Tests workflow to pass.
2. Tag and push the tag:

   ```bash
   git tag v1.2.0
   ```

   ```bash
   git push origin v1.2.0
   ```

3. In the repo's Actions tab, open the Release run, then **Review deployments** > **Approve and deploy**. This publishes to PyPI, then the MCP Registry and a GitHub Release follow on their own.

Use `vMAJOR.MINOR.PATCH`: patch for fixes, minor for new features, major for breaking changes.

## Mistakes

- A tag that isn't `vX.Y.Z` (such as `v1.2`) stops the workflow before building.
- To redo a tag before approving the PyPI job: `git tag -d v1.2.0`, then `git push origin :refs/tags/v1.2.0`, then tag again.
- A version already on PyPI can never be uploaded again, even after deleting it. Fix it with a new patch release.
