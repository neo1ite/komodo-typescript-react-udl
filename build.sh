#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VERSION=$(sed -n 's|.*<em:version>\([^<]*\)</em:version>.*|\1|p' "$ROOT/install.rdf" | head -n 1)
TYPESCRIPT_VERSION=${TYPESCRIPT_VERSION:-7.0.2}

if [ -z "$VERSION" ]; then
    echo "build.sh: cannot determine extension version from install.rdf" >&2
    exit 1
fi

OUT=${1:-"$ROOT/komodo-typescript-9.3.2-${VERSION}.xpi"}
TMP=$(mktemp -d "${TMPDIR:-/tmp}/komodo-typescript-build.XXXXXX")
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

find_typescript_root() {
    if [ -n "${TYPESCRIPT_ROOT:-}" ] && [ -f "$TYPESCRIPT_ROOT/lib/typescript.js" ]; then
        printf '%s\n' "$TYPESCRIPT_ROOT"
        return 0
    fi

    if [ -f "$ROOT/node_modules/typescript/lib/typescript.js" ]; then
        printf '%s\n' "$ROOT/node_modules/typescript"
        return 0
    fi

    if command -v npm >/dev/null 2>&1; then
        GLOBAL_ROOT=$(npm root -g 2>/dev/null || true)
        if [ -n "$GLOBAL_ROOT" ] && [ -f "$GLOBAL_ROOT/typescript/lib/typescript.js" ]; then
            printf '%s\n' "$GLOBAL_ROOT/typescript"
            return 0
        fi
    fi

    return 1
}

TS_ROOT=$(find_typescript_root || true)
if [ -z "$TS_ROOT" ]; then
    if ! command -v npm >/dev/null 2>&1; then
        echo "build.sh: npm is required to bundle TypeScript ${TYPESCRIPT_VERSION}" >&2
        exit 1
    fi

    echo "build.sh: downloading TypeScript ${TYPESCRIPT_VERSION} for bundled LanguageService" >&2
    npm install \
        --prefix "$TMP/npm" \
        --no-save \
        --ignore-scripts \
        --no-audit \
        --no-fund \
        "typescript@${TYPESCRIPT_VERSION}" >/dev/null
    TS_ROOT="$TMP/npm/node_modules/typescript"
fi

mkdir -p "$TMP/vendor/typescript"
cp -a "$TS_ROOT/lib" "$TMP/vendor/typescript/"
for file in LICENSE.txt package.json README.md; do
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
