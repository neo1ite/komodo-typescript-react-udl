#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VERSION=$(sed -n 's|.*<em:version>\([^<]*\)</em:version>.*|\1|p' "$ROOT/install.rdf" | head -n 1)
# TypeScript 7.0 intentionally ships without a stable programmatic API.
# Komodo's semantic services need the JavaScript LanguageService API, so the
# extension bundles the last JavaScript implementation: TypeScript 6.0.3.
TYPESCRIPT_API_VERSION=${TYPESCRIPT_API_VERSION:-6.0.3}

if [ -z "$VERSION" ]; then
    echo "build.sh: cannot determine extension version from install.rdf" >&2
    exit 1
fi

OUT=${1:-"$ROOT/komodo-typescript-9.3.2-${VERSION}.xpi"}
TMP=$(mktemp -d "${TMPDIR:-/tmp}/komodo-typescript-build.XXXXXX")
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

typescript_version() {
    sed -n 's|.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*|\1|p' \
        "$1/package.json" 2>/dev/null | head -n 1
}

is_pinned_typescript_api() {
    [ -f "$1/lib/typescript.js" ] || return 1
    [ "$(typescript_version "$1")" = "$TYPESCRIPT_API_VERSION" ]
}

find_typescript_root() {
    # Explicit override is trusted for development/compatibility testing, but
    # it still must expose the JavaScript programmatic API expected by Komodo.
    if [ -n "${TYPESCRIPT_ROOT:-}" ] && [ -f "$TYPESCRIPT_ROOT/lib/typescript.js" ]; then
        printf '%s\n' "$TYPESCRIPT_ROOT"
        return 0
    fi

    if is_pinned_typescript_api "$ROOT/node_modules/typescript"; then
        printf '%s\n' "$ROOT/node_modules/typescript"
        return 0
    fi

    if command -v npm >/dev/null 2>&1; then
        GLOBAL_ROOT=$(npm root -g 2>/dev/null || true)
        if [ -n "$GLOBAL_ROOT" ] && is_pinned_typescript_api "$GLOBAL_ROOT/typescript"; then
            printf '%s\n' "$GLOBAL_ROOT/typescript"
            return 0
        fi
    fi

    return 1
}

TS_ROOT=$(find_typescript_root || true)
if [ -z "$TS_ROOT" ]; then
    if ! command -v npm >/dev/null 2>&1; then
        echo "build.sh: npm is required to bundle TypeScript ${TYPESCRIPT_API_VERSION} API runtime" >&2
        exit 1
    fi

    echo "build.sh: downloading TypeScript ${TYPESCRIPT_API_VERSION} JavaScript API runtime" >&2
    npm install \
        --prefix "$TMP/npm" \
        --no-save \
        --ignore-scripts \
        --no-audit \
        --no-fund \
        "typescript@${TYPESCRIPT_API_VERSION}" >/dev/null
    TS_ROOT="$TMP/npm/node_modules/typescript"
fi

if [ ! -f "$TS_ROOT/lib/typescript.js" ]; then
    echo "build.sh: selected TypeScript package does not expose lib/typescript.js" >&2
    exit 1
fi

mkdir -p "$TMP/vendor/typescript"
cp -a "$TS_ROOT/lib" "$TMP/vendor/typescript/"
for file in LICENSE.txt package.json README.md SECURITY.md ThirdPartyNoticeText.txt; do
    if [ -f "$TS_ROOT/$file" ]; then
        cp -a "$TS_ROOT/$file" "$TMP/vendor/typescript/$file"
    fi
done

rm -f "$OUT"
cd "$ROOT"
zip -9 -r "$OUT" \
    install.rdf chrome.manifest components pylib support skin test \
    LICENSE README.md docs \
    -x '*/__pycache__/*' '*.pyc' '*.pyo' '.git/*'

cd "$TMP"
zip -9 -r "$OUT" vendor

printf '%s\n' "$OUT"
