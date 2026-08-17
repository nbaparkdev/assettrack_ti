#!/bin/bash

# ==========================================
# AssetTrack TI - Parar Docker
# ==========================================

set -e

echo "------------------------------------------------"
echo "🛑 Parando AssetTrack TI"
echo "------------------------------------------------"

# Ir para pasta do script
cd "$(dirname "$0")"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado."
    exit 1
fi

COMPOSE_CMD="docker compose"

echo "⏳ Parando e removendo os containers..."
$COMPOSE_CMD down

echo ""
echo "------------------------------------------------"
echo "✅ AssetTrack TI parado com sucesso!"
echo "------------------------------------------------"
echo "💾 Volume do PostgreSQL (postgres_data) preservado"
echo "------------------------------------------------"
