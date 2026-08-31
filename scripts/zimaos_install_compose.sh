#!/bin/bash

set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker nao encontrado. Instale/ative o Docker no ZimaOS antes de continuar."
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  docker compose version
  echo "Docker Compose v2 ja esta instalado."
  exit 0
fi

if command -v docker-compose >/dev/null 2>&1; then
  docker-compose version
  echo "docker-compose legado ja esta instalado."
  exit 0
fi

arch="$(uname -m)"
case "$arch" in
  x86_64 | amd64)
    compose_arch="x86_64"
    ;;
  aarch64 | arm64)
    compose_arch="aarch64"
    ;;
  armv7l)
    compose_arch="armv7"
    ;;
  *)
    echo "Arquitetura nao suportada automaticamente: $arch"
    exit 1
    ;;
esac

plugin_dir="${DOCKER_CONFIG:-$HOME/.docker}/cli-plugins"
plugin_path="$plugin_dir/docker-compose"
download_url="https://github.com/docker/compose/releases/latest/download/docker-compose-linux-${compose_arch}"

mkdir -p "$plugin_dir"

echo "Baixando Docker Compose para ${arch}..."
if command -v curl >/dev/null 2>&1; then
  curl -fL "$download_url" -o "$plugin_path"
elif command -v wget >/dev/null 2>&1; then
  wget -O "$plugin_path" "$download_url"
else
  echo "Nem curl nem wget foram encontrados. Instale um deles e tente novamente."
  exit 1
fi

chmod +x "$plugin_path"

echo "Docker Compose instalado em: $plugin_path"
docker compose version
