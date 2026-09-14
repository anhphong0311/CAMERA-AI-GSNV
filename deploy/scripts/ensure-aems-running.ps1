#Requires -Version 5.1
<#
.SYNOPSIS
  Keep AEMS up without thrashing Docker Desktop.

.NOTES
  Never force-restart Docker if API/containers already work.
  Force-restart Docker Desktop at most once per CooldownMinutes.
#>

param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
  [int]$DockerWaitSeconds = 300,
  [int]$CooldownMinutes = 30,
  [int]$HealthTimeoutSeconds = 30,
  [int]$HealthFailureThreshold = 3,
  [int]$HealthRetryDelaySeconds = 10,
  # Watchdog chỉ giữ Docker/API hoạt động. Trạng thái giám sát là lựa chọn của
  # người dùng qua /bat và /tat, nên tuyệt đối không tự bật lại sau /tat.
  # Chỉ dùng -EnsureMonitoringOn khi chủ động muốn ép bật giám sát.
  [switch]$EnsureMonitoringOn = $false
)

$ErrorActionPreference = "Continue"
$logDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "always-on.log"
$lockFile = Join-Path $logDir "ensure-aems.lock"
$restartMarker = Join-Path $logDir "docker-restart.marker"
$exitCode = 0

function Write-Log([string]$msg) {
  $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
  try { Add-Content -Path $logFile -Value $line -Encoding UTF8 } catch {}
  Write-Host $line
}

function Test-AemsHttp {
  param([int]$Attempts = 1)

  # Camera reconnects and AI inference can temporarily make the API slower.
  # Do not treat one slow probe as an outage and restart Docker Desktop.
  for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
    $h = curl.exe -s --max-time $HealthTimeoutSeconds "http://localhost:8000/api/v1/health" 2>$null
    if ($h -match '"status"\s*:\s*"healthy"') {
      if ($attempt -gt 1) { Write-Log ("AEMS HTTP recovered on probe {0}/{1}" -f $attempt, $Attempts) }
      return $true
    }
    Write-Log ("AEMS HTTP probe failed ({0}/{1}, timeout={2}s)" -f $attempt, $Attempts, $HealthTimeoutSeconds)
    if ($attempt -lt $Attempts) { Start-Sleep -Seconds $HealthRetryDelaySeconds }
  }
  return $false
}

function Test-DockerCli {
  # Prefer docker ps (works even when docker info is flaky)
  $null = docker ps -q 2>$null
  return ($LASTEXITCODE -eq 0)
}

