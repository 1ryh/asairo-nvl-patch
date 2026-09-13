"""Build on Windows: bundle Python, Tk and original-code patch assets only."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    if os.name != 'nt':
        raise SystemExit('Build this executable on Windows, or use the Windows installer GitHub Actions workflow.')
    subprocess.run([
        sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile',
        '--windowed', '--noupx', '--name', 'Asairo-NVL-Installer',
        '--add-data', 'patch-files/manifest.json:patch-files',
        '--add-data', 'patch-files/winmm.dll:patch-files',
        '--add-data', 'LICENSE:.', '--add-data', 'THIRD_PARTY_NOTICES.md:.',
        'install_windows.py',
    ], cwd=ROOT, check=True)
    executable = ROOT / 'dist/Asairo-NVL-Installer.exe'
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    (ROOT / 'dist/SHA256SUMS.txt').write_text(f'{digest}  {executable.name}\n', encoding='ascii')

if __name__ == '__main__':
    main()
