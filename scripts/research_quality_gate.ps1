# Compatibility entry point; all gate logic lives in Python.
param([string]$ProjectPath, [switch]$Submission, [switch]$SelfTest)
$ErrorActionPreference = "Stop"
$python = $env:RESEARCH_WRITING_PYTHON
if (-not $python) {
    $command = Get-Command python3 -ErrorAction SilentlyContinue
    if (-not $command) { $command = Get-Command python -ErrorAction Stop }
    $python = $command.Source
}
$gateArgs = @()

if ($ProjectPath) { $gateArgs += @("--project-path", $ProjectPath) }
if ($Submission) { $gateArgs += "--submission" }
if ($SelfTest) { $gateArgs += "--self-test" }
& $python (Join-Path $PSScriptRoot "research_quality_gate.py") @gateArgs
exit $LASTEXITCODE
