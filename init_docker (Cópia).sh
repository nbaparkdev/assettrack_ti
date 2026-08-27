#!/bin/bash

# Compatibilidade: este nome antigo apontava para a aplicação Python legada.
# A aplicação atual é Go + React e usa o fluxo oficial abaixo.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$ROOT_DIR/init_docker.sh" "$@"
