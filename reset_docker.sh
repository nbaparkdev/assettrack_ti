#!/bin/bash

# ==========================================
# AssetTrack TI - Reset do Ambiente Docker (Go + React)
# ==========================================

set -e

cd "$(dirname "$0")"

COMPOSE_CMD="docker compose"

echo "------------------------------------------------"
echo "🧹 Reset do Ambiente AssetTrack TI (Go + React)"
echo "------------------------------------------------"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado."
    exit 1
fi

FULL_RESET=false
REINIT=false

for arg in "$@"; do
    case $arg in
        --full)
            FULL_RESET=true
            ;;
        --reinit)
            REINIT=true
            ;;
        --help|-h)
            echo "Uso: $0 [--full] [--reinit]"
            echo ""
            echo "  --full     Remove também os volumes (banco de dados) e imagens"
            echo "  --reinit   Executa init_docker.sh após o reset"
            echo ""
            exit 0
            ;;
        *)
            echo "⚠️ Parâmetro desconhecido: $arg"
            exit 1
            ;;
    esac
done

if [ "$FULL_RESET" = true ]; then
    echo ""
    echo "⚠️ ATENÇÃO: --full vai REMOVER permanentemente:"
    echo "   - Volumes (dados do banco de dados PostgreSQL)"
    echo "   - Imagens do projeto"
    echo ""
    read -rp "Digite 'SIM' para confirmar o reset completo: " CONFIRM
    if [ "$CONFIRM" != "SIM" ]; then
        echo "❌ Cancelado."
        exit 0
    fi
fi

echo "🛑 Parando containers..."
$COMPOSE_CMD down --remove-orphans || true

if [ "$FULL_RESET" = true ]; then
    echo "🗑️ Removendo volumes..."
    $COMPOSE_CMD down -v --remove-orphans || true
    
    echo "🗑️ Removendo imagens..."
    docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep -E 'assettrack' | awk '{print $2}' | xargs -r docker rmi -f || true
    
    echo "🧹 Limpando cache do build..."
    docker builder prune -f || true
fi

echo ""
echo "------------------------------------------------"
echo "✅ Reset concluído!"
echo "------------------------------------------------"

if [ "$REINIT" = true ]; then
    echo "🚀 Reiniciando ambiente..."
    exec bash ./init_docker.sh
fi
