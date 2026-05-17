#!/bin/bash

# ==========================================
# AssetTrack TI - Stop Docker
# ==========================================

set -e

echo "------------------------------------------------"
echo "🛑 Parando AssetTrack TI"
echo "------------------------------------------------"

# Ir para pasta do script
cd "$(dirname "$0")"

# ==========================================
# Verificar Docker
# ==========================================
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado."
    exit 1
fi

# ==========================================
# Garantir Docker ativo
# ==========================================
if ! systemctl is-active --quiet docker; then
    echo "⚠️ Docker já está parado."
    exit 0
fi

COMPOSE_CMD="docker compose"

# ==========================================
# Mostrar containers
# ==========================================
echo "📦 Containers ativos:"
docker ps || true

# ==========================================
# Stop
# ==========================================
echo "⏳ Parando containers..."
$COMPOSE_CMD down

# ==========================================
# Status final
# ==========================================
echo ""
echo "------------------------------------------------"
echo "✅ AssetTrack TI parado com sucesso!"
echo "------------------------------------------------"
echo "💾 Dados do PostgreSQL preservados"
echo "📦 Containers removidos"
echo "------------------------------------------------"
