#!/bin/bash

# ==========================================
# AssetTrack TI - Inicializacao Docker
# ==========================================

set -e

echo "------------------------------------------------"
echo "🚀 Iniciando AssetTrack TI"
echo "------------------------------------------------"

# Ir para pasta do projeto
cd "$(dirname "$0")"

# ==========================================
# Verificar Docker
# ==========================================
if ! command -v docker &> /dev/null; then
    echo "❌ Docker nao encontrado."
    echo "Instale com:"
    echo "apt install docker.io docker-compose-plugin -y"
    exit 1
fi

# ==========================================
# Verificar servico Docker
# ==========================================
if command -v systemctl &> /dev/null; then
    if ! systemctl is-active --quiet docker 2>/dev/null; then
        echo "⚙️ Iniciando servico Docker..."
        systemctl start docker 2>/dev/null || true
    fi
elif command -v service &> /dev/null; then
    if ! service docker status &> /dev/null; then
        echo "⚙️ Iniciando servico Docker..."
        service docker start 2>/dev/null || true
    fi
fi

# ==========================================
# Verificar Docker Compose
# ==========================================
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose nao encontrado."
    exit 1
fi

COMPOSE_CMD="docker compose"

echo "✅ Docker OK"
echo "✅ Docker Compose OK"

# ==========================================
# Criar .env se nao existir
# ==========================================
if [ ! -f ".env" ]; then
    echo "⚙️ Criando arquivo .env..."

    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        touch .env
    fi
else
    echo "✅ Arquivo .env encontrado"
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
# Derrubar ambiente antigo
# ==========================================
echo "🛑 Parando containers antigos..."

# Tentar compose down normal primeiro
if ! $COMPOSE_CMD down --remove-orphans 2>/dev/null; then
    echo "⚠️ Parada padrão falhou. Iniciando parada forçada..."
    force_stop_web
    
    # Tenta derrubar com compose novamente
    if ! $COMPOSE_CMD down --remove-orphans 2>/dev/null; then
        # Se falhar, limpa manualmente qualquer container restante do projeto
        REMAINING=$(docker ps -a --filter "name=assettrack" -q 2>/dev/null)
        if [ -n "$REMAINING" ]; then
            echo "🛑 Parando e removendo containers restantes do projeto..."
            docker stop $REMAINING 2>/dev/null || true
            docker rm -f $REMAINING 2>/dev/null || true
        fi
    fi
fi

# ==========================================
# Build e Start
# ==========================================
echo "🏗️ Iniciando banco de dados..."
$COMPOSE_CMD up -d db

echo "⏳ Aguardando banco de dados ficar pronto..."
for i in $(seq 1 30); do
    if $COMPOSE_CMD exec -T db pg_isready -U user -d assettrack 2>/dev/null; then
        echo "✅ Banco de dados pronto!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Timeout aguardando banco de dados."
        exit 1
    fi
    sleep 2
done

echo "🏗️ Construindo e iniciando demais containers..."
$COMPOSE_CMD up -d --build

# ==========================================
# Aguardar inicializacao
# ==========================================
echo "⏳ Aguardando container web iniciar..."
MAX_WAIT=120
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
    sleep 3
    WAITED=$((WAITED + 3))
done
if [ $WAITED -ge $MAX_WAIT ]; then
    echo "⚠️ Timeout aguardando container web. Tentando prosseguir mesmo assim..."
fi

# ==========================================
# Status
# ==========================================
echo "📦 Containers ativos:"
docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || docker ps

# ==========================================
# Criar Admin
# ==========================================
echo "👤 Configurando usuario administrador..."

# Garantir estrutura de tabelas, usuário administrador e sementes iniciais
ADMIN_OK=true
$COMPOSE_CMD exec -T web python init_app.py || ADMIN_OK=false

# ==========================================
# Informacoes finais
# ==========================================
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$IP" ] && IP="<IP da maquina>"

echo ""
echo "------------------------------------------------"
echo "✅ AssetTrack TI iniciado com sucesso!"
echo "------------------------------------------------"
echo "🌐 Local:    http://localhost:8000"
echo "🌐 Rede:     http://$IP:8000"
if [ "$IP" != "<IP da maquina>" ]; then
    echo "📖 Swagger:  http://$IP:8000/docs"
fi
if [ "$ADMIN_OK" = true ]; then
    echo "👤 Admin:    admin@example.com"
    echo "🔑 Senha:    admin"
else
    echo "⚠️  Admin nao pode ser criado. Verifique:"
    echo "   $COMPOSE_CMD exec web python create_admin.py"
fi
echo "------------------------------------------------"
echo "📜 Logs:"
echo "$COMPOSE_CMD logs -f"
echo "------------------------------------------------"
