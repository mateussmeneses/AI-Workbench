[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [ValidateSet('codex','claude','antigravity','hermes','openclaude','all')][string]$Agent='codex',
    [string]$Profile,
    [switch]$DryRun
)
$ErrorActionPreference='Stop'
$arguments = @('init', $ProjectPath, '--create', '--agent', $Agent)
if ($Profile) { $arguments += @('--profile', $Profile) }
if ($DryRun) { $arguments += '--dry-run' }
& aiwh @arguments
if ($LASTEXITCODE -ne 0) { throw 'Project bootstrap failed' }
