<#
.SYNOPSIS
Creates or attaches a project, selecting private AI Workbench references.
.DESCRIPTION
Opt-in wrapper: no global hooks, no clones, and no MCP activation.
A path is created only when -Create is specified. Existing paths are kept intact.
.EXAMPLE
.\scripts\New-AIWorkbenchProject.ps1 -ProjectPath 'C:\projetos\meu-app' -Create
.EXAMPLE
.\scripts\New-AIWorkbenchProject.ps1 -ProjectPath 'C:\projetos\theorder1886-port' -DryRun
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [switch]$Create,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$target = [IO.Path]::GetFullPath($ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ProjectPath))
if (-not (Test-Path -LiteralPath $target -PathType Container)) {
    if (-not $Create) { throw "A pasta nao existe. Use -Create para criar: $target" }
    if (-not $DryRun) { New-Item -ItemType Directory -Path $target -Force | Out-Null }
    Write-Host "Pasta a criar: $target"
}
if ($DryRun -and -not (Test-Path -LiteralPath $target)) {
    Write-Host 'DryRun: nada gravado. Crie o diretorio antes de testar a analise real.'
    exit 0
}
if (-not (Get-Command aiwh -ErrorAction SilentlyContinue)) {
    throw 'Instale o Hub primeiro: py -m pip install -e . (no diretorio ai-workbench-hub).'
}
$argsCli = @('attach', '--project', $target)
if ($DryRun) { $argsCli += '--dry-run' }
& aiwh @argsCli
if ($LASTEXITCODE -ne 0) { throw "aiwh attach falhou: $LASTEXITCODE" }
Write-Host 'Concluido. O indice .ai-workbench permanece ignorado pelo Git.'
