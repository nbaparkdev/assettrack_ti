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
if ! systemctl is-active --quiet docker; then
    echo "⚙️ Iniciando Docker..."
    systemctl start docker
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
docker ps || true

# ==========================================
# Rebuild e Restart
# ==========================================
echo "🏗️ Reconstruindo aplicação..."

$COMPOSE_CMD up -d --build

# ==========================================
# Aguardar estabilização
# ==========================================
echo "⏳ Aguardando containers..."
sleep 15

# ==========================================
# Limpeza segura
# ==========================================
echo "🧹 Limpando imagens antigas..."
docker image prune -f

# ==========================================
# Status final
# ==========================================
echo "📦 Containers ativos:"
docker ps

# ==========================================
# Informações
# ==========================================
IP=$(hostname -I | awk '{print $1}')

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
