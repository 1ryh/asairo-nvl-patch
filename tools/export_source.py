#!/usr/bin/env python3
"""Export only reviewed public source files; exclude games, prefixes and extracted data."""
from pathlib import Path
import argparse, hashlib, json, shutil
ROOT=Path(__file__).resolve().parents[1]
FILES=[
    '.gitignore','readme.md','LICENSE','THIRD_PARTY_NOTICES.md',
    'docs/ENGINE.md','docs/TESTING.md','nvl-mode.py','launch-target.sh',
    'tools/common.py','tools/mpk.py','tools/panel.py','tools/resource_recipe.py',
    'tools/prepare_payload.py','tools/export_source.py',
    'hook/nvl_guard.c','hook/build.sh','hook/generate_forwarders.py','hook/winmm-exports.json',
    'patch-files/manifest.json','patch-files/winmm.dll',
    'tests/check_installation.py','.github/ISSUE_TEMPLATE/bug_report.md',
]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,help='A new directory; existing directories are refused')
    args=parser.parse_args();output=args.output.absolute()
    if output.exists() or output.is_symlink():raise SystemExit('Use a new output directory.')
    for relative in FILES:
        source=ROOT/relative
        if not source.is_file() or source.is_symlink():raise SystemExit('Missing or symlinked source: '+relative)
    output.mkdir(parents=True);manifest=[]
    for relative in FILES:
        source=ROOT/relative;destination=output/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
        manifest.append(dict(path=relative,sha256=hashlib.sha256(destination.read_bytes()).hexdigest()))
    (output/'SOURCE-MANIFEST.json').write_text(json.dumps({'files':manifest},indent=2)+'\n')
    print(f'Exported {len(FILES)} source/package files to {output}; no game archives, generated overrides or Wine prefix included.')
if __name__=='__main__':main()
