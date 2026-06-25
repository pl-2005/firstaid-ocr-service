$ErrorActionPreference = "Stop"

function Get-ProjectRoot {
    return (Split-Path -Parent $PSScriptRoot)
}

function Get-DotEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$EnvFile,
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if (-not (Test-Path -LiteralPath $EnvFile)) {
        return $null
    }

    $pattern = "^\s*" + [regex]::Escape($Name) + "\s*="
    $line = Get-Content -LiteralPath $EnvFile |
        Where-Object { $_ -match $pattern } |
        Select-Object -First 1

    if (-not $line) {
        return $null
    }

    return ($line -replace $pattern, "").Trim().Trim('"').Trim("'")
}

function Resolve-ProjectPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProjectRoot,
        [Parameter(Mandatory = $true)]
        [string]$PathValue
    )

    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $PathValue))
}

function Get-VenvPath {
    $projectRoot = Get-ProjectRoot
    return (Join-Path $projectRoot ".venv")
}

function Get-VenvPython {
    $pythonExe = Join-Path (Get-VenvPath) "Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $pythonExe)) {
        Write-Error "OCR virtual environment not found. Run a script under scripts\create first."
    }
    return $pythonExe
}

function New-OcrEnvironment {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RequirementsFile,
        [string]$PythonExe = "python",
        [switch]$WithDev
    )

    $projectRoot = Get-ProjectRoot
    $venvPath = Get-VenvPath
    $requirementsPath = Join-Path $projectRoot $RequirementsFile

    if (Test-Path -LiteralPath $venvPath) {
        Write-Error "Virtual environment already exists: $venvPath"
    }
    if (-not (Test-Path -LiteralPath $requirementsPath)) {
        Write-Error "Requirements file not found: $requirementsPath"
    }

    & $PythonExe -m venv $venvPath
    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    & $venvPython -m pip install --upgrade pip setuptools wheel
    & $venvPython -m pip install -r $requirementsPath

    if ($WithDev) {
        & $venvPython -m pip install -r (Join-Path $projectRoot "requirements-dev.txt")
    }
}

function Remove-OcrEnvironment {
    $projectRoot = [System.IO.Path]::GetFullPath((Get-ProjectRoot))
    $venvPath = [System.IO.Path]::GetFullPath((Get-VenvPath))

    if ([System.IO.Path]::GetDirectoryName($venvPath) -ne $projectRoot) {
        Write-Error "Refusing to remove virtual environment outside project root: $venvPath"
    }
    if (Test-Path -LiteralPath $venvPath) {
        Remove-Item -LiteralPath $venvPath -Recurse -Force
    }
}

function Start-OcrService {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Device,
        [string]$HostName = "",
        [int]$Port = 0,
        [string]$LogLevel = "",
        [switch]$NoReload
    )

    $projectRoot = Get-ProjectRoot
    Set-Location $projectRoot
    $envFile = Join-Path $projectRoot ".env"

    $configuredHost = Get-DotEnvValue -EnvFile $envFile -Name "OCR_HOST"
    $configuredPort = Get-DotEnvValue -EnvFile $envFile -Name "OCR_PORT"
    $configuredLogLevel = Get-DotEnvValue -EnvFile $envFile -Name "OCR_LOG_LEVEL"
    $cachePath = Get-DotEnvValue -EnvFile $envFile -Name "OCR_MODEL_CACHE_DIR"

    $ocrHost = if ($HostName) { $HostName } elseif ($configuredHost) { $configuredHost } else { "127.0.0.1" }
    $ocrPort = if ($Port -gt 0) { $Port } elseif ($configuredPort) { [int]$configuredPort } else { 8898 }
    $ocrLogLevel = if ($LogLevel) { $LogLevel } elseif ($configuredLogLevel) { $configuredLogLevel } else { "info" }
    if (-not $cachePath) { $cachePath = "model_cache" }

    $resolvedCachePath = Resolve-ProjectPath -ProjectRoot $projectRoot -PathValue $cachePath
    New-Item -ItemType Directory -Force -Path $resolvedCachePath | Out-Null

    $env:OCR_DEVICE = $Device
    $env:PADDLEOCR_HOME = $resolvedCachePath
    $env:PADDLE_PDX_CACHE_HOME = $resolvedCachePath

    $uvicornArgs = @(
        "-m", "uvicorn", "app.main:app",
        "--host", $ocrHost,
        "--port", [string]$ocrPort,
        "--log-level", $ocrLogLevel
    )
    if (-not $NoReload) {
        $uvicornArgs += "--reload"
    }

    & (Get-VenvPython) @uvicornArgs
}
