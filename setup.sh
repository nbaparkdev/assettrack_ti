#!/bin/bash

# Script de Instalação e Execução - AssetTrack TI (Linux/macOS)
echo "--- Iniciando Setup AssetTrack TI ---"

# 1. Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "Erro: Python 3 não encontrado. Por favor, instale o Python 3.11+."
    exit 1
fi

# 2. Criar ambiente virtual
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

# 3. Ativar venv e instalar dependências
echo "Instalando dependências..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configurar .env se não existir
if [ ! -f ".env" ]; then
    echo "Configurando .env inicial (SQLite)..."
    cp .env.example .env
    # Forçar SQLite no .env local para facilidade de uso
    sed -i 's/^DATABASE_URL=.*/DATABASE_URL=sqlite+aiosqlite:\/\/\/.\/assettrack.db/' .env
fi

# 5. Criar usuários iniciais
echo "Criando usuários padrão..."
python3 create_admin.py
python3 create_technician.py

# 6. Iniciar servidor
echo "--- Setup concluído! Iniciando servidor em http://localhost:8000 ---"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
