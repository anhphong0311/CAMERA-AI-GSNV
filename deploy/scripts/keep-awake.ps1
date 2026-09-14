#Requires -Version 5.1
<#
.SYNOPSIS
  Giữ Windows không Sleep/Hibernate để AEMS (Docker) luôn chạy.

.DESCRIPTION
  Khi máy Sleep, Docker Desktop và toàn bộ container dừng — không thể giữ
  giám sát khi OS đang ngủ. Script này tắt Sleep/Hibernate (AC + DC).
  Màn hình vẫn có thể tắt để tiết kiệm (monitor timeout giữ nguyên nếu muốn).
#>

param(
  [switch]$AllowMonitorOff = $true,
  [int]$MonitorTimeoutMinutes = 10
)

$ErrorActionPreference = "Continue"

Write-Host "==> Disable Sleep / Hibernate (AC + battery)"

# 0 = Never
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0
powercfg /change hibernate-timeout-ac 0
powercfg /change hibernate-timeout-dc 0
powercfg /change disk-timeout-ac 0
powercfg /change disk-timeout-dc 0

# Hybrid sleep off
powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_SLEEP HYBRIDSLEEP 0
powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_SLEEP HYBRIDSLEEP 0

# Lid close / Power button / Sleep button = Do nothing (0)
powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 0
powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 0
powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS SBUTTONACTION 0
powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_BUTTONS SBUTTONACTION 0

if ($AllowMonitorOff) {
  powercfg /change monitor-timeout-ac $MonitorTimeoutMinutes
  powercfg /change monitor-timeout-dc $MonitorTimeoutMinutes
  Write-Host "    Monitor may turn off after ${MonitorTimeoutMinutes}m (PC stays awake)"
} else {
  powercfg /change monitor-timeout-ac 0
  powercfg /change monitor-timeout-dc 0
  Write-Host "    Monitor never turns off"
}

powercfg /SETACTIVE SCHEME_CURRENT

Write-Host "==> Current sleep timeouts:"
powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE | Select-String -Pattern "Current (AC|DC) Power Setting Index"
Write-Host "Done. PC will not sleep while this power plan is active."
