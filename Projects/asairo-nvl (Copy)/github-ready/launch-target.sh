#!/bin/bash
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")" && pwd -P)
game_dir=${ASAIRO_GAME_DIR:-"$root/games/きっと、澄みわたる朝色よりも、 (Copy)"}
mode=$(python3 "$root/nvl-mode.py" check --game "$game_dir")
cd -- "$game_dir"
game_dir=$PWD
wine_bin=${ASAIRO_WINE:-/usr/share/steam/compatibilitytools.d/proton-cachyos-slr/files/bin/wine}
if [[ ! -x "$wine_bin" ]]; then
    echo 'Set ASAIRO_WINE to the absolute path of a compatible Wine/Proton wine executable.' >&2
    exit 1
fi
export WINEPREFIX=${ASAIRO_PREFIX:-"$game_dir/.wine-prepared"}
python3 - <<'PY'
from pathlib import Path
import os
prefix=Path(os.environ['WINEPREFIX'])
if not prefix.is_absolute() or not prefix.is_dir() or not prefix.resolve().is_relative_to(Path.cwd().resolve()):
    raise SystemExit('Use an existing private Wine prefix inside the game Copy (default: .wine-prepared).')
PY
export LANG=ja_JP.UTF-8 LC_ALL=ja_JP.UTF-8
export WINEDEBUG=${WINEDEBUG:--all} ASAIRO_NVL_TRACE=${ASAIRO_NVL_TRACE:-0}
if [[ "$mode" == NVL ]]; then
    export WINEDLLOVERRIDES='winmm=n,b'
else
    export WINEDLLOVERRIDES='winmm=b'
fi
python3 - <<'PY'
from pathlib import Path
import shutil,datetime,os
root=Path.cwd();parent=root/'_nvl_backups'
if parent.is_symlink():raise SystemExit('Refusing symlinked backup directory.')
for name in ['save','nvl-hook-status.txt','nvl-trace.bin','nvl-state.bin']:
    if (root/name).is_symlink():raise SystemExit('Refusing symlinked runtime file/directory: '+name)
backup=parent/('launch_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'));backup.mkdir(parents=True)
if (root/'save').exists():shutil.copytree(root/'save',backup/'save')
for name in ['nvl-hook-status.txt']+(['nvl-trace.bin','nvl-state.bin'] if os.environ.get('ASAIRO_NVL_TRACE')=='1' else []):
    if (root/name).exists():shutil.copy2(root/name,backup/name)
PY
mkdir -p -- "$root/logs"
exec "$wine_bin" asairo.exe >> "$root/logs/target-runtime.log" 2>&1
