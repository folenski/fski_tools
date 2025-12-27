<#
Launcher for fkiSave/save.py using the project's virtualenv (.venv).
Forwards all parameters to `save.py`.

Usage:
  .\run_save.ps1 --target <name> [other args passed to save.py]
#>

Param(
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$Args
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Preferred python: project .venv
$venvPy = Join-Path $scriptDir ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPy) { $venvPy } else { "python.exe" }

$savePy = Join-Path $scriptDir "synchronize.py"
if (-not (Test-Path $savePy)) {
    Write-Error "synchronize.py not found in $scriptDir"
    exit 1
}

Write-Host "Using Python: $python"
Write-Host "Running: $savePy $($Args -join ' ')"

$arguments = @($savePy) + $Args
# Run in the same console/process
& $python @arguments
$proc = [pscustomobject]@{ ExitCode = $LASTEXITCODE }
exit $proc.ExitCode
