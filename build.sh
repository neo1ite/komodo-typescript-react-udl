#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUT=${1:-"$ROOT/../komodo-typescript-9.3.2-0.1.0.xpi"}

rm -f "$OUT"
cd "$ROOT"
zip -9 -r "$OUT" install.rdf components support LICENSE README.md \
    -x '*/__pycache__/*' '*.pyc' '*.pyo'

echo "$OUT"
