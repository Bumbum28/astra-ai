#!/usr/bin/env bash
set -euo pipefail

FRONTEND_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMP_ROOT="$(mktemp -d)"

cleanup() {
  rm -rf "$TEMP_ROOT"
}
trap cleanup EXIT

case "$(uname -s)" in
  Darwin)
    PLATFORMS="android,ios,web,macos"
    ;;
  Linux)
    PLATFORMS="android,web,linux"
    ;;
  *)
    PLATFORMS="android,web"
    ;;
esac

flutter create \
  --project-name astra_ai \
  --org com.astra.ai \
  --platforms="$PLATFORMS" \
  --no-pub \
  "$TEMP_ROOT"

IFS=',' read -ra platform_list <<< "$PLATFORMS"
for platform in "${platform_list[@]}"; do
  rm -rf "$FRONTEND_ROOT/$platform"
  cp -R "$TEMP_ROOT/$platform" "$FRONTEND_ROOT/$platform"
done

cp "$TEMP_ROOT/.metadata" "$FRONTEND_ROOT/.metadata"

if [[ -d "$FRONTEND_ROOT/android/app/src/debug" ]]; then
  cp \
    "$FRONTEND_ROOT/tool/platform_overrides/android/app/src/debug/AndroidManifest.xml" \
    "$FRONTEND_ROOT/android/app/src/debug/AndroidManifest.xml"
fi

cd "$FRONTEND_ROOT"
flutter pub get
dart run build_runner build --delete-conflicting-outputs
dart format .
flutter analyze
flutter test
