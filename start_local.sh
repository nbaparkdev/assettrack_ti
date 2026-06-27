#!/bin/bash

# Abortar em caso de erros e variáveis indefinidas
set -euo pipefail

echo "=========================================="
echo "  AssetTrack TI - Modo Local"
echo "=========================================="
echo ""

# Ir para pasta do projeto
cd "$(dirname "$0")"

# 1. Verificar se python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Erro: O Python 3 não está instalado neste sistema!"
    echo "Instale-o usando o gerenciador de pacotes do seu sistema (ex: sudo apt install python3)"
    exit 1
fi

# 2. Verificar se a porta 8000 já está ocupada
echo "🔍 Verificando porta 8000..."
PORT_BUSY=false
if command -v ss &> /dev/null; then
    if ss -tln | grep -q ":8000 "; then
        PORT_BUSY=true
    fi
elif command -v netstat &> /dev/null; then
    if netstat -tln | grep -q ":8000 "; then
        PORT_BUSY=true
    fi
elif command -v lsof &> /dev/null; then
    if lsof -i :8000 &> /dev/null; then
        PORT_BUSY=true
    fi
fi

if [ "$PORT_BUSY" = true ]; then
    echo "⚠️  Alerta: A porta 8000 já está em uso!"
    echo "Verifique se a aplicação já não está rodando em Docker ou por outro processo."
    echo "Caso deseje encerrar o Docker ativo, execute: bash stop_docker.sh"
    echo ""
    read -rp "Deseja tentar iniciar mesmo assim? (s/N): " TRY_START
    if [[ ! "$TRY_START" =~ ^[sS]$ ]]; then
        echo "❌ Execução abortada pelo usuário."
        exit 1
    fi
fi

# 3. Verificar se venv existe
if [ ! -d ".venv" ]; then
    echo "🔧 Criando ambiente virtual..."
    if ! python3 -m venv .venv 2>/dev/null; then
        echo "❌ Erro ao criar ambiente virtual (.venv)!"
        echo "Em sistemas Debian/Ubuntu, você pode precisar instalar o pacote python3-venv:"
        echo "   sudo apt update && sudo apt install python3-venv -y"
        exit 1
    fi
fi

# 4. Ativar venv
echo "🔧 Ativando ambiente virtual..."
# shellcheck disable=SC1091
source .venv/bin/activate

# 5. Instalar dependências se necessário
echo "🔧 Verificando dependências..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip -q
    pip install -q -r requirements.txt
else
    echo "⚠️  Aviso: requirements.txt não encontrado. Pulando instalação de pacotes."
fi

# 6. Criar pastas necessárias se não existirem
mkdir -p static
mkdir -p static/uploads   # Para PDFs e anexos de contratos (módulo de Compras)

# 7. Inicializar banco de dados e criar usuário admin
echo ""
echo "🔧 Inicializando banco de dados..."
python init_app.py

# Iniciar servidor
echo ""
echo "🚀 Iniciando AssetTrack TI..."
echo "🌐 Acesse: http://localhost:8000"
echo "📖 Swagger: http://localhost:8000/docs"
echo ""
echo "=========================================="
echo ""

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
