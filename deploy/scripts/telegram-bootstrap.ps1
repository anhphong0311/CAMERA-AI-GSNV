#Requires -Version 5.1
<#
.SYNOPSIS
  Lightweight Telegram bootstrap for AEMS.

.DESCRIPTION
  This process runs outside Docker so /bat still works when Docker/AEMS is down.
  When the backend is healthy it stops polling and lets the in-app Telegram
  poller own the bot. Only the configured TELEGRAM_CHAT_ID may start AEMS.
#>

param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
  [int]$DockerWaitSeconds = 300,
  [int]$BackendWaitSeconds = 240,
  [int]$PollTimeoutSeconds = 25,
  [switch]$Once,
  [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"
$logDir = Join-Path $ProjectRoot "logs"
$logFile = Join-Path $logDir "telegram-bootstrap.log"
$offsetFile = Join-Path $logDir "telegram-command.offset"
$legacyOffsetFile = Join-Path $logDir "telegram-bootstrap.offset"
$envFile = Join-Path $ProjectRoot ".env"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
if (-not (Test-Path -LiteralPath $offsetFile) -and
    (Test-Path -LiteralPath $legacyOffsetFile)) {
  Copy-Item -LiteralPath $legacyOffsetFile -Destination $offsetFile
}

function Write-BootstrapLog([string]$Message) {
  $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
  try { Add-Content -LiteralPath $logFile -Value $line -Encoding UTF8 } catch {}
}

function Get-DotEnvValue([string]$Name) {
  if (-not (Test-Path -LiteralPath $envFile)) { return "" }
  foreach ($line in Get-Content -LiteralPath $envFile) {
    if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
    $parts = $line -split '=', 2
    if ($parts[0].Trim() -ne $Name) { continue }
    $value = $parts[1].Trim()
    if ($value.Length -ge 2) {
      if (($value.StartsWith('"') -and $value.EndsWith('"')) -or
          ($value.StartsWith("'") -and $value.EndsWith("'"))) {
        $value = $value.Substring(1, $value.Length - 2)
      }
    }
    return $value
  }
  return ""
}

function Get-TelegramSettings {
  $token = [Environment]::GetEnvironmentVariable("TELEGRAM_BOT_TOKEN")
  $chatId = [Environment]::GetEnvironmentVariable("TELEGRAM_CHAT_ID")
  if ([string]::IsNullOrWhiteSpace($token)) { $token = Get-DotEnvValue "TELEGRAM_BOT_TOKEN" }
  if ([string]::IsNullOrWhiteSpace($chatId)) { $chatId = Get-DotEnvValue "TELEGRAM_CHAT_ID" }
  return @{ Token = $token.Trim(); ChatId = $chatId.Trim() }
}

function Invoke-TelegramApi {
  param(
    [Parameter(Mandatory)][string]$Token,
    [Parameter(Mandatory)][string]$Method,
    [hashtable]$Body = @{},
    [int]$TimeoutSeconds = 35
  )
  $uri = "https://api.telegram.org/bot${Token}/${Method}"
  return Invoke-RestMethod -Method Post -Uri $uri -Body $Body -TimeoutSec $TimeoutSeconds
}

function Send-TelegramText([string]$Token, [string]$ChatId, [string]$Text) {
  try {
    $null = Invoke-TelegramApi -Token $Token -Method "sendMessage" -Body @{
      chat_id = $ChatId
      text = $Text
    } -TimeoutSeconds 30
    return $true
  } catch {
    Write-BootstrapLog ("Telegram reply failed: {0}" -f $_.Exception.Message)
    return $false
  }
}

function Get-AemsBackendBase {
  # Local compose publishes 18000; the base compose publishes 8000.
  foreach ($baseUrl in @("http://127.0.0.1:18000", "http://127.0.0.1:8000")) {
    try {
      $response = Invoke-RestMethod -Method Get -Uri "${baseUrl}/api/v1/health" -TimeoutSec 5
      $status = if ($response.data) { $response.data.status } else { $response.status }
      if ($status -eq "healthy") { return $baseUrl }
    } catch {}
  }
  return $null
}

function Test-AemsHealthy {
  return ($null -ne (Get-AemsBackendBase))
}

function Test-DockerReady {
  & docker info *> $null
  return ($LASTEXITCODE -eq 0)
}

function Find-DockerDesktop {
  $candidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\Docker Desktop.exe"),
    (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe")
  )
  foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate) { return $candidate }
  }
  return $null
}

