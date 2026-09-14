#Requires -Version 5.1
<#
.SYNOPSIS
  Background agent: prevent Windows Sleep while AEMS should stay online.

.DESCRIPTION
  Windows Sleep ALWAYS stops Docker. This agent continuously calls
  SetThreadExecutionState so the OS cannot enter sleep (screen may still turn off).
  Run via Scheduled Task at logon (AEMS-PreventSleep).
#>

param(
  [int]$HeartbeatSeconds = 30,
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Continue"
$logDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "prevent-sleep.log"

function Write-Log([string]$msg) {
  $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
  try { Add-Content -Path $logFile -Value $line -Encoding UTF8 } catch {}
}

# Win32 API: keep system awake (allow display off)
Add-Type -Namespace Aems -Name Power -MemberDefinition @"
[DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
public static extern uint SetThreadExecutionState(uint esFlags);
"@

$ES_CONTINUOUS = [uint32]"0x80000000"
$ES_SYSTEM_REQUIRED = [uint32]"0x00000001"
# Optional: $ES_DISPLAY_REQUIRED = 0x00000002  -- keep screen on too
$flags = $ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED

Write-Log "prevent-sleep agent started (pid=$PID)"
Write-Log "Holding ES_SYSTEM_REQUIRED so Windows cannot sleep"

# Apply power plan once at start
try {
  powercfg /change standby-timeout-ac 0 | Out-Null
  powercfg /change standby-timeout-dc 0 | Out-Null
  powercfg /change hibernate-timeout-ac 0 | Out-Null
  powercfg /change hibernate-timeout-dc 0 | Out-Null
  powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_SLEEP HYBRIDSLEEP 0 | Out-Null
  powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_SLEEP HYBRIDSLEEP 0 | Out-Null
  # Lid / power / sleep button = Do nothing (0)
  powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS LIDACTION 0 | Out-Null
  powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_BUTTONS LIDACTION 0 | Out-Null
  powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 0 | Out-Null
  powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 0 | Out-Null
  powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS SBUTTONACTION 0 | Out-Null
  powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_BUTTONS SBUTTONACTION 0 | Out-Null
  powercfg /SETACTIVE SCHEME_CURRENT | Out-Null
  Write-Log "powercfg: sleep/lid/power-button set to never/do-nothing"
} catch {
  Write-Log ("powercfg warn: {0}" -f $_)
}

while ($true) {
  try {
    [void][Aems.Power]::SetThreadExecutionState($flags)
  } catch {
    Write-Log ("SetThreadExecutionState failed: {0}" -f $_)
  }
  Start-Sleep -Seconds $HeartbeatSeconds
}
