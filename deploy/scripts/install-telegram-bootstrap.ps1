#Requires -Version 5.1
<#
.SYNOPSIS
  Install the lightweight Telegram /bat launcher for AEMS.

.DESCRIPTION
  Registers a per-user logon task which listens for /bat while Docker/AEMS is
  down. Legacy auto-start/watchdog tasks are removed so AEMS starts on demand.
#>

param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"
$bootstrap = Join-Path $PSScriptRoot "telegram-bootstrap.ps1"
if (-not (Test-Path -LiteralPath $bootstrap)) {
  throw "Bootstrap script not found: $bootstrap"
}
$powershell = (Get-Command "powershell.exe" -ErrorAction Stop).Source
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot ".env"))) {
  throw "Missing $ProjectRoot\.env (Telegram token/chat ID are read from this file)"
}

# These legacy tasks start Docker without a Telegram command, which conflicts
# with the requested on-demand behavior. Removing a missing task is harmless.
@("AEMS-AlwaysOn-Logon", "AEMS-AlwaysOn-Watchdog") | ForEach-Object {
  Unregister-ScheduledTask -TaskName $_ -Confirm:$false -ErrorAction SilentlyContinue
}

$action = New-ScheduledTaskAction -Execute $powershell -Argument (
  "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"{0}`" -ProjectRoot `"{1}`"" -f
    $bootstrap, $ProjectRoot
)
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -ExecutionTimeLimit ([TimeSpan]::Zero) `
  -RestartCount 999 `
  -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Register-ScheduledTask -TaskName "AEMS-Telegram-Bootstrap" `
  -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
  -Description "Listen for Telegram /bat and start Docker + AEMS on demand" `
  -Force | Out-Null

$existing = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
  Where-Object {
    $_.CommandLine -and
    $_.CommandLine -match '(?i)-File\s+"?[^\"]*[\\/]telegram-bootstrap\.ps1(?:"|\s|$)'
  }
if (-not $existing) {
  Start-Process -FilePath $powershell -WindowStyle Hidden -ArgumentList (
    "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"{0}`" -ProjectRoot `"{1}`"" -f
      $bootstrap, $ProjectRoot
  )
}

$task = Get-ScheduledTask -TaskName "AEMS-Telegram-Bootstrap" -ErrorAction Stop
Write-Host "AEMS Telegram bootstrap installed: $($task.State)"
Write-Host "From now on, send /bat in the configured Telegram chat to start AEMS."
