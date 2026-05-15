#!/bin/bash

# init_docker.sh - Automação para inicializar AssetTrack TI via Docker/Podman no Ubuntu
set -e

echo "------------------------------------------------"
echo "🚀 Iniciando Automação AssetTrack TI (Docker)"
echo "------------------------------------------------"

# 1. Verificar se Docker ou Podman está instalado
if command -v docker &> /dev/null; then
    DOCKER_CMD="docker"
elif command -v podman &> /dev/null; then
    DOCKER_CMD="podman"
else
    echo "❌ Erro: Docker ou Podman não encontrado. Por favor, instale um deles."
    exit 1
fi

# 2. Verificar Docker Compose
if $DOCKER_CMD compose version &> /dev/null; then
    COMPOSE_CMD="$DOCKER_CMD compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Erro: Docker Compose não encontrado."
    exit 1
fi

echo "✅ Utilizando: $COMPOSE_CMD"

# 3. Configurar .env se não existir
if [ ! -f ".env" ]; then
    echo "⚙️  Configurando arquivo .env a partir do exemplo..."
    cp .env.example .env
else
    echo "✅ Arquivo .env já existe."
fi

# 4. Subir containers
echo "🏗️  Construindo e subindo os containers..."
$COMPOSE_CMD up -d --build

# 5. Aguardar o banco de dados inicializar
echo "⏳ Aguardando o banco de dados estar pronto..."
sleep 10

# 6. Inicializar Usuários (Admin)
echo "👤 Inicializando usuário Administrador..."
$COMPOSE_CMD exec web python create_admin.py || echo "⚠️ Usuário admin já pode existir ou erro na criação."
$COMPOSE_CMD exec web python activate_user_admin.py

# 7. Finalização
echo "------------------------------------------------"
echo "✅ Aplicação inicializada com sucesso!"
echo "🌐 Acesse em: http://localhost:8000"
echo "📖 Documentação: http://localhost:8000/docs"
echo "👤 Admin: admin@example.com / admin"
echo "------------------------------------------------"
echo "Para ver os logs, use: $COMPOSE_CMD logs -f"
