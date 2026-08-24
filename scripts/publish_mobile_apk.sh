#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
ANDROID_DIR="$FRONTEND_DIR/android"
BACKEND_UPLOADS_DIR="$ROOT_DIR/backend/uploads"

APK_DEBUG_PATH="$ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"
APK_RELEASE_PATH="$ANDROID_DIR/app/build/outputs/apk/release/app-release.apk"

APP_RELEASE_KEYSTORE_FILE="${APP_RELEASE_KEYSTORE_FILE:-${APP_RELEASE_KEYSTORE:-}}"
APP_RELEASE_KEYSTORE_PASSWORD="${APP_RELEASE_KEYSTORE_PASSWORD:-${APP_RELEASE_STORE_PASSWORD:-}}"
APP_RELEASE_KEY_ALIAS="${APP_RELEASE_KEY_ALIAS:-${APP_RELEASE_KEY_ALIAS_NAME:-}}"
APP_RELEASE_KEY_PASSWORD="${APP_RELEASE_KEY_PASSWORD:-${APP_RELEASE_KEY_PASSWORD_VALUE:-}}"
ENV_FILE="$ROOT_DIR/backend/uploads/android-signing/release-signing.env"

if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  APP_RELEASE_KEYSTORE_FILE="${APP_RELEASE_KEYSTORE_FILE:-${APP_RELEASE_KEYSTORE:-}}"
  APP_RELEASE_KEYSTORE_PASSWORD="${APP_RELEASE_KEYSTORE_PASSWORD:-${APP_RELEASE_STORE_PASSWORD:-}}"
  APP_RELEASE_KEY_ALIAS="${APP_RELEASE_KEY_ALIAS:-${APP_RELEASE_KEY_ALIAS_NAME:-}}"
  APP_RELEASE_KEY_PASSWORD="${APP_RELEASE_KEY_PASSWORD:-${APP_RELEASE_KEY_PASSWORD_VALUE:-}}"
fi

timestamp_utc="$(date -u +%Y.%m.%d.%H%M)"
version_code="${VITE_APP_VERSION_CODE:-$(date -u +%s)}"
version_name="${VITE_APP_VERSION_NAME:-$timestamp_utc}"
release_date="${VITE_APP_BUILD_TIMESTAMP:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
apk_filename="AssetTrack-TI-v${version_name}.apk"

if ! command -v npm >/dev/null 2>&1; then
  echo "❌ npm não encontrado. Não foi possível gerar o APK."
  exit 1
fi

if ! command -v java >/dev/null 2>&1; then
  echo "❌ Java não encontrado. Instale o JDK para compilar o APK."
  exit 1
fi

if [ ! -x "$ANDROID_DIR/gradlew" ] && [ ! -x "$ANDROID_DIR/gradlew.bat" ]; then
  echo "❌ Gradle Wrapper não encontrado em $ANDROID_DIR."
  exit 1
fi

echo "------------------------------------------------"
echo "📱 Publicando APK do AssetTrack TI"
echo "------------------------------------------------"
echo "Versão:      ${version_name}"
echo "Código:      ${version_code}"
echo "Release date ${release_date}"
echo "------------------------------------------------"

echo "⚙️  Sincronizando frontend com Capacitor..."
(cd "$FRONTEND_DIR" && npm run mobile:sync)

build_type="debug"
gradle_args=(
  "-PappVersionCode=$version_code"
  "-PappVersionName=$version_name"
)

if [ -n "$APP_RELEASE_KEYSTORE_FILE" ] && [ -n "$APP_RELEASE_KEYSTORE_PASSWORD" ] && [ -n "$APP_RELEASE_KEY_ALIAS" ] && [ -n "$APP_RELEASE_KEY_PASSWORD" ] && [ -f "$APP_RELEASE_KEYSTORE_FILE" ]; then
  echo "🔐 Keystore de release encontrado. Gerando APK assinada de produção..."
  build_type="release"
  gradle_args+=(
    "-PappKeystoreFile=$APP_RELEASE_KEYSTORE_FILE"
    "-PappKeystorePassword=$APP_RELEASE_KEYSTORE_PASSWORD"
    "-PappKeyAlias=$APP_RELEASE_KEY_ALIAS"
    "-PappKeyPassword=$APP_RELEASE_KEY_PASSWORD"
  )
