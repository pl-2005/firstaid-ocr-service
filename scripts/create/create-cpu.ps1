param(
    [string]$PythonExe = "python",
    [switch]$WithDev
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "..\common.ps1")

New-OcrEnvironment `
    -RequirementsFile "requirements-cpu.txt" `
    -PythonExe $PythonExe `
    -WithDev:$WithDev
