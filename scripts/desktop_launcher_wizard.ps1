param(
  [switch]$SkipBrowserOpen
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$desktopStackScript = Join-Path $PSScriptRoot "start_desktop_stack.ps1"
$chromeBridgeScript = Join-Path $PSScriptRoot "start_chrome_bridge.ps1"
$automationChromeScript = Join-Path $PSScriptRoot "start_automation_chrome.ps1"
$dashboardUrl = "http://localhost:3000"
$runtimeUrl = "http://localhost:8000/api/v1/health/runtime"
$chromeDebugUrl = "http://127.0.0.1:9222/json/version"
$automationChromeProfileDir = "$env:LocalAppData\KDPDesktopChromeProfile"

function Write-Title {
  param([string]$Text)

  Write-Host ""
  Write-Host "============================================================" -ForegroundColor DarkGray
  Write-Host $Text -ForegroundColor Cyan
  Write-Host "============================================================" -ForegroundColor DarkGray
}

function Write-Step {
  param([string]$Text)

  Write-Host ""
  Write-Host $Text -ForegroundColor Yellow
}

function Wait-ForEnter {
  param([string]$Prompt)

  Read-Host $Prompt | Out-Null
}

function Test-DockerReady {
  try {
    & docker info | Out-Null
    return $true
  } catch {
    return $false
  }
}

function Test-ChromeDebugReady {
  try {
    $payload = Invoke-RestMethod $chromeDebugUrl -TimeoutSec 3
    return [bool]$payload
  } catch {
    return $false
  }
}

function Get-ChromePath {
  $candidates = @(
    (Join-Path $env:ProgramFiles "Google\Chrome\Application\chrome.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe"),
    (Join-Path $env:LocalAppData "Google\Chrome\Application\chrome.exe")
  ) | Where-Object { $_ -and (Test-Path $_) }

  return $candidates | Select-Object -First 1
}

function Start-AutomationChrome {
  if (-not (Test-Path $automationChromeScript)) {
    throw "Missing Chrome launcher at $automationChromeScript"
  }

  & $automationChromeScript -ProfileDir $automationChromeProfileDir
}

function Ensure-DockerReady {
  if (Test-DockerReady) {
    Write-Host "Docker Desktop is already running." -ForegroundColor Green
    return
  }

  Write-Host "Docker Desktop is not ready yet." -ForegroundColor Yellow
  Write-Host "Please start Docker Desktop now." -ForegroundColor Gray

  $dockerDesktopPath = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
  if (Test-Path $dockerDesktopPath) {
    $answer = Read-Host "Type Y if you want me to open Docker Desktop for you"
    if ($answer -match "^(y|yes)$") {
      Start-Process $dockerDesktopPath
    }
  }

  while (-not (Test-DockerReady)) {
    Wait-ForEnter "Press Enter after Docker Desktop shows as running"
  }

  Write-Host "Docker Desktop is ready." -ForegroundColor Green
}

function Ensure-ChromeDebugReady {
  if (Test-ChromeDebugReady) {
    Write-Host "Chrome remote debugging is already active on port 9222." -ForegroundColor Green
    return
  }

  Write-Host "Authenticated Chrome automation is not active yet." -ForegroundColor Yellow
  Write-Host "This app needs a dedicated KDP Chrome window with remote debugging on port 9222." -ForegroundColor Gray
  Write-Host ""
  Write-Host "I will use a separate persistent Chrome profile for the KDP tool:" -ForegroundColor Gray
  Write-Host $automationChromeProfileDir -ForegroundColor White
  Write-Host ""
  Write-Host "Why this changed:" -ForegroundColor Gray
  Write-Host "Current Chrome versions do not reliably allow remote debugging on the normal default profile." -ForegroundColor Gray
  Write-Host "This KDP profile stays on your desktop machine and keeps its own login state." -ForegroundColor Gray

  $chromePath = Get-ChromePath
  if ($chromePath) {
    Write-Host ""
    Write-Host "KDP Chrome command:" -ForegroundColor Gray
    Write-Host "`"$chromePath`" --remote-debugging-port=9222 --user-data-dir=`"$automationChromeProfileDir`"" -ForegroundColor White

    $answer = Read-Host "Type Y if you want me to open KDP Chrome for you"
    if ($answer -match "^(y|yes)$") {
      Start-AutomationChrome
    }
  } else {
    Write-Host ""
    Write-Host "Chrome was not found in the standard install paths." -ForegroundColor Yellow
    Write-Host "Start Chrome manually with --remote-debugging-port=9222 and --user-data-dir set to the KDP profile path above." -ForegroundColor Gray
  }

  while (-not (Test-ChromeDebugReady)) {
    Wait-ForEnter "Press Enter after the KDP Chrome window is open"
  }

  Write-Host "Chrome remote debugging is ready." -ForegroundColor Green
  Write-Host ""
  Write-Host "If Amazon login is needed, log into Amazon inside that KDP Chrome window now." -ForegroundColor Gray
  Wait-ForEnter "Press Enter after the KDP Chrome window is ready to use"
}

function Start-DesktopStack {
  if (-not (Test-Path $desktopStackScript)) {
    throw "Missing desktop stack script at $desktopStackScript"
  }

  Push-Location $repoRoot
  try {
    & $desktopStackScript
  } finally {
    Pop-Location
  }
}

function Show-RuntimeStatus {
  try {
    $runtime = Invoke-RestMethod $runtimeUrl -TimeoutSec 10
  } catch {
    Write-Host "Runtime status could not be loaded from $runtimeUrl" -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor DarkYellow
    return
  }

  Write-Host ""
  Write-Host "Runtime status: $($runtime.status)" -ForegroundColor Cyan
  Write-Host "Mode: $($runtime.mode)" -ForegroundColor Gray
  Write-Host "Fetch mode: $($runtime.fetch_mode)" -ForegroundColor Gray
  Write-Host "Chrome bridge: $($runtime.chrome_bridge.status)" -ForegroundColor Gray

  if ($runtime.chrome_bridge.reachable -and $runtime.chrome_bridge.chrome_debugging_ready) {
    Write-Host "Authenticated Chrome bridge is ready." -ForegroundColor Green
  } else {
    Write-Host "Authenticated Chrome bridge is still not ready." -ForegroundColor Yellow
    if ($runtime.chrome_bridge.detail) {
      Write-Host "Detail: $($runtime.chrome_bridge.detail)" -ForegroundColor DarkYellow
    }
  }
}

Write-Title "KDP Desktop Launcher"
Write-Host "This wizard checks Docker, opens the dedicated KDP Chrome profile, starts the local stack, and opens the dashboard." -ForegroundColor Gray

Write-Step "Step 1: Docker Desktop"
Ensure-DockerReady

Write-Step "Step 2: Chrome for authenticated Amazon access"
Ensure-ChromeDebugReady

Write-Step "Step 3: Start the local stack"
Start-DesktopStack

Write-Step "Step 4: Open the dashboard"
if (-not $SkipBrowserOpen) {
  Start-Process $dashboardUrl
}
Write-Host "Dashboard: $dashboardUrl" -ForegroundColor Green

Write-Step "Step 5: Confirm runtime status"
Show-RuntimeStatus

Write-Host ""
Write-Host "All set. You can use the dashboard now." -ForegroundColor Green
Wait-ForEnter "Press Enter to close this window"
