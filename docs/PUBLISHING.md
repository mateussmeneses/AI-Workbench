# Publishing releases

The repository is published at `mateussmeneses/AI-Workbench`. Regular changes are pushed to `main` after tests pass:

```powershell
py -m unittest discover -s tests -v
git push
```

For a release, `scripts/Publish-GitHub.ps1` checks tests and GitHub authentication, stages only allowlisted source paths and pushes `main` plus a version tag. `.github/workflows/release.yml` runs tests on the tag and creates the GitHub release only if verification passes. Private browser bookmarks, the stars catalog, local handoffs, tokens and credentials must never be committed.
