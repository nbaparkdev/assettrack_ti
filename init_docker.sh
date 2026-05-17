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
if ! systemctl is-active --quiet docker; then
    echo "⚙️ Iniciando serviço Docker..."
    systemctl start docker
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
echo "⏳ Aguardando containers iniciarem..."
sleep 20

# ==========================================
# Status
# ==========================================
echo "📦 Containers ativos:"
docker ps

# ==========================================
# Criar Admin
# ==========================================
echo "👤 Configurando usuário administrador..."

$COMPOSE_CMD exec -T web python create_admin.py || true
$COMPOSE_CMD exec -T web python activate_user_admin.py || true

# ==========================================
# Informações finais
# ==========================================
IP=$(hostname -I | awk '{print $1}')

echo ""
echo "------------------------------------------------"
echo "✅ AssetTrack TI iniciado com sucesso!"
echo "------------------------------------------------"
echo "🌐 Local:    http://localhost:8000"
echo "🌐 Rede:     http://$IP:8000"
echo "📖 Swagger:  http://$IP:8000/docs"
echo "👤 Admin:    admin@example.com"
echo "🔑 Senha:    admin"
echo "------------------------------------------------"
echo "📜 Logs:"
echo "$COMPOSE_CMD logs -f"
echo "------------------------------------------------"
