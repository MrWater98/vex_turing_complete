#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUITE_DIR="${OSS_CAD_SUITE:-"$ROOT_DIR/../VeriFlatten/oss-cad-suite"}"

if [[ -n "${YOSYS:-}" ]]; then
    exec "$YOSYS" "$@"
fi

YOSYS_BIN="$SUITE_DIR/libexec/yosys"
if [[ -x "$YOSYS_BIN" && -d "$SUITE_DIR/share/yosys" ]]; then
    LOADER="$SUITE_DIR/lib/ld-linux-x86-64.so.2"
    if [[ -x "$LOADER" ]]; then
        exec "$LOADER" --library-path "$SUITE_DIR/lib" "$YOSYS_BIN" "$@"
    fi
    exec "$YOSYS_BIN" "$@"
fi

if command -v yosys >/dev/null 2>&1; then
    exec yosys "$@"
fi

echo "Yosys not found. Expected $YOSYS_BIN or set YOSYS to its executable." >&2
exit 127
