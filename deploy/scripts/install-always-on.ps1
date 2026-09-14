#Requires -Version 5.1
<#
.SYNOPSIS
  Install AEMS always-on: no sleep + prevent-sleep agent + ensure containers.

.NOTES
  IMPORTANT: PC cannot run Docker while Windows is Sleeping.
  This setup PREVENTS sleep so AEMS keeps running (monitor may turn off).
#>

param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

# Task registration is the recovery mechanism.  Do not hide a failure here:
# without these tasks the application will not come back after a restart/logoff.
$ErrorActionPreference = "Stop"

$keepAwake = Join-Path $PSScriptRoot "keep-awake.ps1"
$prevent = Join-Path $PSScriptRoot "prevent-sleep-agent.ps1"
$ensure = Join-Path $PSScriptRoot "ensure-aems-running.ps1"

Write-Host "==> 1) Apply keep-awake power settings"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $keepAwake

# Extra: lid / buttons do nothing
Write-Host "==> 2) Lid close / Power / Sleep button = Do nothing"
powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 0
powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 0
powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS SBUTTONACTION 0
powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_BUTTONS SBUTTONACTION 0
powercfg /SETACTIVE SCHEME_CURRENT

$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -ExecutionTimeLimit ([TimeSpan]::Zero) `
  -RestartCount 999 `
  -RestartInterval (New-TimeSpan -Minutes 1)

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# --- Prevent-sleep agent (runs forever at logon) ---
Write-Host "==> 3) Register prevent-sleep agent (logon)"
Unregister-ScheduledTask -TaskName "AEMS-PreventSleep" -Confirm:$false -ErrorAction SilentlyContinue
$actionPrevent = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$prevent`" -ProjectRoot `"$ProjectRoot`""
$triggerLogon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
Register-ScheduledTask -TaskName "AEMS-PreventSleep" -Action $actionPrevent `
  -Trigger $triggerLogon -Settings $settings -Principal $principal `
  -Description "Keep Windows awake so Docker/AEMS never stop" -Force -ErrorAction Stop | Out-Null

# Start agent now if not running
$agentRunning = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -and $_.CommandLine -like "*prevent-sleep-agent.ps1*" }
if (-not $agentRunning) {
  Write-Host "    Starting prevent-sleep agent now..."
  Start-Process -FilePath "powershell.exe" -ArgumentList `
    "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$prevent`" -ProjectRoot `"$ProjectRoot`"" `
    -WindowStyle Hidden
} else {
  Write-Host "    prevent-sleep agent already running"
}

# --- Ensure AEMS at logon ---
Write-Host "==> 4) Register AEMS ensure-at-logon"
Unregister-ScheduledTask -TaskName "AEMS-AlwaysOn-Logon" -Confirm:$false -ErrorAction SilentlyContinue
$actionEnsure = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ensure`" -ProjectRoot `"$ProjectRoot`""
$settingsEnsure = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
Register-ScheduledTask -TaskName "AEMS-AlwaysOn-Logon" -Action $actionEnsure `
  -Trigger $triggerLogon -Settings $settingsEnsure -Principal $principal `
  -Description "Start Docker + AEMS at logon" -Force -ErrorAction Stop | Out-Null

# --- Watchdog every 15 minutes (gentle: never thrash Docker Desktop) ---
Write-Host "==> 5) Register AEMS watchdog (every 15 min)"
Unregister-ScheduledTask -TaskName "AEMS-AlwaysOn-Watchdog" -Confirm:$false -ErrorAction SilentlyContinue
$start = (Get-Date).AddMinutes(2)
$triggerWd = New-ScheduledTaskTrigger -Once -At $start `
  -RepetitionInterval (New-TimeSpan -Minutes 15) `
  -RepetitionDuration (New-TimeSpan -Days 3650)
$settingsWd = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 12)
Register-ScheduledTask -TaskName "AEMS-AlwaysOn-Watchdog" -Action $actionEnsure `
  -Trigger $triggerWd -Settings $settingsWd -Principal $principal `
  -Description "Every 15m gentle AEMS heal (no Docker kill loop)" -Force -ErrorAction Stop | Out-Null

# Registration can appear to succeed while a task is not persisted (for example
# when Task Scheduler denies the current token).  Verify before claiming success.
$requiredTasks = @("AEMS-PreventSleep", "AEMS-AlwaysOn-Logon", "AEMS-AlwaysOn-Watchdog")
foreach ($taskName in $requiredTasks) {
  $task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
  if (-not $task) { throw "Scheduled task was not created: $taskName" }
}

Write-Host "==> 6) Start AEMS now"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ensure -ProjectRoot $ProjectRoot

Write-Host ""
Write-Host "============================================"
Write-Host " ALWAYS-ON INSTALLED"
Write-Host "============================================"
Write-Host " Windows Sleep is DISABLED."
Write-Host " Lid/Power/Sleep button = Do nothing."
Write-Host " Agent blocks sleep even if settings change."
Write-Host " Screen can still turn off (PC stays awake)."
Write-Host ""
Write-Host " NOTE: Cannot run Docker WHILE PC is sleeping."
Write-Host "       This setup keeps PC awake instead."
Write-Host "============================================"
Get-ScheduledTask -TaskName "AEMS-*" | Select-Object TaskName,State | Format-Table -AutoSize
