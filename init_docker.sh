#!/bin/bash

# ==========================================
# AssetTrack TI - Inicialização Docker
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
    echo "❌ Docker não encontrado."
    echo "Instale com:"
    echo "apt install docker.io docker-compose-plugin -y"
    exit 1
fi

# ==========================================
# Verificar serviço Docker
# ==========================================
if command -v systemctl &> /dev/null; then
    if ! systemctl is-active --quiet docker; then
        echo "⚙️ Iniciando serviço Docker..."
        systemctl start docker
    fi
elif command -v service &> /dev/null; then
    if ! service docker status &> /dev/null; then
        echo "⚙️ Iniciando serviço Docker..."
        service docker start
    fi
fi

# ==========================================
# Verificar Docker Compose
# ==========================================
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose não encontrado."
    exit 1
fi

COMPOSE_CMD="docker compose"

echo "✅ Docker OK"
echo "✅ Docker Compose OK"

# ==========================================
# Criar .env se não existir
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
# Derrubar ambiente antigo
# ==========================================
echo "🧹 Limpando containers antigos..."
$COMPOSE_CMD down --remove-orphans || true

# ==========================================
# Build e Start
# ==========================================
echo "🏗️ Construindo containers..."
$COMPOSE_CMD up -d --build

# ==========================================
# Aguardar inicialização
# ==========================================
echo "⏳ Aguardando container web iniciar..."
MAX_WAIT=120
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    STATUS=$($COMPOSE_CMD ps --format json 2>/dev/null | python3 -c "
import sys, json
for line in sys.stdin:
    s = json.loads(line)
    if s.get('Service') == 'web' and s.get('State') == 'running':
        health = s.get('Health', '')
        if health == 'healthy' or health == '':
            print('ready')
            break
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
docker ps

# ==========================================
# Criar Admin
# ==========================================
echo "👤 Configurando usuário administrador..."

ADMIN_OK=true
$COMPOSE_CMD exec -T web python create_admin.py || ADMIN_OK=false
$COMPOSE_CMD exec -T web python activate_user_admin.py || ADMIN_OK=false
# ==========================================
# Informações finais
# ==========================================
IP=$(hostname -I | awk '{print $1}')
[ -z "$IP" ] && IP="<IP da máquina>"

echo ""
echo "------------------------------------------------"
echo "✅ AssetTrack TI iniciado com sucesso!"
echo "------------------------------------------------"
echo "🌐 Local:    http://localhost:8000"
echo "🌐 Rede:     http://$IP:8000"
if [ "$IP" != "<IP da máquina>" ]; then
    echo "📖 Swagger:  http://$IP:8000/docs"
fi
if [ "$ADMIN_OK" = true ]; then
    echo "👤 Admin:    admin@example.com"
    echo "🔑 Senha:    admin"
else
    echo "⚠️  Admin não pôde ser criado. Verifique:"
    echo "   $COMPOSE_CMD exec web python create_admin.py"
fi
echo "------------------------------------------------"
echo "📜 Logs:"
echo "$COMPOSE_CMD logs -f"
echo "------------------------------------------------"
