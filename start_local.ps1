$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  AssetTrack TI - Modo Desenvolvimento Local" -ForegroundColor Cyan
Write-Host "  (Native Go + React Vite)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

function Wait-ForDockerHealth {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ServiceName,
        [int]$TimeoutSeconds = 60
    )

    $elapsed = 0
    while ($elapsed -lt $TimeoutSeconds) {
        $containerId = docker compose ps -q $ServiceName
        if ($containerId) {
            $status = docker inspect --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" $containerId 2>$null
            if ($status -eq "healthy" -or $status -eq "running") {
                Write-Host "[Docker] $ServiceName pronto ($status)." -ForegroundColor Green
                return
            }
        }

        Start-Sleep -Seconds 2
        $elapsed += 2
    }

    throw "Timeout aguardando o servico '$ServiceName' ficar saudavel."
}

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
docker compose up -d db redis

Write-Host "[Docker] Aguardando PostgreSQL e Redis ficarem saudaveis..." -ForegroundColor Yellow
Wait-ForDockerHealth -ServiceName "db"
Wait-ForDockerHealth -ServiceName "redis"

# 3. Iniciar Backend em Go (Em background)
Write-Host "[Backend] Iniciando Backend (Go Gin API) na porta 8080..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath "go" -ArgumentList "run ./cmd/server" -PassThru -NoNewWindow -WorkingDirectory (Join-Path $PSScriptRoot "backend")

# 4. Iniciar Frontend em React
Write-Host "[Frontend] Iniciando Frontend (React/Vite) na porta 3000..." -ForegroundColor Magenta
Set-Location frontend
if (-not (Test-Path "node_modules") -or -not (Test-Path "package-lock.json")) {
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
