# Publishing to GitHub

AI Workbench has not been pushed to the user's GitHub by the assistant because the connected GitHub integration does not expose repository creation. The source is ready for publication using GitHub CLI on Windows.

```powershell
cd C:\projetos\AI-Workbench
py -m pip install -e .
py -m unittest discover -s tests -v
.\scripts\Publish-GitHub.ps1 -Repository mateussmeneses/ai-workbench
```

The script checks tests and GitHub authentication, stages the explicitly allowlisted source paths, creates a public repository if missing, or pushes `main` to an existing remote. Review `git status` and staged files before publication. Private browser bookmarks, stars catalog, local handoffs, tokens and credentials must not be committed. The script pushes a `v0.3.0` tag. `.github/workflows/release.yml` runs tests on the tag and creates the GitHub release only if verification passes. Inspect GitHub Actions for the outcome.