else
  if [ -x "$ROOT_DIR/scripts/init_android_release_signing.sh" ]; then
    echo "🔧 Nenhum keystore de release foi encontrado. Criando uma assinatura local para release..."
    "$ROOT_DIR/scripts/init_android_release_signing.sh"
    if [ -f "$ENV_FILE" ]; then
      # shellcheck disable=SC1090
      source "$ENV_FILE"
      APP_RELEASE_KEYSTORE_FILE="${APP_RELEASE_KEYSTORE_FILE:-${APP_RELEASE_KEYSTORE:-}}"
      APP_RELEASE_KEYSTORE_PASSWORD="${APP_RELEASE_KEYSTORE_PASSWORD:-${APP_RELEASE_STORE_PASSWORD:-}}"
      APP_RELEASE_KEY_ALIAS="${APP_RELEASE_KEY_ALIAS:-${APP_RELEASE_KEY_ALIAS_NAME:-}}"
      APP_RELEASE_KEY_PASSWORD="${APP_RELEASE_KEY_PASSWORD:-${APP_RELEASE_KEY_PASSWORD_VALUE:-}}"
    fi
  fi

  if [ -n "$APP_RELEASE_KEYSTORE_FILE" ] && [ -n "$APP_RELEASE_KEYSTORE_PASSWORD" ] && [ -n "$APP_RELEASE_KEY_ALIAS" ] && [ -n "$APP_RELEASE_KEY_PASSWORD" ] && [ -f "$APP_RELEASE_KEYSTORE_FILE" ]; then
    echo "🔐 Assinatura de release local pronta. Gerando APK assinada de produção..."
    build_type="release"
    gradle_args+=(
      "-PappKeystoreFile=$APP_RELEASE_KEYSTORE_FILE"
      "-PappKeystorePassword=$APP_RELEASE_KEYSTORE_PASSWORD"
      "-PappKeyAlias=$APP_RELEASE_KEY_ALIAS"
      "-PappKeyPassword=$APP_RELEASE_KEY_PASSWORD"
    )
  else
    echo "⚠️ Keystore de produção não configurado. Gerando APK debug assinada pelo Gradle como fallback."
    echo "   Para release assinada, defina: APP_RELEASE_KEYSTORE_FILE, APP_RELEASE_KEYSTORE_PASSWORD, APP_RELEASE_KEY_ALIAS e APP_RELEASE_KEY_PASSWORD."
  fi
fi

echo "🏗️  Compilando APK Android (${build_type})..."
(cd "$ANDROID_DIR" && ./gradlew "assemble${build_type^}" "${gradle_args[@]}")

apk_source=""
if [ "$build_type" = "release" ] && [ -f "$APK_RELEASE_PATH" ]; then
  apk_source="$APK_RELEASE_PATH"
elif [ -f "$APK_DEBUG_PATH" ]; then
  apk_source="$APK_DEBUG_PATH"
elif [ -f "$APK_RELEASE_PATH" ]; then
  apk_source="$APK_RELEASE_PATH"
fi

if [ -z "$apk_source" ]; then
  echo "❌ APK não encontrado após o build."
  exit 1
fi

mkdir -p "$BACKEND_UPLOADS_DIR"

cp "$apk_source" "$BACKEND_UPLOADS_DIR/$apk_filename"
cp "$apk_source" "$BACKEND_UPLOADS_DIR/app-debug.apk"
cp "$apk_source" "$BACKEND_UPLOADS_DIR/AssetTrack-TI.apk"

apk_size_bytes="$(stat -c %s "$BACKEND_UPLOADS_DIR/$apk_filename")"
apk_size_formatted="$(python3 - <<PY
size_bytes = int("$apk_size_bytes")
print(f"{size_bytes / (1024 * 1024):.1f} MB")
PY
)"

cat > "$BACKEND_UPLOADS_DIR/mobile-release.json" <<EOF
{
  "version_code": ${version_code},
  "version_name": "${version_name}",
  "release_date": "${release_date}",
  "apk_filename": "${apk_filename}",
  "apk_size_bytes": ${apk_size_bytes},
  "apk_size_formatted": "${apk_size_formatted}",
  "min_android_version": "Android 7.0 (Nougat) ou superior",
  "release_notes": "• APK gerado automaticamente a partir da versão mais recente da aplicação.\\n• Download versionado salvo no portal de backups e distribuição.\\n• Metadados de release atualizados na publicação."
}
EOF

echo "✅ APK publicado com sucesso:"
echo "   Arquivo:  $BACKEND_UPLOADS_DIR/$apk_filename"
echo "   Tamanho:  $apk_size_formatted"
echo "   Manifest: $BACKEND_UPLOADS_DIR/mobile-release.json"
