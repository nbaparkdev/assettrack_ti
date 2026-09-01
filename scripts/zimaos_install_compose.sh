#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker nao encontrado. Instale/ative o Docker no ZimaOS antes de continuar."
  exit 1
fi

if DOCKER_CONFIG="$ROOT_DIR/.zimaos/docker-config" docker compose version >/dev/null 2>&1; then
  docker compose version
  echo "Docker Compose v2 ja esta instalado."
  exit 0
fi

if command -v docker-compose >/dev/null 2>&1 && docker-compose version 2>/dev/null | grep -qE 'Docker Compose version v?2\.'; then
  docker-compose version
  echo "Docker Compose v2 ja esta instalado."
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

bin_dir="$ROOT_DIR/.zimaos/bin"
compose_path="$bin_dir/docker-compose"
download_url="https://github.com/docker/compose/releases/latest/download/docker-compose-linux-${compose_arch}"

mkdir -p "$bin_dir" "$ROOT_DIR/.zimaos/docker-config"

echo "Baixando docker-compose para ${arch}..."
if command -v curl >/dev/null 2>&1; then
  curl -fL "$download_url" -o "$compose_path"
elif command -v wget >/dev/null 2>&1; then
  wget -O "$compose_path" "$download_url"
else
  echo "Nem curl nem wget foram encontrados. Instale um deles e tente novamente."
  exit 1
fi

chmod +x "$compose_path"

echo "docker-compose instalado em: $compose_path"
"$compose_path" version
echo ""
echo "Agora rode:"
echo "  ./scripts/zimaos_start.sh"