function Wait-Until {
  param(
    [Parameter(Mandatory)][scriptblock]$Condition,
    [Parameter(Mandatory)][int]$TimeoutSeconds,
    [int]$DelaySeconds = 5
  )
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    if (& $Condition) { return $true }
    Start-Sleep -Seconds $DelaySeconds
  }
  return $false
}

function Start-AemsOnDemand {
  $backendBase = Get-AemsBackendBase
  if ($backendBase) {
    try {
      $reply = Invoke-RestMethod -Method Post `
        -Uri "${backendBase}/api/v1/processing/telegram/command?command=%2Fbat" `
        -TimeoutSec 120
      if ($reply.data.response) { return [string]$reply.data.response }
      if ($reply.data) { return [string]$reply.data }
    } catch {
      Write-BootstrapLog ("Backend /bat call failed: {0}" -f $_.Exception.Message)
    }
    return "🟢 AEMS đang chạy."
  }

  if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    return "❌ Không tìm thấy Docker CLI trên máy AEMS."
  }

  if (-not (Test-DockerReady)) {
    $dockerDesktop = Find-DockerDesktop
    if (-not $dockerDesktop) {
      return "❌ Không tìm thấy Docker Desktop trên máy AEMS."
    }
    Write-BootstrapLog "Starting Docker Desktop on demand"
    Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
    if (-not (Wait-Until -Condition { Test-DockerReady } -TimeoutSeconds $DockerWaitSeconds)) {
      return (
        "❌ Docker Desktop không khởi động được sau ${DockerWaitSeconds}s.`n" +
        "Kiểm tra logs/telegram-bootstrap.log và Docker Desktop trên máy AEMS."
      )
    }
  }

  Write-BootstrapLog "Running docker compose up -d"
  Push-Location $ProjectRoot
  try {
    $composeOutput = & docker compose `
      -f docker-compose.yml -f docker-compose.local.yml up -d 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
      Write-BootstrapLog ("docker compose failed: {0}" -f $composeOutput.Trim())
      return "❌ Không thể dựng AEMS bằng Docker Compose. Xem logs/telegram-bootstrap.log."
    }
  } finally {
    Pop-Location
  }

  if (-not (Wait-Until -Condition { Test-AemsHealthy } -TimeoutSeconds $BackendWaitSeconds -DelaySeconds 3)) {
    return "⚠️ Docker đã chạy nhưng backend AEMS chưa healthy sau ${BackendWaitSeconds}s."
  }

  $backendBase = Get-AemsBackendBase
  try {
    $reply = Invoke-RestMethod -Method Post `
      -Uri "${backendBase}/api/v1/processing/telegram/command?command=%2Fbat" `
      -TimeoutSec 120
    if ($reply.data.response) { return [string]$reply.data.response }
    if ($reply.data) { return [string]$reply.data }
  } catch {
    Write-BootstrapLog ("AEMS started but /bat call failed: {0}" -f $_.Exception.Message)
  }
  return "🟢 AEMS đã khởi động; dashboard: http://localhost:18080/."
}

function Save-Offset([long]$Offset) {
  Set-Content -LiteralPath $offsetFile -Value $Offset -Encoding ASCII
}

function Get-SavedOffset {
  if (-not (Test-Path -LiteralPath $offsetFile)) { return $null }
  $raw = (Get-Content -LiteralPath $offsetFile -Raw).Trim()
  $parsed = 0L
  if ([long]::TryParse($raw, [ref]$parsed)) { return $parsed }
  return $null
}

$createdNew = $false
$mutex = [System.Threading.Mutex]::new(
  $true,
  "Local\AEMS-Telegram-Bootstrap",
  [ref]$createdNew
)
if (-not $createdNew) {
  Write-BootstrapLog "Another bootstrap process is already running"
  exit 0
}

try {
  Write-BootstrapLog "Telegram bootstrap started"
  if ($ValidateOnly) {
    $settings = Get-TelegramSettings
    if ([string]::IsNullOrWhiteSpace($settings.Token) -or
        [string]::IsNullOrWhiteSpace($settings.ChatId)) {
      throw "TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID are not configured"
    }
    Write-Output "VALIDATION_OK"
    exit 0
  }
  $offset = Get-SavedOffset

  while ($true) {
    try {
      # The backend owns getUpdates while healthy. This prevents two pollers
      # from racing for the same Telegram update.
      if (Test-AemsHealthy) {
        if ($Once) { break }
        Start-Sleep -Seconds 10
        continue
      }

      $settings = Get-TelegramSettings
      if ([string]::IsNullOrWhiteSpace($settings.Token) -or
          [string]::IsNullOrWhiteSpace($settings.ChatId)) {
        Write-BootstrapLog "TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID are not configured"
        if ($Once) { break }
        Start-Sleep -Seconds 30
        continue
      }

      $body = @{ timeout = $(if ($Once) { 0 } else { $PollTimeoutSeconds }) }
      if ($null -ne $offset) { $body.offset = $offset }
      $updates = Invoke-TelegramApi -Token $settings.Token -Method "getUpdates" `
        -Body $body -TimeoutSeconds ($PollTimeoutSeconds + 10)

      foreach ($update in @($updates.result)) {
        $updateId = [long]$update.update_id
        $offset = $updateId + 1
        # Persist before doing slow Docker work. The next getUpdates call will
        # acknowledge this update even if Windows restarts during startup.
        Save-Offset $offset

        $message = if ($update.message) { $update.message } else { $update.edited_message }
        if (-not $message -or -not $message.text) { continue }
        if ([string]$message.chat.id -ne [string]$settings.ChatId) {
          Write-BootstrapLog "Ignored Telegram command from unauthorized chat"
          continue
        }

        $command = ([string]$message.text).Trim().Split(' ')[0].Split('@')[0].ToLowerInvariant()
        if ($command -in @('/bat', '/system_on', '/on')) {
          # Acknowledge /bat before the backend poller starts, avoiding a
          # duplicate delivery during the ownership hand-off.
          $null = Invoke-TelegramApi -Token $settings.Token -Method "getUpdates" `
            -Body @{ offset = $offset; timeout = 0; limit = 1 } -TimeoutSeconds 10
          $null = Send-TelegramText $settings.Token $settings.ChatId "⏳ Đã nhận /bat. Đang khởi động Docker và AEMS..."
          $result = Start-AemsOnDemand
          $null = Send-TelegramText $settings.Token $settings.ChatId $result
        } elseif ($command -in @('/tat', '/system_off', '/off')) {
          $null = Send-TelegramText $settings.Token $settings.ChatId "🔴 AEMS hiện đang tắt. Gõ /bat để khởi động."
        } elseif ($command -in @('/system_status', '/status')) {
          $null = Send-TelegramText $settings.Token $settings.ChatId "🔴 AEMS/Docker chưa hoạt động. Gõ /bat để khởi động."
        }
      }
    } catch {
      Write-BootstrapLog ("Bootstrap loop error: {0}" -f $_.Exception.Message)
      if ($Once) { break }
      Start-Sleep -Seconds 5
    }

    if ($Once) { break }
  }
} finally {
  $mutex.ReleaseMutex()
  $mutex.Dispose()
  Write-BootstrapLog "Telegram bootstrap stopped"
}
