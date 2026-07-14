# AEMS One-line Production Installer — Windows (Sprint 11)
param(
    [string]$EnvFile = ".env.production"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $Root

Write-Host "=== AEMS Production Installer (Windows) ===" -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker Desktop required. Install from https://docker.com/products/docker-desktop"
}

if (-not (Test-Path $EnvFile)) {
    Copy-Item ".env.production.example" $EnvFile
    Write-Warning "Created $EnvFile — edit secrets before continuing."
    Read-Host "Press Enter after editing $EnvFile"
}

$sslDir = Join-Path $Root "deploy\ssl"
if (-not (Test-Path (Join-Path $sslDir "fullchain.pem"))) {
    New-Item -ItemType Directory -Force -Path $sslDir | Out-Null
    openssl req -x509 -nodes -days 365 -newkey rsa:4096 `
        -keyout (Join-Path $sslDir "privkey.pem") `
        -out (Join-Path $sslDir "fullchain.pem") `
        -subj "/CN=localhost/O=AEMS/C=VN"
}

@("logs", "data\evidence", "data\backups\db", "models") | ForEach-Object {
    New-Item -ItemType Directory -Force -Path (Join-Path $Root $_) | Out-Null
}

docker compose -f docker-compose.production.yml --env-file $EnvFile up -d --build
docker compose -f docker-compose.production.yml exec -T backend alembic upgrade head

Write-Host "=== AEMS deployed ===" -ForegroundColor Green
Write-Host "  HTTPS: https://localhost"
Write-Host "  Grafana: http://localhost:3000"
