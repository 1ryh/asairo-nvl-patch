Download **Asairo-NVL-Installer.exe** below. No Python installation, terminal commands or source-code download is needed.

1. Copy your working game to a separate folder ending in `(Copy)`, such as `C:\Games\Asairo (Copy)`.
2. Close the game, open the installer, and choose that folder.
3. Click **Install / Repair**, then launch `asairo.exe` from the patched folder.

The installer checks the supported executable, generates resources locally from your game, verifies the patch hashes, and backs up saves before installing. Use **Check** to inspect the installation or **Remove patch** to return to ADV. Unknown overrides are refused. The game executable and archives are not modified.

The installer targets 64-bit Windows 10/11. The game and patch DLL remain 32-bit. Game files, fonts and codecs are not included.

**Experimental:** existing gameplay validation covers one executable under Wine/Proton. Native Windows gameplay and the WinMM forwarding catalog on Windows remain unvalidated. Installer tests and packaging checks do not establish gameplay compatibility.

Load NVL saves with the patch enabled. After removal, use a pre-NVL save or start a new game. Backups are stored in the selected game's `_nvl_backups` folder.
