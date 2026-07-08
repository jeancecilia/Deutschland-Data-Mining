param(
  [switch]$Build,
  [switch]$FrontendDev
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$bridgeScript = Join-Path $PSScriptRoot "start_chrome_bridge.ps1"

Push-Location $repoRoot
try {
  & docker info | Out-Null

  if (-not (Test-Path $bridgeScript)) {
    throw "Missing bridge launcher at $bridgeScript"
  }

  & $bridgeScript

  $previousFrontendAppEnv = $env:FRONTEND_APP_ENV
  if ($FrontendDev) {
    $env:FRONTEND_APP_ENV = "development"
  } else {
    $env:FRONTEND_APP_ENV = "production"
  }

  $composeArgs = @("compose", "up", "-d")
  if ($Build) {
    $composeArgs += "--build"
  }

  & docker @composeArgs
  if ($LASTEXITCODE -ne 0) {
    throw "docker compose failed with exit code $LASTEXITCODE."
  }

  Write-Output "Desktop stack started."
  Write-Output "Frontend mode: $($env:FRONTEND_APP_ENV)"
  Write-Output "Dashboard: http://localhost:3000"
  Write-Output "API docs: http://localhost:8000/docs"
  Write-Output "Chrome bridge: http://localhost:9223/health"
} finally {
  if ($null -eq $previousFrontendAppEnv) {
    Remove-Item Env:FRONTEND_APP_ENV -ErrorAction SilentlyContinue
  } else {
    $env:FRONTEND_APP_ENV = $previousFrontendAppEnv
  }
  Pop-Location
}
