# Compatibility entry point; all gate logic lives in Python.
param([string]$Root = (Join-Path $PSScriptRoot ".."))
$ErrorActionPreference = "Stop"
$python = $env:RESEARCH_WRITING_PYTHON
if (-not $python) {
    $command = Get-Command python3 -ErrorAction SilentlyContinue
    if (-not $command) { $command = Get-Command python -ErrorAction Stop }
    $python = $command.Source
}
$gateArgs = @("--root", $Root)
& $python (Join-Path $PSScriptRoot "check_skill_integrity.py") @gateArgs
exit $LASTEXITCODE
