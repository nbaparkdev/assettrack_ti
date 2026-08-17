#!/bin/bash

# ==========================================
# AssetTrack TI - Atualizar/Recompilar Docker (Go + React)
# ==========================================

set -e

echo "------------------------------------------------"
echo "🔄 Atualizando AssetTrack TI (Go + React)"
echo "------------------------------------------------"

# Ir para pasta do script
cd "$(dirname "$0")"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado."
    exit 1
fi

COMPOSE_CMD="docker compose"

# Atualizar Git
if [ -d ".git" ]; then
    echo "📥 Atualizando repositório Git..."
    git pull || true
fi

# Rebuild e Restart
echo "🏗️ Recompilando e reiniciando a aplicação..."
$COMPOSE_CMD up -d --build

# Aguardar API ficar ativa
echo "⏳ Aguardando API (Go) ficar saudável..."
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8080/health | grep -q '"status":"ok"'; then
        echo "✅ API (Go) ativa e saudável!"
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

# Limpeza de imagens suspensas/antigas
echo "🧹 Removendo imagens antigas não utilizadas..."
docker image prune -f || true

# Status final
echo "📦 Containers ativos:"
docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || docker ps

echo ""
echo "------------------------------------------------"
echo "✅ AssetTrack TI atualizado com sucesso!"
echo "------------------------------------------------"
echo "🌐 Frontend URL: http://localhost:8000"
echo "🌐 Backend API:  http://localhost:8080/api/v1"
echo "------------------------------------------------"