function Test-DockerReallyBroken {
  # Only true after several failed HTTP probes AND the CLI cannot talk to engine.
  # This prevents a slow API from causing a whole Docker Desktop restart.
  if (Test-AemsHttp -Attempts $HealthFailureThreshold) { return $false }
  if (Test-DockerCli) { return $false }
  $out = docker info 2>&1 | Out-String
  if ($out -match "500 Internal Server Error") { return $true }
  if ($out -match "cannot connect to the Docker daemon|open //\./pipe/dockerDesktopLinuxEngine") { return $true }
  if ($LASTEXITCODE -ne 0 -and -not (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) { return $true }
  # Process up but still starting — not "broken" yet
  return $false
}

function Test-RestartCooldownOk {
  if (-not (Test-Path $restartMarker)) { return $true }
  $age = ((Get-Date) - (Get-Item $restartMarker).LastWriteTime).TotalMinutes
  if ($age -lt $CooldownMinutes) {
    Write-Log ("SKIP Docker force-restart (cooldown {0:N0}m / {1}m)" -f $age, $CooldownMinutes)
    return $false
  }
  return $true
}

function Restart-DockerDesktop {
  if (-not (Test-RestartCooldownOk)) { return $false }
  Write-Log "Restarting Docker Desktop (engine truly broken)..."
  Get-Process "Docker Desktop","com.docker.backend" -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 8
  $dockerExe = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
  if (-not (Test-Path $dockerExe)) {
    Write-Log ("ERROR: Docker Desktop not found: {0}" -f $dockerExe)
    return $false
  }
  Start-Process $dockerExe
  try { Set-Content -Path $restartMarker -Value (Get-Date -Format o) -Encoding ASCII -Force } catch {}
  return $true
}

# Prevent overlapping runs
if (Test-Path $lockFile) {
  $ageMin = ((Get-Date) - (Get-Item $lockFile).LastWriteTime).TotalMinutes
  if ($ageMin -lt 12) {
    Write-Log ("SKIP: another ensure run in progress (lock age {0:N1}m)" -f $ageMin)
    exit 0
  }
  Write-Log "Stale lock found - continuing"
}
try { Set-Content -Path $lockFile -Value $PID -Encoding ASCII -Force } catch {}

try {
  Write-Log "==== ensure-aems-running start ===="
  Write-Log ("ProjectRoot={0}" -f $ProjectRoot)

  try {
    powercfg /change standby-timeout-ac 0 | Out-Null
    powercfg /change standby-timeout-dc 0 | Out-Null
    powercfg /change hibernate-timeout-ac 0 | Out-Null
    powercfg /change hibernate-timeout-dc 0 | Out-Null
  } catch {}

  $agent = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -like "*prevent-sleep-agent.ps1*" }
  if (-not $agent) {
    $prevent = Join-Path $ProjectRoot "deploy\scripts\prevent-sleep-agent.ps1"
    if (Test-Path $prevent) {
      Write-Log "Starting prevent-sleep agent..."
      Start-Process -FilePath "powershell.exe" -WindowStyle Hidden -ArgumentList `
        "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$prevent`" -ProjectRoot `"$ProjectRoot`""
    }
  }

  # Fast path: AEMS already healthy — do NOT touch Docker Desktop
  if (Test-AemsHttp -Attempts $HealthFailureThreshold) {
    Write-Log "AEMS HTTP healthy - skip Docker restart"
    $healthy = $true
  } else {
    $dockerExe = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
    if (-not (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
      if (Test-Path $dockerExe) {
        Write-Log "Starting Docker Desktop (not running)..."
        Start-Process $dockerExe
      } else {
        Write-Log ("ERROR: Docker Desktop not found at {0}" -f $dockerExe)
        $exitCode = 1
        return
      }
    } elseif (Test-DockerReallyBroken) {
      Write-Log "Docker appears broken (no CLI + no HTTP) - force restart once"
      [void](Restart-DockerDesktop)
    } else {
      Write-Log "Docker process up / CLI usable - wait without kill"
    }

    $deadline = (Get-Date).AddSeconds($DockerWaitSeconds)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
      if (Test-DockerCli -or (Test-AemsHttp -Attempts 1)) {
        $ready = $true
        break
      }
      Start-Sleep -Seconds 5
    }
    if (-not $ready) {
      Write-Log ("ERROR: Docker/AEMS not ready after {0}s (no force-loop)" -f $DockerWaitSeconds)
      $exitCode = 1
      return
    }
    Write-Log "Docker CLI/AEMS reachable"

    Set-Location $ProjectRoot
    Write-Log "docker compose up -d"
    $composeOut = docker compose up -d 2>&1 | Out-String
    Write-Log $composeOut.Trim()

    $healthy = $false
    for ($i = 1; $i -le 50; $i++) {
      if (Test-AemsHttp -Attempts 1) {
        Write-Log ("Backend healthy (attempt {0})" -f $i)
        $healthy = $true
        break
      }
      Start-Sleep -Seconds 3
    }
    if (-not $healthy) {
      Write-Log "WARN: backend health not OK - restart container only (not Docker Desktop)"
      docker restart aems-backend 2>&1 | Out-Null
      Start-Sleep -Seconds 20
      if (Test-AemsHttp -Attempts 1) { $healthy = $true; Write-Log "Backend healthy after container restart" }
    }
  }

  # Không tự khôi phục monitoring: /tat phải được giữ nguyên qua mọi lần
  # watchdog chạy. Nhánh này chỉ là opt-in thủ công cho vận hành khẩn cấp.
  if ($EnsureMonitoringOn -and $healthy) {
    # Soft: only compose up if docker cli works (won't kill Desktop)
    if (Test-DockerCli) {
      Set-Location $ProjectRoot
      docker compose up -d 2>&1 | Out-Null
    }
    $st = curl.exe -s --max-time 20 -X POST "http://localhost:8000/api/v1/processing/telegram/command?command=/system_status" 2>$null
    Write-Log ("system_status: {0}" -f $st)
    if ($st -match "TẮT|ĐANG TẮT|OFF") {
      Write-Log "Monitoring OFF - turning ON via /bat"
      $on = curl.exe -s --max-time 90 -X POST "http://localhost:8000/api/v1/processing/telegram/command?command=/bat" 2>$null
      Write-Log ("system_on: {0}" -f $on)
    }
  }

  Write-Log "==== ensure-aems-running done ===="
}
finally {
  try { Remove-Item $lockFile -Force -ErrorAction SilentlyContinue } catch {}
}

exit $exitCode
