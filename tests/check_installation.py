"""Exercise installation guards in a disposable Copy; never mutate the supplied game."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys, tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.common import PAYLOAD_PATHS, checked_game, digest
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game',type=Path,required=True);args=p.parse_args();source=checked_game(args.game)
results=[]
with tempfile.TemporaryDirectory(prefix='asairo-install-check-') as directory:
    base=Path(directory);game=base/'Test (Copy)';game.mkdir();shutil.copy2(source/'asairo.exe',game/'asairo.exe')
    def run(action,expected=0):
        r=subprocess.run([sys.executable,str(ROOT/'nvl-mode.py'),action,'--game',str(game)],capture_output=True,text=True)
        assert r.returncode==expected,(action,r.stdout,r.stderr)
        return r.stdout+r.stderr
    assert run('check').strip()=='ADV';results.append('clean Copy detected as ADV')
    assert 'NVL active' in run('enable');assert run('check').strip()=='NVL'
    for rel in PAYLOAD_PATHS:assert digest(game/rel)==digest(ROOT/'patch-files'/rel)
    results.append('enable installs exactly the expected payload')
    before=list((game/'_nvl_backups').iterdir());assert 'already active' in run('enable');assert list((game/'_nvl_backups').iterdir())==before
    results.append('enable is idempotent')
    target=game/'Scenario/01game.msc';backup=target.with_name(target.name+'.pre_tamper_backup');shutil.copy2(target,backup);target.write_bytes(target.read_bytes()+b'unknown')
    assert 'Unrecognized modified file' in run('disable',1);assert (game/'winmm.dll').exists();shutil.copy2(backup,target)
    results.append('unknown overrides refused before any payload removal')
    assert 'ADV active' in run('disable');assert all(not (game/rel).exists() for rel in PAYLOAD_PATHS)
    latest=sorted((game/'_nvl_backups').glob('mode_disable_*'))[-1]
    assert all(digest(latest/rel)==digest(ROOT/'patch-files'/rel) for rel in PAYLOAD_PATHS)
    results.append('disable preserves byte-identical backups of every removed file')
    outside=base/'outside';outside.mkdir();sentinel=outside/'01game.msc';sentinel.write_bytes(b'outside must remain untouched')
    shutil.rmtree(game/'Scenario');(game/'Scenario').symlink_to(outside,target_is_directory=True)
    assert 'symlink' in run('enable',1);assert sentinel.read_bytes()==b'outside must remain untouched';assert not (game/'winmm.dll').exists();(game/'Scenario').unlink()
    results.append('symlinked parent refused without writes outside Copy')
    (game/'Scenario').mkdir();trap=game/'Scenario/01game.msc.nvl_next';trap.symlink_to(sentinel)
    run('enable');assert sentinel.read_bytes()==b'outside must remain untouched';assert trap.is_symlink();run('disable')
    results.append('pre-existing staging symlink cannot redirect installation')
    original_exe=game/'asairo.exe.pre_test_backup';shutil.copy2(game/'asairo.exe',original_exe);(game/'asairo.exe').write_bytes(b'wrong executable')
    assert 'Unsupported' in run('enable',1);shutil.copy2(original_exe,game/'asairo.exe');results.append('unsupported executable refused')
    renamed=base/'Original';game.rename(renamed);game=renamed;assert 'separate directory' in run('enable',1);results.append('directory not marked Copy refused')
print(json.dumps({'passed':len(results),'checks':results},indent=2))
