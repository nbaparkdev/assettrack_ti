#!/bin/bash

# ==========================================
# AssetTrack TI - Update/Rebuild Docker
# ==========================================

set -e

echo "------------------------------------------------"
echo "🔄 Atualizando AssetTrack TI"
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
if command -v systemctl &> /dev/null && ! systemctl is-active --quiet docker 2>/dev/null; then
    echo "⚙️ Iniciando Docker..."
    systemctl start docker 2>/dev/null || true
fi

COMPOSE_CMD="docker compose"

echo "✅ Docker OK"

# ==========================================
# Atualizar Git
# ==========================================
if [ -d ".git" ]; then
    echo "📥 Atualizando repositório..."
    git pull || true
fi

# ==========================================
# Mostrar containers atuais
# ==========================================
echo "📦 Containers atuais:"
docker ps --format "table {{.Names}}\t{{.Status}}" || true

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

echo "🛑 Parando container web..."
force_stop_web

# ==========================================
# Rebuild e Restart
# ==========================================
echo "🏗️ Reconstruindo aplicacao..."
$COMPOSE_CMD up -d --build

# ==========================================
# Aguardar estabilização
# ==========================================
echo "⏳ Aguardando container web iniciar..."
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    STATUS=$($COMPOSE_CMD ps --format json 2>/dev/null | python3 -c "
import sys, json
try:
    content = sys.stdin.read().strip()
    if content.startswith('['):
        data = json.loads(content)
    else:
        data = [json.loads(line) for line in content.splitlines() if line.strip()]
    for s in data:
        if s.get('Service') == 'web' and s.get('State') == 'running':
            if s.get('Health', '') in ('healthy', ''):
                print('ready')
                break
except Exception:
    pass
" 2>/dev/null)
    if [ "$STATUS" = "ready" ]; then
        echo "✅ Container web pronto"
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

# ==========================================
# Limpeza segura
# ==========================================
echo "🧹 Limpando imagens antigas..."
docker image prune -f 2>/dev/null || true

# ==========================================
# Status final
# ==========================================
echo "📦 Containers ativos:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker ps

# ==========================================
# Informacoes
# ==========================================
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$IP" ] && IP="<IP da maquina>"

echo ""
echo "------------------------------------------------"
echo "✅ AssetTrack TI atualizado com sucesso!"
echo "------------------------------------------------"
echo "🌐 Local:    http://localhost:8000"
echo "🌐 Rede:     http://$IP:8000"
echo "📖 Swagger:  http://$IP:8000/docs"
echo "------------------------------------------------"
echo "📜 Logs:"
echo "docker compose logs -f"
