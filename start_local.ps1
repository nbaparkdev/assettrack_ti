$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  AssetTrack TI - Modo Desenvolvimento Local" -ForegroundColor Cyan
Write-Host "  (Native Go + React Vite)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# 1. Verificar dependencias
if (-not (Get-Command "go" -ErrorAction SilentlyContinue)) {
    Write-Host "[Erro] Go nao esta instalado!" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-Host "[Erro] Node.js (npm) nao esta instalado!" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "[Erro] Docker nao esta instalado!" -ForegroundColor Red
    exit 1
}

# 2. Subir dependencias de banco e cache (Docker)
Write-Host "[Docker] Iniciando PostgreSQL e Redis em background..." -ForegroundColor Blue
docker compose up db redis -d

Write-Host "[Docker] Aguardando PostgreSQL aceitar conexoes..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 3. Iniciar Backend em Go (Em background)
Write-Host "[Backend] Iniciando Backend (Go Gin API) na porta 8080..." -ForegroundColor Green
Set-Location backend
$backendProcess = Start-Process -FilePath "go" -ArgumentList "run ./cmd/server" -PassThru -NoNewWindow
Set-Location ..

# 4. Iniciar Frontend em React
Write-Host "[Frontend] Iniciando Frontend (React/Vite) na porta 3000..." -ForegroundColor Magenta
Set-Location frontend
if (-not (Test-Path "node_modules")) {
    Write-Host "[Frontend] Instalando dependencias do frontend..." -ForegroundColor Yellow
    npm install
}

try {
    # Run frontend in foreground
    npm run dev
}
finally {
    Write-Host "`n[Sistema] Parando servidor de desenvolvimento local..." -ForegroundColor Yellow
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[Sistema] Servidores encerrados." -ForegroundColor Green
}
