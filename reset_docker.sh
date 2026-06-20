#!/bin/bash

# ==========================================
# AssetTrack TI - Reset do Ambiente Docker
# ==========================================

set -e

cd "$(dirname "$0")"

COMPOSE_CMD="docker compose"

echo "------------------------------------------------"
echo "🧹 Reset do Ambiente AssetTrack TI"
echo "------------------------------------------------"

# ==========================================
# Verificar Docker
# ==========================================
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado."
    exit 1
fi

# ==========================================
# Parâmetros
# ==========================================
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
            echo "  --full     Remove também volumes e imagens (destrutivo)"
            echo "  --reinit   Executa init_docker.sh ao final"
            echo ""
            echo "Sem --full: apenas derruba containers e redes"
            exit 0
            ;;
        *)
            echo "⚠️  Parâmetro desconhecido: $arg"
            echo "   Use --help para opções"
            exit 1
            ;;
    esac
done

# ==========================================
# Confirmar reset full
# ==========================================
if [ "$FULL_RESET" = true ]; then
    echo ""
    echo "⚠️  ATENÇÃO: --full vai REMOVER permanentemente:"
    echo "   - Volumes (banco de dados PostgreSQL)"
    echo "   - Imagens Docker do projeto"
    echo ""
    read -rp "Digite 'SIM' para confirmar: " CONFIRM
    if [ "$CONFIRM" != "SIM" ]; then
        echo "❌ Cancelado."
        exit 0
    fi
fi

# ==========================================
# Derrubar containers
# ==========================================
echo "🛑 Parando containers..."
$COMPOSE_CMD down --remove-orphans 2>/dev/null || true
echo "✅ Containers parados"

# ==========================================
# Reset full
# ==========================================
if [ "$FULL_RESET" = true ]; then
    echo "🗑️  Removendo volumes..."
    docker volume ls -q | grep -E 'assettrack|assettrack_ti' | xargs -r docker volume rm 2>/dev/null || true

    echo "🗑️  Removendo imagens do projeto..."
    docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep -E 'assettrack' | awk '{print $2}' | xargs -r docker rmi 2>/dev/null || true

    echo "🧹 Limpando build cache..."
    docker builder prune -f 2>/dev/null || true

    echo "✅ Reset full concluído"
fi

echo ""
echo "------------------------------------------------"
echo "✅ Reset concluído"
echo "------------------------------------------------"

# ==========================================
# Reinit
# ==========================================
if [ "$REINIT" = true ]; then
    if [ -f "./init_docker.sh" ]; then
        echo "🚀 Executando init_docker.sh..."
        exec bash ./init_docker.sh
    else
        echo "❌ init_docker.sh não encontrado"
        exit 1
    fi
fi
