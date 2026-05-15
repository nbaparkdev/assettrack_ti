#!/bin/bash

# update_docker.sh - Atualiza e reinicia a aplicação AssetTrack TI
set -e

# Detectar comando (docker ou podman)
if command -v docker &> /dev/null; then
    DOCKER_CMD="docker"
elif command -v podman &> /dev/null; then
    DOCKER_CMD="podman"
else
    echo "❌ Docker/Podman não encontrado."
    exit 1
fi

if $DOCKER_CMD compose version &> /dev/null; then
    COMPOSE_CMD="$DOCKER_CMD compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "🔄 Atualizando AssetTrack TI..."

# 1. Pull changes (opcional, se estiver usando git)
if [ -d ".git" ]; then
    echo "📥 Baixando últimas alterações do Git..."
    git pull
fi

# 2. Reconstruir e subir
echo "🏗️  Reconstruindo containers..."
$COMPOSE_CMD up -d --build

# 3. Limpar imagens órfãs/não utilizadas (opcional para economizar espaço)
echo "🧹 Limpando imagens antigas..."
$DOCKER_CMD image prune -f

echo "------------------------------------------------"
echo "✅ Aplicação atualizada e reiniciada com sucesso!"
echo "🌐 Acesse em: http://localhost:8000"
echo "------------------------------------------------"
