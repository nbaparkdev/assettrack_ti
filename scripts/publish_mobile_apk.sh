#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_UPLOADS_DIR="$ROOT_DIR/backend/uploads"

apk_source="${1:-}"
timestamp_utc="$(date -u +%Y.%m.%d.%H%M)"
version_code="${VITE_APP_VERSION_CODE:-$(date -u +%s)}"
version_name="${VITE_APP_VERSION_NAME:-$timestamp_utc}"
release_date="${VITE_APP_BUILD_TIMESTAMP:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"

if [ -z "$apk_source" ]; then
  echo "❌ Informe o APK já gerado para anexar à aplicação."
  echo "   Uso: $0 /caminho/AssetTrack-TI.apk"
  exit 1
fi

if [ ! -f "$apk_source" ]; then
  echo "❌ APK não encontrado: $apk_source"
  exit 1
fi

if [[ "${apk_source,,}" != *.apk ]]; then
  echo "❌ O arquivo informado precisa ter extensão .apk"
  exit 1
fi

apk_filename="$(basename "$apk_source")"

echo "------------------------------------------------"
echo "📱 Anexando APK do AssetTrack TI"
echo "------------------------------------------------"
echo "Versão:      ${version_name}"
echo "Código:      ${version_code}"
echo "Release date ${release_date}"
echo "Arquivo:     ${apk_source}"
echo "------------------------------------------------"

mkdir -p "$BACKEND_UPLOADS_DIR"

cp "$apk_source" "$BACKEND_UPLOADS_DIR/$apk_filename"
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
  "release_notes": "• APK anexado manualmente após build realizado via terminal.\\n• Download salvo no portal de backups e distribuição.\\n• Metadados de release atualizados no anexo."
}
EOF

echo "✅ APK anexado com sucesso:"
echo "   Arquivo:  $BACKEND_UPLOADS_DIR/$apk_filename"
echo "   Tamanho:  $apk_size_formatted"
echo "   Manifest: $BACKEND_UPLOADS_DIR/mobile-release.json"
