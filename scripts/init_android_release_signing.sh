#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SIGNING_DIR="$ROOT_DIR/backend/uploads/android-signing"
KEYSTORE_FILE="$SIGNING_DIR/assettrack-release.jks"
ENV_FILE="$SIGNING_DIR/release-signing.env"
KEY_ALIAS="assettrack"

mkdir -p "$SIGNING_DIR"

if [ -f "$ENV_FILE" ] && [ -f "$KEYSTORE_FILE" ]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  echo "✅ Keystore de release já existe em $KEYSTORE_FILE"
  exit 0
fi

if ! command -v keytool >/dev/null 2>&1; then
  echo "❌ keytool não encontrado. Instale um JDK completo para gerar a assinatura de release."
  exit 1
fi

if ! command -v openssl >/dev/null 2>&1; then
  echo "❌ openssl não encontrado. Não foi possível gerar uma senha segura automaticamente."
  exit 1
fi

STORE_PASSWORD="$(openssl rand -hex 16)"
KEY_PASSWORD="$STORE_PASSWORD"

keytool -genkeypair \
  -keystore "$KEYSTORE_FILE" \
  -storepass "$STORE_PASSWORD" \
  -keypass "$KEY_PASSWORD" \
  -alias "$KEY_ALIAS" \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -dname "CN=AssetTrack TI, OU=Mobile, O=AssetTrack, L=Sao Paulo, S=SP, C=BR" >/dev/null

cat > "$ENV_FILE" <<EOF
APP_RELEASE_KEYSTORE_FILE=$KEYSTORE_FILE
APP_RELEASE_KEYSTORE_PASSWORD=$STORE_PASSWORD
APP_RELEASE_KEY_ALIAS=$KEY_ALIAS
APP_RELEASE_KEY_PASSWORD=$KEY_PASSWORD
EOF

chmod 600 "$KEYSTORE_FILE" "$ENV_FILE"

echo "✅ Keystore de release criado com sucesso."
echo "   Keystore: $KEYSTORE_FILE"
echo "   Arquivo de configuração: $ENV_FILE"
