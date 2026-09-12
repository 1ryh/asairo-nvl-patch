#!/usr/bin/env python3
"""Generate five game-derived resources locally without modifying an installation."""
import argparse, hashlib, json, sys
from pathlib import Path
from common import ROOT, DEFAULT_GAME, checked_game
from resource_recipe import generate

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, default=DEFAULT_GAME)
    parser.add_argument('--output', type=Path, default=ROOT/'patch-files')
    args = parser.parse_args()
    game = checked_game(args.game)
    manifest = json.loads((ROOT/'patch-files/manifest.json').read_text())
    files, changes = generate(game)
    files['winmm.dll'] = (ROOT/'patch-files/winmm.dll').read_bytes()
    for row in manifest['files']:
        if hashlib.sha256(files[row['path']]).hexdigest() != row['sha256']:
            raise RuntimeError('Generated resource differs from the reviewed version: '+row['path'])
    output = args.output.absolute()
    if output.resolve() == game or output.resolve().is_relative_to(game):
        raise RuntimeError('Generate outside the game Copy, then use nvl-mode.py to install with backups.')
    for relative, data in files.items():
        target = output/relative
        if target.is_symlink() or any(p.is_symlink() for p in target.parents):
            raise RuntimeError(f'Refusing symlinked output: {target}')
        if target.exists() and target.read_bytes() != data:
            raise RuntimeError(f'Existing output differs; use a fresh --output directory: {target}')
    target_manifest = output/'manifest.json'
    if target_manifest.is_symlink() or (target_manifest.exists() and json.loads(target_manifest.read_text()) != manifest):
        raise RuntimeError('Existing manifest differs; use a fresh --output directory.')
    for relative, data in files.items():
        target = output/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with target.open('xb') as destination:
                destination.write(data)
    if not target_manifest.exists():
        target_manifest.write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Generated and verified six payload files in {output}. Game files unchanged.')

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, AssertionError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
