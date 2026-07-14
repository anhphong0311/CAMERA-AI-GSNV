# AEMS Windows Service Installer (Sprint 11)
# Requires NSSM: https://nssm.cc/download
param(
    [string]$InstallPath = "C:\AEMS",
    [string]$PythonExe = "python"
)
$ErrorActionPreference = "Stop"

if (-not (Get-Command nssm -ErrorAction SilentlyContinue)) {
    Write-Error "NSSM required. Download from https://nssm.cc and add to PATH."
}

$backendCmd = Join-Path $InstallPath "backend"
nssm install AEMS-Backend $PythonExe "-m uvicorn app.main:app --host 0.0.0.0 --port 8000"
nssm set AEMS-Backend AppDirectory $backendCmd
nssm set AEMS-Backend AppEnvironmentExtra "ENVIRONMENT=production"
nssm set AEMS-Backend AppRestartDelay 5000
nssm set AEMS-Backend AppExit Default Restart

nssm install AEMS-AIWorker $PythonExe "-m app.modules.ops.ai_worker"
nssm set AEMS-AIWorker AppDirectory $backendCmd
nssm set AEMS-AIWorker AppRestartDelay 10000

nssm install AEMS-Watchdog $PythonExe "-m app.modules.ops.watchdog"
nssm set AEMS-Watchdog AppDirectory $backendCmd

Start-Service AEMS-Backend, AEMS-AIWorker, AEMS-Watchdog
Write-Host "Windows services installed and started."
