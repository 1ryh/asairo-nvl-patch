#!/usr/bin/env python3
"""Enable or disable exactly six validated overrides in a separate game Copy."""
import argparse, datetime, json, shutil, subprocess, sys, tempfile
from pathlib import Path
from tools.common import ROOT, DEFAULT_GAME, PAYLOAD_PATHS, checked_game, checked_destination, digest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'status', 'enable', 'disable'])
    parser.add_argument('--game', type=Path, default=DEFAULT_GAME, help='Installation directory ending in (Copy)')
    parser.add_argument('--payload', type=Path, default=ROOT/'patch-files')
    args = parser.parse_args()
    game = checked_game(args.game)
    payload = args.payload.resolve(strict=True)
    rows = json.loads((payload/'manifest.json').read_text())['files']
    if len(rows) != len(PAYLOAD_PATHS) or {row['path'] for row in rows} != PAYLOAD_PATHS:
        raise RuntimeError('Manifest must contain exactly the six documented override paths.')
    present = []
    for row in rows:
        relative = Path(row['path'])
        if digest(payload/relative) != row['sha256']:
            raise RuntimeError(f'Payload differs: {relative}')
        destination = checked_destination(game, relative)
        if destination.exists() and digest(destination) != row['sha256']:
            raise RuntimeError(f'Unrecognized modified file; left untouched: {destination}')
        present.append(destination.exists())
    state = 'NVL' if all(present) else 'ADV' if not any(present) else 'INCOMPLETE'
    if args.action in ['check', 'status']:
        print(state)
        if state == 'INCOMPLETE':
            raise RuntimeError('Run enable or disable before launching.')
        return
    process = subprocess.run(['pgrep', '-x', 'asairo.exe'], stdout=subprocess.DEVNULL)
    if process.returncode != 1:
        raise RuntimeError('Close every asairo.exe instance before switching modes (or check pgrep availability).')
    enable = args.action == 'enable'
    changes = [row for row, exists in zip(rows, present) if exists != enable]
    if not changes:
        print(state+' already active')
        return
    backup_root = game/'_nvl_backups'
    if backup_root.is_symlink():
        raise RuntimeError('Refusing symlinked backup directory.')
    backup = backup_root/('mode_'+args.action+'_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    backup.mkdir(parents=True)
    log = []
    for row in changes:
        relative = Path(row['path'])
        destination = checked_destination(game, relative)
        log.append(dict(path=row['path'], existed=destination.exists()))
        if destination.exists():
            prior = backup/relative
            prior.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, prior)
    (backup/'changes.json').write_text(json.dumps(log, ensure_ascii=False, indent=2))
    for row in changes:
        destination = checked_destination(game, row['path'])
        if enable:
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive temporary files cannot follow a pre-existing staging symlink.
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.nvl-', delete=False) as staged:
                staged_path = Path(staged.name)
                with (payload/row['path']).open('rb') as source:
                    shutil.copyfileobj(source, staged)
            try:
                staged_path.replace(destination)
            finally:
                staged_path.unlink(missing_ok=True)
        else:
            destination.unlink()  # Exact-hash override, backed up above.
    print(('NVL' if enable else 'ADV')+' active. Backup: '+str(backup))

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
