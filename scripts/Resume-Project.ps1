[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [ValidateSet('codex','claude','antigravity','hermes','openclaude','all')][string]$Agent='codex',
    [switch]$DryRun
)
$ErrorActionPreference='Stop'
$arguments = @('resume', $ProjectPath, '--agent', $Agent)
if ($DryRun) { $arguments += '--dry-run' }
& aiwh @arguments
if ($LASTEXITCODE -ne 0) { throw 'Project continuity scan failed' }
