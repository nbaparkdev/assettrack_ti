#!/bin/bash
# ==========================================
# AssetTrack TI - Reset do Banco de Dados
# ==========================================
# Remove e recria o banco do zero (volume PostgreSQL).
# Cria o admin padrao automaticamente ao final.
#
# Uso:
#   ./scripts/reset_db.sh           # Reset limpo
#   ./scripts/reset_db.sh --backup  # Faz backup antes de resetar
# ==========================================

set -e
cd "$(dirname "$0")/.."

DO_BACKUP=false

for arg in "$@"; do
    case $arg in
        --backup) DO_BACKUP=true ;;
        --help|-h)
            echo "Uso: $0 [--backup]"
            echo "  --backup  Faz backup do banco antes de resetar"
            exit 0
            ;;
        *)
            echo "Parametro desconhecido: $arg"
            echo "Use --help para opcoes"
            exit 1
            ;;
    esac
done

echo "========================================"
echo " Reset do Banco de Dados - AssetTrack TI"
echo "========================================"
echo ""

# Confirmacao
echo "ATENCAO: Todos os dados serao PERMANENTEMENTE removidos."
read -rp "Digite 'SIM' para confirmar: " CONFIRM
if [ "$CONFIRM" != "SIM" ]; then
    echo "Cancelado."
    exit 0
fi

# Backup opcional
if [ "$DO_BACKUP" = true ] && [ -f "./scripts/backup.sh" ]; then
    echo ""
    echo "Executando backup antes do reset..."
    bash ./scripts/backup.sh
    echo ""
fi

# Derrubar containers e remover volume
echo "Parando containers e removendo volume do banco..."
docker compose down -v 2>/dev/null || true

# Garantir que volume foi removido
docker volume rm assettrack_ti_postgres_data 2>/dev/null || true

echo ""

# Subir ambiente
echo "Subindo containers..."
docker compose up -d

# Aguardar banco ficar saudavel
echo "Aguardando banco de dados..."
for i in $(seq 1 30); do
    if docker compose exec -T db pg_isready -U user -d assettrack 2>/dev/null; then
        echo ""
        echo "Banco pronto!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Timeout aguardando banco."
        exit 1
    fi
    printf "."
    sleep 2
done

# Aguardar web iniciar e criar tabelas
echo "Aguardando aplicacao iniciar..."
for i in $(seq 1 30); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
    if [ "$STATUS" = "200" ]; then
        echo "Aplicacao pronta!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Timeout aguardando aplicacao. Forcando criacao de tabelas..."
        docker compose exec -T web python -c "
import asyncio
from app.database import engine, Base
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
" 2>/dev/null || true
        break
    fi
    printf "."
    sleep 3
done

# Criar admin padrao
echo ""
echo "Criando usuario administrador..."
docker compose exec -T web python -c "
from app.database import engine
from sqlalchemy import text
from passlib.context import CryptContext
import asyncio

async def seed():
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    hashed = pwd_context.hash('admin')
    async with engine.begin() as conn:
        await conn.execute(text('''
            INSERT INTO users (nome, email, hashed_password, role, is_active)
            VALUES ('Administrador', 'admin@example.com', :pw, 'ADMIN', true)
            ON CONFLICT (email) DO NOTHING
        '''), {'pw': hashed})
    print('Admin criado: admin@example.com / admin')

asyncio.run(seed())
" 2>/dev/null

echo ""
echo "========================================"
echo " Reset concluido!"
echo "========================================"
echo ""
echo "  URL:    http://localhost:8000/login"
echo "  Email:  admin@example.com"
echo "  Senha:  admin"
echo ""
