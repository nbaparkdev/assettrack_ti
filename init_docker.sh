#!/bin/bash

# ==========================================
# AssetTrack TI - Inicialização Docker (Decoupled Go + React)
# ==========================================

set -e

echo "------------------------------------------------"
echo "🚀 Iniciando AssetTrack TI (Go + React)"
echo "------------------------------------------------"

# Ir para pasta do projeto
cd "$(dirname "$0")"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado."
    exit 1
fi

# Verificar Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose não encontrado."
    exit 1
fi

COMPOSE_CMD="docker compose"

echo "✅ Docker OK"
echo "✅ Docker Compose OK"

# Derrubar ambiente antigo se estiver ativo
echo "🛑 Parando containers antigos..."
$COMPOSE_CMD down --remove-orphans 2>/dev/null || true

# Garantir remoção de processos conflitantes nas portas 8080 e 8000
PORT_8080=$(docker ps -a --filter "publish=8080" -q 2>/dev/null)
PORT_8000=$(docker ps -a --filter "publish=8000" -q 2>/dev/null)
CONFLICT_CONTAINERS=$(echo "$PORT_8080 $PORT_8000" | xargs)
if [ -n "$CONFLICT_CONTAINERS" ]; then
    echo "🧹 Removendo containers conflitantes nas portas 8080/8000..."
    docker rm -f $CONFLICT_CONTAINERS 2>/dev/null || true
fi

# Build e Start
echo "🏗️ Construindo e iniciando os containers (API, Web, DB, Redis)..."
$COMPOSE_CMD up -d --build

# Aguardar inicialização da API
echo "⏳ Aguardando API (Go) ficar saudável..."
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8080/health | grep -q '"status":"ok"'; then
        echo "✅ API (Go) está ativa e saudável!"
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "⚠️ Timeout aguardando API. Verifique os logs com: docker compose logs api"
fi

# Status
echo "📦 Containers ativos:"
docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || docker ps

# Informações finais
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$IP" ] && IP="<IP da máquina>"

echo ""
echo "------------------------------------------------"
echo "✅ AssetTrack TI iniciado com sucesso!"
echo "------------------------------------------------"
echo "🌐 Frontend URL: http://localhost:8000"
echo "🌐 Backend API:  http://localhost:8080/api/v1"
echo "🌐 API Health:   http://localhost:8080/health"
echo "👤 Admin Padrão: admin@example.com"
echo "🔑 Senha:        admin"
echo "------------------------------------------------"
echo "📜 Logs:"
echo "$COMPOSE_CMD logs -f"
echo "------------------------------------------------"