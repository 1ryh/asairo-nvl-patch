"""Checked installation operations shared by the graphical installer."""
import csv
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from tools.common import ROOT, PAYLOAD_PATHS, checked_game, checked_destination, digest
from tools.resource_recipe import generate


def reject_link(path):
    path = Path(path)
    for item in (path, *path.parents):
        if item.is_symlink() or (item.exists() and getattr(item.lstat(), 'st_file_attributes', 0) & 0x400):
            raise RuntimeError(f'Use real folders and files, not links or junctions: {item}')


def game_folder(path):
    reject_link(path)
    game = checked_game(path)
    reject_link(game / 'asairo.exe')
    return game


def manifest():
    rows = json.loads((ROOT / 'patch-files/manifest.json').read_text(encoding='utf-8'))['files']
    if len(rows) != len(PAYLOAD_PATHS) or {row['path'] for row in rows} != PAYLOAD_PATHS:
        raise RuntimeError('The installer manifest is invalid. Download the installer again.')
    return rows


def require_closed():
    if os.name == 'nt':
        system = Path(os.environ['SystemRoot']) / 'System32/tasklist.exe'
        result = subprocess.run(
            [str(system), '/FI', 'IMAGENAME eq asairo.exe', '/FO', 'CSV', '/NH'],
            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW,
            stdin=subprocess.DEVNULL, timeout=20,
        )
        if result.returncode != 0:
            raise RuntimeError('Could not check running games. Close the game and try again.')
        rows = csv.reader(io.StringIO(result.stdout.decode('utf-8', errors='replace')))
        running = any(row and row[0].casefold() == 'asairo.exe' for row in rows)
    else:
        result = subprocess.run(['pgrep', '-x', 'asairo.exe'], capture_output=True, timeout=20)
        if result.returncode not in (0, 1):
            raise RuntimeError('Could not check running games.')
        running = result.returncode == 0
    if running:
        raise RuntimeError('Close every instance of asairo.exe before installing or removing the patch.')


def inspect(game, rows):
    present = []
    for row in rows:
        destination = checked_destination(game, row['path'])
        reject_link(destination)
        if destination.exists() and (not destination.is_file() or digest(destination) != row['sha256']):
            raise RuntimeError(f"Another mod or an unknown file is present. Nothing was changed:\n{destination}")
        present.append(destination.exists())
    return present


def status(path):
    game = game_folder(path)
    present = inspect(game, manifest())
    return 'NVL' if all(present) else 'ADV' if not any(present) else 'INCOMPLETE'


def payload(game, rows):
    reject_link(game / 'Scenario.mpk')
    files, _ = generate(game)
    files['winmm.dll'] = (ROOT / 'patch-files/winmm.dll').read_bytes()
    for row in rows:
        if hashlib.sha256(files[row['path']]).hexdigest() != row['sha256']:
            raise RuntimeError('Generated patch files do not match this release. Nothing was installed.')
    return files


def snapshot_saves(game, backup):
    saves = game / 'save'
    reject_link(saves)
    if saves.exists():
        for directory, folders, files in os.walk(saves):
            for name in folders + files:
                reject_link(Path(directory) / name)
        shutil.copytree(saves, backup / 'save')


def replace_bytes(destination, data):
    reject_link(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.nvl-', delete=False) as staged:
        temporary = Path(staged.name)
        try:
            staged.write(data)
        except BaseException:
            staged.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def change(path, enable, progress=lambda message: None):
    game = game_folder(path)
    require_closed()
    rows = manifest()
    present = inspect(game, rows)
    changes = [row for row, exists in zip(rows, present) if exists != enable]
    mode = 'NVL' if enable else 'ADV'
    if not changes:
        return f'{mode} is already active.'
    progress('Generating and verifying patch resources…' if enable else 'Checking installed files…')
    files = payload(game, rows) if enable else {}
    # Recheck after generation before backing up or changing the installation.
    require_closed()
    if inspect(game, rows) != present:
        raise RuntimeError('The game folder changed during preparation. Please try again.')
    backup_root = game / '_nvl_backups'
    reject_link(backup_root)
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup = backup_root / ('mode_' + ('enable_' if enable else 'disable_') + stamp)
    backup.mkdir(parents=True)
    progress('Backing up saves and existing patch files…')
    snapshot_saves(game, backup)
    for row in changes:
        relative = row['path']
        source = game / relative
        if source.exists():
            target = backup / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    (backup / 'changes.json').write_text(json.dumps([
        {'path': row['path'], 'existed': (game / row['path']).exists()} for row in changes
    ], indent=2), encoding='utf-8')
    require_closed()
    if inspect(game, rows) != present:
        raise RuntimeError('The game folder changed during backup. No patch files were changed.')
    progress('Installing patch…' if enable else 'Removing patch…')
    completed = []
    try:
        for row in changes:
            destination = checked_destination(game, row['path'])
            reject_link(destination)
            if enable:
                replace_bytes(destination, files[row['path']])
            else:
                destination.unlink()
            completed.append(row)
    except Exception as error:
        try:
            for row in reversed(completed):
                destination = game / row['path']
                reject_link(destination)
                previous = backup / row['path']
                if previous.exists():
                    replace_bytes(destination, previous.read_bytes())
                else:
                    destination.unlink(missing_ok=True)
        except Exception as rollback_error:
            raise RuntimeError(f'Installation stopped and rollback could not finish. Backups: {backup}\n{rollback_error}') from error
        raise RuntimeError(f'The operation failed; completed changes were rolled back. Backups: {backup}\n{error}') from error
    return f'{mode} is active.\nBackups: {backup}'
