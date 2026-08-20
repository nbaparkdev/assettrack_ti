#!/bin/bash
# Script para ativar o usuário administrador no banco de dados

echo "Ativando o usuário administrador (admin@example.com)..."

docker exec assettrack_ti-db-1 psql -U user -d assettrack -c "UPDATE users SET is_active = true WHERE email = 'admin@example.com';"

if [ $? -eq 0 ]; then
  echo "✅ Administrador ativado com sucesso!"
else
  echo "❌ Erro ao tentar ativar o administrador. Verifique se o container do banco de dados está rodando."
fi
