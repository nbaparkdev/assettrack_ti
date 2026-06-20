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
    echo "❌ Docker nao encontrado."
    exit 1
fi

# ==========================================
# Parametros
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
            echo "  --full     Remove tambem volumes e imagens (destrutivo)"
            echo "  --reinit   Executa init_docker.sh ao final"
            echo ""
            echo "Sem --full: apenas derruba containers e redes"
            exit 0
            ;;
        *)
            echo "⚠️  Parametro desconhecido: $arg"
            echo "   Use --help para opcoes"
            exit 1
            ;;
    esac
done

# ==========================================
# Confirmar reset full
# ==========================================
if [ "$FULL_RESET" = true ]; then
    echo ""
    echo "⚠️  ATENCAO: --full vai REMOVER permanentemente:"
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
# Force stop web container (AppArmor-safe)
# ==========================================
force_stop_web() {
    local WEB_CONTAINER
    WEB_CONTAINER=$(docker ps -a --filter "name=^assettrack_ti-web" --format "{{.Names}}" 2>/dev/null | head -1)
    if [ -z "$WEB_CONTAINER" ]; then
        return 0
    fi

    # Tentar stop normal primeiro
    if docker stop "$WEB_CONTAINER" 2>/dev/null; then
        docker rm "$WEB_CONTAINER" 2>/dev/null || true
        return 0
    fi

    echo "⚠️ Container preso (AppArmor/snap). Usando metodo alternativo..."

    # Renomear para liberar o nome no compose
    local OLD_NAME="${WEB_CONTAINER}-old-$(date +%Y%m%d%H%M%S)"
    docker rename "$WEB_CONTAINER" "$OLD_NAME" 2>/dev/null || true

    # Matar uvicorn de dentro do container via Python
    docker exec "$OLD_NAME" python3 -c "
import os, signal
for pid in [int(p) for p in os.listdir('/proc') if p.isdigit()]:
    try:
        with open(f'/proc/{pid}/cmdline', 'rb') as f:
            cmd = f.read().decode()
        if 'python' in cmd and 'uvicorn' in cmd and 'app.main' in cmd:
            os.kill(pid, signal.SIGTERM)
            break
    except:
        pass
" 2>/dev/null || true

    # Aguardar container sair
    for i in $(seq 1 15); do
        if ! docker ps --filter "name=$OLD_NAME" --format "{{.Names}}" 2>/dev/null | grep -q .; then
            break
        fi
        sleep 1
    done

    # Remover containers antigos
    docker rm -f "$OLD_NAME" 2>/dev/null || true
    for c in $(docker ps -a --filter "name=assettrack_ti-web" --format "{{.Names}}" 2>/dev/null); do
        docker rm -f "$c" 2>/dev/null || true
    done
    echo "✅ Container antigo removido"
}

# ==========================================
# Derrubar containers
# ==========================================
echo "🛑 Parando containers..."

# Tentar compose down normal primeiro
if ! $COMPOSE_CMD down --remove-orphans 2>/dev/null; then
    # Fallback: force stop web e tenta de novo
    force_stop_web
    $COMPOSE_CMD down --remove-orphans 2>/dev/null || true
fi

echo "✅ Containers parados"

# ==========================================
# Reset full
# ==========================================
if [ "$FULL_RESET" = true ]; then
    echo "🗑️  Removendo volumes..."
    docker volume ls -q 2>/dev/null | grep -E 'assettrack|assettrack_ti' | xargs -r docker volume rm 2>/dev/null || true

    echo "🗑️  Removendo imagens do projeto..."
    docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' 2>/dev/null | grep -E 'assettrack' | awk '{print $2}' | xargs -r docker rmi 2>/dev/null || true

    echo "🧹 Limpando build cache..."
    docker builder prune -f 2>/dev/null || true

    echo "✅ Reset full concluido"
fi

echo ""
echo "------------------------------------------------"
echo "✅ Reset concluido"
echo "------------------------------------------------"

# ==========================================
# Reinit
# ==========================================
if [ "$REINIT" = true ]; then
    if [ -f "./init_docker.sh" ]; then
        echo "🚀 Executando init_docker.sh..."
        exec bash ./init_docker.sh
    else
        echo "❌ init_docker.sh nao encontrado"
        exit 1
    fi
fi
