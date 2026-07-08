param(
  [string]$ProfileDir = "$env:LocalAppData\KDPDesktopChromeProfile",
  [string]$StartUrl = "about:blank"
)

$ErrorActionPreference = "Stop"

$chromeDebugUrl = "http://127.0.0.1:9222/json/version"

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

if (Test-ChromeDebugReady) {
  Write-Output "Chrome remote debugging is already active on port 9222."
  exit 0
}

$chromePath = Get-ChromePath
if (-not $chromePath) {
  throw "Chrome was not found in the standard install paths."
}

New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

$arguments = @(
  "--remote-debugging-port=9222",
  "--user-data-dir=$ProfileDir",
  "--no-first-run",
  "--no-default-browser-check",
  "--new-window",
  $StartUrl
)

Start-Process -FilePath $chromePath -ArgumentList $arguments

Write-Output "Started KDP Chrome with profile $ProfileDir"
