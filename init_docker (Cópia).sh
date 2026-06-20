#!/bin/bash

# init_docker.sh - Automacao para inicializar AssetTrack TI via Docker/Podman no Ubuntu
set -e

echo "------------------------------------------------"
echo "🚀 Iniciando Automacao AssetTrack TI (Docker)"
echo "------------------------------------------------"

# 1. Verificar se Docker ou Podman esta instalado
if command -v docker &> /dev/null; then
    DOCKER_CMD="docker"
elif command -v podman &> /dev/null; then
    DOCKER_CMD="podman"
else
    echo "❌ Erro: Docker ou Podman nao encontrado. Por favor, instale um deles."
    exit 1
fi

# 2. Verificar Docker Compose
if $DOCKER_CMD compose version &> /dev/null; then
    COMPOSE_CMD="$DOCKER_CMD compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Erro: Docker Compose nao encontrado."
    exit 1
fi

echo "✅ Utilizando: $COMPOSE_CMD"

# 3. Configurar .env se nao existir
if [ ! -f ".env" ]; then
    echo "⚙️  Configurando arquivo .env a partir do exemplo..."
    cp .env.example .env
else
    echo "✅ Arquivo .env ja existe."
fi

# 4. Force stop web container (AppArmor-safe para Docker snap)
force_stop_web() {
    local WEB_CONTAINER
    WEB_CONTAINER=$($DOCKER_CMD ps -a --filter "name=^assettrack_ti-web" --format "{{.Names}}" 2>/dev/null | head -1)
    if [ -z "$WEB_CONTAINER" ]; then
        return 0
    fi

    # Tentar stop normal primeiro
    if $DOCKER_CMD stop "$WEB_CONTAINER" 2>/dev/null; then
        $DOCKER_CMD rm "$WEB_CONTAINER" 2>/dev/null || true
        return 0
    fi

    echo "⚠️ Container preso (AppArmor/snap). Usando metodo alternativo..."

    local OLD_NAME="${WEB_CONTAINER}-old-$(date +%Y%m%d%H%M%S)"
    $DOCKER_CMD rename "$WEB_CONTAINER" "$OLD_NAME" 2>/dev/null || true

    $DOCKER_CMD exec "$OLD_NAME" python3 -c "
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

    for i in $(seq 1 15); do
        if ! $DOCKER_CMD ps --filter "name=$OLD_NAME" --format "{{.Names}}" 2>/dev/null | grep -q .; then
            break
        fi
        sleep 1
    done

    $DOCKER_CMD rm -f "$OLD_NAME" 2>/dev/null || true
    for c in $($DOCKER_CMD ps -a --filter "name=assettrack_ti-web" --format "{{.Names}}" 2>/dev/null); do
        $DOCKER_CMD rm -f "$c" 2>/dev/null || true
    done
    echo "✅ Container antigo removido"
}

# 5. Derrubar containers antigos
echo "🛑 Parando containers antigos..."
if ! $COMPOSE_CMD down --remove-orphans 2>/dev/null; then
    force_stop_web
    $COMPOSE_CMD down --remove-orphans 2>/dev/null || true
fi

# 6. Subir containers
echo "🏗️  Construindo e subindo os containers..."
$COMPOSE_CMD up -d --build

# 7. Aguardar o banco de dados inicializar
echo "⏳ Aguardando o banco de dados estar pronto..."
sleep 10

# 8. Inicializar Usuarios (Admin)
echo "👤 Inicializando usuario Administrador..."
$COMPOSE_CMD exec -T web python create_admin.py || echo "⚠️ Usuario admin ja pode existir ou erro na criacao."
$COMPOSE_CMD exec -T web python activate_user_admin.py || true

# 9. Finalizacao
echo "------------------------------------------------"
echo "✅ Aplicacao inicializada com sucesso!"
echo "🌐 Acesse em: http://localhost:8000"
echo "📖 Documentacao: http://localhost:8000/docs"
echo "👤 Admin: admin@example.com / admin"
echo "------------------------------------------------"
echo "Para ver os logs, use: $COMPOSE_CMD logs -f"
