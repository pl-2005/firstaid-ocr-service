param(
    [Alias("Host")]
    [string]$HostName = "",
    [int]$Port = 0,
    [string]$LogLevel = "",
    [switch]$NoReload
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "..\common.ps1")

Start-OcrService `
    -Device "cpu" `
    -HostName $HostName `
    -Port $Port `
    -LogLevel $LogLevel `
    -NoReload:$NoReload
