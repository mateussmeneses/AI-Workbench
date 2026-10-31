[CmdletBinding()]
param([switch]$RunTests)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { & py -m pip install --no-deps -e . }
    else { & python -m pip install --no-deps -e . }
    if ($LASTEXITCODE -ne 0) { throw 'Python installation failed' }
    if ($RunTests) {
        if ($py) { & py -m unittest discover -s tests -v }
        else { & python -m unittest discover -s tests -v }
        if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
    }
    Write-Host 'AI Workbench installed. Open a new shell, then run: aiwh doctor'
} finally { Pop-Location }
