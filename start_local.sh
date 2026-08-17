#!/bin/bash

# Abortar em caso de erros
set -e

echo "=========================================="
echo "  AssetTrack TI - Modo Desenvolvimento Local"
echo "  (Native Go + React Vite)"
echo "=========================================="
echo ""

# Ir para pasta do projeto
cd "$(dirname "$0")"

# 1. Verificar dependências
if ! command -v go &> /dev/null; then
    echo "❌ Erro: Go não está instalado!"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Erro: Node.js (npm) não está instalado!"
    exit 1
fi

# 2. Subir dependências de banco e cache (Docker)
echo "🐳 Iniciando PostgreSQL e Redis em background..."
docker compose up db redis -d

# Aguardar banco de dados
echo "⏳ Aguardando PostgreSQL aceitar conexões..."
sleep 3

# 3. Iniciar Backend em Go (Em background)
echo "⚙️  Iniciando Backend (Go Gin API) na porta 8080..."
cd backend
go run ./cmd/server &
BACKEND_PID=$!
cd ..

# 4. Iniciar Frontend em React
echo "⚛️  Iniciando Frontend (React/Vite) na porta 3000..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependências do frontend..."
    npm install
fi

# Função para matar o processo Go quando fechar o script
cleanup() {
    echo ""
    echo "🛑 Parando servidor de desenvolvimento local..."
    kill $BACKEND_PID 2>/dev/null || true
    echo "✅ Servidores encerrados."
}
trap cleanup EXIT INT TERM

npm run dev
