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
    echo "❌ Docker nao encontrado."
    exit 1
fi

# ==========================================
# Garantir Docker ativo
# ==========================================
if command -v systemctl &> /dev/null && ! systemctl is-active --quiet docker 2>/dev/null; then
    echo "⚠️ Docker ja esta parado."
    exit 0
fi

COMPOSE_CMD="docker compose"

# ==========================================
# Mostrar containers
# ==========================================
echo "📦 Containers ativos:"
docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || true

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

    local OLD_NAME="${WEB_CONTAINER}-old-$(date +%Y%m%d%H%M%S)"
    docker rename "$WEB_CONTAINER" "$OLD_NAME" 2>/dev/null || true

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

    for i in $(seq 1 15); do
        if ! docker ps --filter "name=$OLD_NAME" --format "{{.Names}}" 2>/dev/null | grep -q .; then
            break
        fi
        sleep 1
    done

    docker rm -f "$OLD_NAME" 2>/dev/null || true
    for c in $(docker ps -a --filter "name=assettrack_ti-web" --format "{{.Names}}" 2>/dev/null); do
        docker rm -f "$c" 2>/dev/null || true
    done
    echo "✅ Container removido"
}

# ==========================================
# Stop
# ==========================================
echo "⏳ Parando containers..."

if ! $COMPOSE_CMD down 2>/dev/null; then
    force_stop_web
    $COMPOSE_CMD down 2>/dev/null || true
fi

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
