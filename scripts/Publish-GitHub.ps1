# Run from the root of the extracted AI Workbench repository.
param([string]$Repository = "mateussmeneses/ai-workbench")
$ErrorActionPreference = 'Stop'
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'Install GitHub CLI (gh) and run gh auth login' }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Install Git for Windows' }
py -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed; refusing publication' }
gh auth status
if ($LASTEXITCODE -ne 0) { throw 'GitHub authentication is required' }
if (-not (Test-Path .git)) { git init; git branch -M main }
git add .github .gitignore LICENSE README.md AGENTS.md CODEX_START_HERE.md CONTRIBUTING.md SECURITY.md CHANGELOG.md pyproject.toml src tests capabilities config docs scripts
if ($LASTEXITCODE -ne 0) { throw 'Git staging failed' }
git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw 'Whitespace or conflict markers detected' }
git status --short
Write-Host 'Review staged files before running this publisher. No secrets or private catalogs should be committed.'
if ((git diff --cached --name-only).Count -gt 0) { git commit -m 'feat: AI Workbench universal domain registry and project continuity' }
if ($LASTEXITCODE -ne 0) { throw 'Git commit failed' }
gh repo view $Repository *> $null
if ($LASTEXITCODE -ne 0) {
  gh repo create $Repository --public --source . --remote origin --push
  if ($LASTEXITCODE -ne 0) { throw 'Repository creation failed' }
} else {
  if (-not (git remote)) { git remote add origin "https://github.com/$Repository.git" }
  git push -u origin main
  if ($LASTEXITCODE -ne 0) { throw 'Push failed' }
}
Write-Host "Pushed: https://github.com/$Repository"
$tag = 'v0.3.0'
# Tag only the exact verified local main commit. GitHub Actions re-verifies
# this tag and creates the release; this script never bypasses CI.
git rev-parse -q --verify "refs/tags/$tag" *> $null
if ($LASTEXITCODE -ne 0) {
  git tag -a $tag -m "AI Workbench $tag"
  if ($LASTEXITCODE -ne 0) { throw 'Unable to create release tag' }
}
git push origin $tag
if ($LASTEXITCODE -ne 0) { throw 'Tag push failed; source on main may already be published' }
Write-Host "Release workflow triggered for $tag. Verify https://github.com/$Repository/actions"

