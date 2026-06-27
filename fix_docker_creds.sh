#!/bin/bash

echo "=============================================="
echo "  Fix Docker Credential Helper Issue"
echo "=============================================="
echo ""

DOCKER_CONFIG="$HOME/.docker/config.json"

if [ -f "$DOCKER_CONFIG" ]; then
    echo "✅ Arquivo config.json encontrado"
    echo ""
    
    # Backup do arquivo original
    cp "$DOCKER_CONFIG" "$DOCKER_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Backup criado"
    
    # Remover a linha com credsStore
    if grep -q '"credsStore":' "$DOCKER_CONFIG"; then
        echo "🔧 Removendo credsStore..."
        
        # Usar Python para editar o JSON corretamente (preservar a estrutura)
        python3 - <<END
import json
import os

config_path = "$DOCKER_CONFIG"

with open(config_path, 'r') as f:
    config = json.load(f)

if 'credsStore' in config:
    del config['credsStore']
    print("✅ credsStore removido")

with open(config_path, 'w') as f:
    json.dump(config, f, indent=4)

print("✅ Arquivo atualizado!")
END
        
    else
        echo "⚠️ credsStore não encontrado no arquivo"
    fi
    
    echo ""
    echo "✅ Arquivo config.json corrigido!"
    echo ""
    echo "Conteúdo atual:"
    echo "----------------------------------------"
    cat "$DOCKER_CONFIG"
    echo ""
    
else
    echo "❌ Arquivo config.json não encontrado em $DOCKER_CONFIG"
    exit 1
fi

echo ""
echo "=============================================="
echo "  Pronto! Agora você pode tentar novamente:"
echo "  bash init_docker.sh"
echo "=============================================="
