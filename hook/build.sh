#!/bin/bash
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")" && pwd -P)
build_dir=${NVL_BUILD_DIR:-"$root/build"}
mkdir -p -- "$build_dir"
build_dir=$(cd -- "$build_dir" && pwd -P)
import_lib=${WINE_KERNEL32_LIB:-/usr/lib/wine/i386-windows/libkernel32.a}
if [[ ! -f "$import_lib" ]]; then
    echo 'Set WINE_KERNEL32_LIB to the 32-bit Wine libkernel32.a import library.' >&2
    exit 1
fi
if [[ -f "$build_dir/winmm.dll" ]]; then
    cp -p -- "$build_dir/winmm.dll" "$build_dir/winmm.dll.pre_build_$(date +%Y%m%d_%H%M%S_%N)"
fi
python3 "$root/generate_forwarders.py" "$build_dir"
clang --target=i686-pc-windows-msvc -O2 -fno-stack-protector -fno-builtin -I"$build_dir" -c "$root/nvl_guard.c" -o "$build_dir/nvl_guard.obj"
clang --target=i686-pc-windows-msvc -c "$build_dir/forwarders.s" -o "$build_dir/forwarders.obj"
lld-link /dll /nodefaultlib /safeseh:no /entry:DllMain@12 "$build_dir/nvl_guard.obj" "$build_dir/forwarders.obj" "/def:$build_dir/winmm.def" "/out:$build_dir/winmm.dll" "$import_lib"
echo "Built $build_dir/winmm.dll; the installed game DLL was not changed."
