"""Exact-version and Copy-directory guards shared by installation tools."""
from pathlib import Path
import hashlib
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GAME = ROOT / 'games/きっと、澄みわたる朝色よりも、 (Copy)'
EXPECTED_EXE = '40457ef359392a16a7486cb31a0ff7b0446fd4463822847b5e0a5c5dd6e3ef24'
PAYLOAD_PATHS = {'Scenario/01game.msc', 'Scenario/01game_HIY.msc', 'Scenario/01game_OTH.msc', 'Scenario/01game_NAK.msc', 'BG/NV00.mgr', 'winmm.dll'}
def digest(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()
def checked_game(path):
    supplied = Path(path).expanduser().absolute()
    game = supplied.resolve(strict=True)
    if supplied.is_symlink() or not game.name.casefold().endswith('(copy)'):
        raise RuntimeError('Use a separate directory ending in (Copy), not an original installation or a symlink.')
    if (game/'asairo.exe').is_symlink() or digest(game/'asairo.exe') != EXPECTED_EXE:
        raise RuntimeError('Unsupported or symlinked executable; no files changed.')
    return game
def checked_destination(game, relative):
    relative = Path(relative)
    if relative.as_posix() not in PAYLOAD_PATHS:
        raise RuntimeError(f'Unexpected payload path: {relative}')
    current = game
    for component in relative.parts:
        current = current/component
        if current.is_symlink():
            raise RuntimeError(f'Refusing symlink in installation path: {current}')
    return current
