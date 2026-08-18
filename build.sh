#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VERSION=$(sed -n 's|.*<em:version>\([^<]*\)</em:version>.*|\1|p' "$ROOT/install.rdf" | head -n 1)

if [ -z "$VERSION" ]; then
    echo "build.sh: cannot determine extension version from install.rdf" >&2
    exit 1
fi

OUT=${1:-"$ROOT/komodo-typescript-9.3.2-${VERSION}.xpi"}

rm -f "$OUT"
cd "$ROOT"
zip -9 -r "$OUT" \
    install.rdf chrome.manifest components content pylib support skin test \
    LICENSE README.md docs \
    -x '*/__pycache__/*' '*.pyc' '*.pyo' '.git/*'

printf '%s\n' "$OUT"
