# Script de Instalação e Execução - AssetTrack TI (Windows PowerShell)
Write-Host "--- Iniciando Setup AssetTrack TI ---" -ForegroundColor Cyan

# 1. Verificar Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Erro: Python não encontrado. Por favor, instale o Python 3.11+ e adicione ao PATH." -ForegroundColor Red
    exit
}

# 2. Criar ambiente virtual
if (!(Test-Path "venv")) {
    Write-Host "Criando ambiente virtual..."
    python -m venv venv
}

# 3. Instalar dependências e greenlet (necessário para Windows)
Write-Host "Instalando dependências..."
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pip install greenlet

# 4. Configurar .env se não existir
if (!(Test-Path ".env")) {
    Write-Host "Configurando .env inicial (SQLite)..."
    Copy-Item .env.example .env
    (Get-Content .env) -replace '^DATABASE_URL=.*', 'DATABASE_URL=sqlite+aiosqlite:///./assettrack.db' | Set-Content .env
}

# 5. Criar usuários iniciais
Write-Host "Criando usuários padrão..."
.\venv\Scripts\python.exe create_admin.py
.\venv\Scripts\python.exe create_technician.py

# 6. Iniciar servidor
Write-Host "--- Setup concluído! Iniciando servidor em http://localhost:8000 ---" -ForegroundColor Green
Write-Host "Para acessar de outros dispositivos, use o IP da sua máquina na rede." -ForegroundColor Gray
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
