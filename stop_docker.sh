#!/bin/bash

# stop_docker.sh - Para os containers do AssetTrack TI
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

echo "🛑 Parando a aplicação AssetTrack TI..."
$COMPOSE_CMD down

echo "✅ Containers parados com sucesso."
