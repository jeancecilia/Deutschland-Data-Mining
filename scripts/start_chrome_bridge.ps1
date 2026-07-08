$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot ".host-bridge-venv"
$pythonPath = Join-Path $venvPath "Scripts\\python.exe"
$bridgePort = 9223
$chromePort = 9222

if (-not (Test-Path $pythonPath)) {
  py -3 -m venv $venvPath
}

& $pythonPath -m pip install --upgrade pip | Out-Null
& $pythonPath -m pip install fastapi uvicorn playwright | Out-Null

$existing = Get-CimInstance Win32_Process | Where-Object {
  $_.Name -eq "python.exe" -and $_.CommandLine -like "*host_chrome_bridge.server:app*" -and $_.CommandLine -like "*$bridgePort*"
}
if ($existing) {
  Write-Output "Chrome bridge already running on port $bridgePort."
  exit 0
}

$chromeReady = $false
for ($attempt = 0; $attempt -lt 5; $attempt++) {
  try {
    $versionPayload = & curl.exe -s "http://127.0.0.1:$chromePort/json/version"
    if ($versionPayload) {
      $chromeReady = $true
      break
    }
  } catch {
    Start-Sleep -Seconds 1
  }
}

if (-not $chromeReady) {
  throw "Chrome remote debugging is not available on port $chromePort. Start the dedicated KDP Chrome profile with .\\scripts\\start_automation_chrome.ps1, then rerun .\\scripts\\start_chrome_bridge.ps1."
}

Start-Process `
  -FilePath $pythonPath `
  -ArgumentList @("-m", "uvicorn", "host_chrome_bridge.server:app", "--host", "0.0.0.0", "--port", "$bridgePort") `
  -WorkingDirectory $repoRoot `
  -WindowStyle Hidden

Write-Output "Chrome bridge started on port $bridgePort."
