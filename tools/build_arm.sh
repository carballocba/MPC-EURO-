#!/usr/bin/env bash
# Local open-source Zig cross compiler; no Docker emulation or physical device.
set -euo pipefail
cd "$(dirname "$0")/.."
ZIG_BIN="${ZIG_BIN:-$(pwd)/build/toolchain/ziglang/zig}"
if [ ! -x "$ZIG_BIN" ]; then
  python3 -m pip install --require-hashes --no-deps --target build/toolchain -r tools/zig-requirements.txt
fi
mkdir -p build/arm
export ZIG_GLOBAL_CACHE_DIR="$(pwd)/build/zig-cache"
export ZIG_LOCAL_CACHE_DIR="$(pwd)/build/zig-local-cache"
for unit in plugin repeat; do
  "$ZIG_BIN" cc -target arm-linux-gnueabihf.2.31 -mcpu=cortex_a9 \
    -std=c11 -O2 -Wall -Wextra -Werror -ffp-contract=off -fPIC -fvisibility=hidden \
    -ffunction-sections -fdata-sections -Ibuild -Isrc -c "src/$unit.c" -o "build/arm/$unit.o"
done
"$ZIG_BIN" cc -target arm-linux-gnueabihf.2.31 -mcpu=cortex_a9 \
  -s -shared build/arm/plugin.o build/arm/repeat.o -lm -pthread \
  -Wl,--gc-sections -Wl,--version-script=src/exports.map \
  -Wl,--no-undefined -Wl,--build-id=none -o build/arm/beatrepeat.so
python3 tools/validate_arm.py
