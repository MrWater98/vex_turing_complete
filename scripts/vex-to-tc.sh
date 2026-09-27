#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TECHLIB_DIR="$ROOT_DIR/vendor/TuringCompleteYosysTechlib"

usage() {
    echo "Usage: $0 <source.v> [top_module]" >&2
    exit 2
}

[[ $# -ge 1 && $# -le 2 ]] || usage
SOURCE="$(realpath "$1")"
[[ -f "$SOURCE" ]] || { echo "Verilog file not found: $SOURCE" >&2; exit 2; }
TOP="${2:-$(basename "${SOURCE%.v}")}"
[[ "$SOURCE" == *.v ]] || { echo "Expected a .v Verilog source file" >&2; exit 2; }
[[ "$TOP" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || { echo "Invalid Verilog top-module name: $TOP" >&2; exit 2; }

BUILD_DIR="$ROOT_DIR/build"
mkdir -p "$BUILD_DIR"
OUTPUT="$BUILD_DIR/$(basename "${SOURCE%.v}")_tc.v"
SAVE_NAME="${TC_SAVE_NAME:-$(basename "${SOURCE%.v}")}"
LEVEL="${TC_LEVEL:-component_factory}"
YOSYS_SCRIPT="$(mktemp "$BUILD_DIR/yosys-XXXXXX.ys")"
trap 'rm -f "$YOSYS_SCRIPT"' EXIT
FF_MAP="$BUILD_DIR/turing_complete_ff_map.v"
sed 's/ wire _TECHMAP_REMOVEINIT_Q_ = 1;//' "$TECHLIB_DIR/turing_complete_ff_map.v" > "$FF_MAP"

cat > "$YOSYS_SCRIPT" <<EOF
read_verilog -sv "$SOURCE"
hierarchy -check -top $TOP
proc; opt
flatten; opt
memory; opt
fsm; opt
techmap; opt
techmap -map "$FF_MAP"
abc -liberty "$TECHLIB_DIR/turing_complete_nand_focus_tech.lib"
clean -purge
write_verilog "$OUTPUT"
EOF

"$ROOT_DIR/scripts/yosys.sh" -s "$YOSYS_SCRIPT"

PYTHON="$ROOT_DIR/.venv/bin/python"
[[ -x "$PYTHON" ]] || { echo "Python environment missing. Run: python3 -m venv .venv && .venv/bin/pip install -e ./vendor/turing-complete-interface nimporter" >&2; exit 1; }
"$PYTHON" -m turing_complete_interface.from_verilog "$OUTPUT" -l "$LEVEL" -s "$SAVE_NAME"
