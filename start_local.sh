#!/bin/bash

set -e

echo "=========================================="
echo "  AssetTrack TI - Modo Desenvolvimento Local"
echo "  (Native Go + React Vite)"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

wait_for_docker_health() {
    local service_name="$1"
    local timeout_seconds="${2:-60}"
    local elapsed=0

    while [ "$elapsed" -lt "$timeout_seconds" ]; do
        local container_id
        container_id="$(docker compose ps -q "$service_name" 2>/dev/null || true)"
        if [ -n "$container_id" ]; then
            local status
            status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id" 2>/dev/null || true)"
            if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
                echo "✅ $service_name pronto ($status)."
                return 0
            fi
        fi

        sleep 2
        elapsed=$((elapsed + 2))
    done

    echo "❌ Timeout aguardando o serviço '$service_name' ficar saudável."
    exit 1
}

if ! command -v go &> /dev/null; then
    echo "❌ Erro: Go não está instalado!"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Erro: Node.js (npm) não está instalado!"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Erro: Docker não está instalado!"
    exit 1
fi

echo "🐳 Iniciando PostgreSQL e Redis em background..."
docker compose up -d db redis

echo "⏳ Aguardando PostgreSQL e Redis ficarem saudáveis..."
wait_for_docker_health db
wait_for_docker_health redis

echo "⚙️  Iniciando Backend (Go Gin API) na porta 8080..."
cd backend
go run ./cmd/server &
BACKEND_PID=$!
cd ..

echo "⚛️  Iniciando Frontend (React/Vite) na porta 3000..."
cd frontend
if [ ! -d "node_modules" ] || [ ! -f "package-lock.json" ]; then
    echo "📦 Instalando dependências do frontend..."
    npm install
fi

cleanup() {
    echo ""
    echo "🛑 Parando servidor de desenvolvimento local..."
    kill "$BACKEND_PID" 2>/dev/null || true
    echo "✅ Servidores encerrados."
}
trap cleanup EXIT INT TERM

npm run dev
