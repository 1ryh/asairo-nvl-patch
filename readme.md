# Asairo Native NVL

An experimental native NVL presentation patch for **きっと、澄みわたる朝色よりも、**.

Ordinary scenario dialogue uses a large reading area with rounded corners, a black background at approximately **55% opacity**, and the CG visible through it. The appearance is based on **いつか、届く、あの空に。** (Itsusora). Japanese text, ruby, voices, history, choices and timing continue through the target game's native engine.

**Status:** implemented and tested on one exact executable under Wine/Proton. The extended run passed **7,766 boundary checks across 21,829 message preparations**. Full-route compatibility remains unverified; see [validation and limitations](docs/TESTING.md).


<img width="801" height="598" alt="image" src="https://github.com/user-attachments/assets/5988722f-4f7d-47ad-ae73-8860db71ed6a" />


## Features

- Wide native Japanese text area with paragraph accumulation and page clearing.
- Itsusora-matched transparency and rounded corners; approximately 45% CG transmission.
- Inline visible speaker names while preserving hidden voice identities.
- Original CP932/Shift-JIS parsing, glyph measurement, kinsoku, ruby and text controls.
- Native centered/cinematic layouts, choices, backlog, auto, skip and save/load retained.
- Reversible loose-resource overrides and two narrowly scoped runtime hooks.
- Exact-version and payload checks to identify unsupported executables and conflicting overrides.

## Requirements

- Your own complete, working installation of the game in a **separate folder whose name ends in `(Copy)`**, for example `C:\Games\Asairo (Copy)`. Copy the actual files; do not use a symlink or junction to the original installation.
- The supported `asairo.exe`, with SHA-256:

  ```text
  40457ef359392a16a7486cb31a0ff7b0446fd4463822847b5e0a5c5dd6e3ef24
  ```

- **Python 3.11+** to generate and verify the patch resources. No third-party Python packages are required.
- A setup that already runs the original game correctly, including Japanese text, fonts and audio. Fonts, codecs and game files are not supplied.

The prebuilt `winmm.dll` is included; a compiler and Ghidra are **not required to play**. Windows instructions are below, with Linux/Wine instructions in a separate section. **Native Windows gameplay is not yet validated.** Existing gameplay results come from CachyOS Wine 11.0 (`proton-cachyos-slr`), and the proxy's WinMM forwarding catalog was built for that environment. Other executable versions and runtimes are not validated; see [validation and limitations](docs/TESTING.md).

## Installation on Windows

Download and extract this repository, or clone it. Open **PowerShell in the repository folder**. Stop and resolve any command error before continuing. These examples use `py -3`; if your Python installation provides `python` instead, substitute that command and make sure it is version 3.11 or newer.

1. Make an independent copy of the working game, including its saves, then set the path:

   ```powershell
   $GameCopy = "C:\Games\Asairo (Copy)"
   ```

   This folder must already contain `asairo.exe`, `Scenario.mpk` and the rest of the original game. Setting the variable does not copy or install the game. Keep the original installation and saves as your backup.

2. Verify the executable:

   ```powershell
   Get-FileHash -Algorithm SHA256 -LiteralPath "$GameCopy\asairo.exe"
   ```

   The hash must match the supported hash above (letter case does not matter). Do not bypass the version check.

3. Generate the patch resources from your own copy:

   ```powershell
   py -3 tools/prepare_payload.py --game "$GameCopy"
   ```

   This reads `Scenario.mpk`, generates the files under `patch-files/`, and verifies them against the manifest without changing the game. Game-derived scripts and graphics are generated locally rather than distributed.

4. Close every instance of the game, then check for conflicts:

   ```powershell
   py -3 nvl-mode.py check --game "$GameCopy"
   ```

   A clean copy should report `ADV`. **Stop if the command reports an error**: unknown overrides must be reviewed before installing. `NVL` means all six patch files are already installed; `INCOMPLETE` means only some are present.

5. For a clean `ADV` copy, install the six files listed below. In File Explorer, copy the generated `Scenario` and `BG` folders and `winmm.dll` from `patch-files` into the game copy, preserving the folder structure. Alternatively, run:

   ```powershell
   $PatchFiles = @(
       "Scenario/01game.msc",
       "Scenario/01game_HIY.msc",
       "Scenario/01game_OTH.msc",
       "Scenario/01game_NAK.msc",
       "BG/NV00.mgr",
       "winmm.dll"
   )
   foreach ($Relative in $PatchFiles) {
       $Destination = Join-Path $GameCopy $Relative
       New-Item -ItemType Directory -Force -Path (Split-Path $Destination) | Out-Null
       Copy-Item -LiteralPath (Join-Path "patch-files" $Relative) -Destination $Destination -ErrorAction Stop
   }
   py -3 nvl-mode.py check --game "$GameCopy"
   ```

   The final check must print `NVL`. The Windows workflow uses manual copying because the current `enable` and `disable` commands require Linux `pgrep`. Manual copying does not create automatic backups; keep your untouched game copy and saves.

6. Launch `asairo.exe` from the patched game folder, using the same locale setup you use for the original game. No Wine launcher or Wine environment variables are needed on Windows. Check `nvl-hook-status.txt` in that folder to confirm the native NVL hooks are active.

If installation was interrupted, close the game and run the check again. An `INCOMPLETE` result with no unknown-file error can be repaired by copying all six files again and checking for `NVL`. Resolve any other error before copying or removing files.

## Installation on Linux / Wine / Proton

This workflow additionally requires Bash, `pgrep` from procps/procps-ng, `ja_JP.UTF-8`, a graphical session, and a compatible Wine/Proton runtime with the game's 32-bit dependencies. Prepare a **private Wine prefix inside the game copy** with Japanese fonts; the tested font is MS Gothic. Textractor is not required.

From the repository root, set the path to an existing independent game copy, verify its executable against the hash above, generate the resources, and install with the game closed:

```bash
export GAME_COPY="$HOME/Games/Asairo (Copy)"
sha256sum "$GAME_COPY/asairo.exe"
python3 tools/prepare_payload.py --game "$GAME_COPY"
python3 nvl-mode.py enable --game "$GAME_COPY"
python3 nvl-mode.py check --game "$GAME_COPY"
```

Stop if any command fails. The final check should print `NVL`. Unknown loose overrides are refused rather than overwritten.

Configure and run the launcher:

```bash
export ASAIRO_GAME_DIR="$GAME_COPY"
export ASAIRO_PREFIX="$GAME_COPY/.wine-prepared"
export ASAIRO_WINE="/usr/share/steam/compatibilitytools.d/proton-cachyos-slr/files/bin/wine"
bash ./launch-target.sh
```

`ASAIRO_PREFIX` must point to an existing prepared prefix inside the copy. Set `ASAIRO_WINE` to the absolute path of your compatible runtime. These variables apply to the current shell; set them again or use a local wrapper for future launches.

The launcher checks the payload, selects the native WinMM proxy, sets the Japanese locale and snapshots saves before launching. Logs go to `logs/target-runtime.log`. Check `nvl-hook-status.txt` inside the game copy for active hooks. If cloning a prefix, close its applications first and localize profile-folder symlinks; do not use a shared original prefix.

## Files installed

| File | Purpose |
| --- | --- |
| `Scenario/01game.msc` | Ordinary native NVL setup |
| `Scenario/01game_HIY.msc` | Ordinary viewpoint setup |
| `Scenario/01game_OTH.msc` | Ordinary viewpoint setup |
| `Scenario/01game_NAK.msc` | Ordinary viewpoint setup |
| `BG/NV00.mgr` | Generated rounded native panel |
| `winmm.dll` | Version-checked forwarding proxy and scoped hooks |

The executable and MPK archives are not edited. The Linux installer and launcher store timestamped backups in the copy's `_nvl_backups/` folder. Save snapshots accumulate across launches. On Windows, back up saves yourself before testing or changing patch versions.

## Controls

These remain the game's native controls:

| Key | Action |
| --- | --- |
| Enter | Complete or advance text |
| Space | Hide/show the reading area |
| C | Open the native menu |
| V | Replay the current voice |
| A | Auto mode |
| Ctrl | Skip according to the native setting |
| PageUp | Backlog |
| F1 / F2 | Load / save |
| Escape | Minimize the game |

The native configuration screen still controls text speed, sound and skip behavior.

## Disable or reinstall

**Load NVL saves with NVL enabled.** They reference the generated native panel. After disabling, use a pre-NVL save or start a new game.

### Windows

1. Close every instance of the game and back up your saves.
2. From the repository folder, run `py -3 nvl-mode.py check --game "$GameCopy"`. A fully installed patch reports `NVL`. Stop on an unknown-file or version error.
3. Back up the six installed files in the table above to a separate folder, preserving their relative paths. Then delete **only those six files** from the game copy. Keep the `Scenario` and `BG` folders and any other files inside them.
4. Run the same check again; it should report `ADV`. Original archive resources now take effect.

For a recognized `INCOMPLETE` installation, back up and remove only the listed files that are present, then check for `ADV`. To re-enable, follow the Windows installation steps again.

### Linux / Wine / Proton

Close every game instance first:

```bash
python3 nvl-mode.py disable --game "$GAME_COPY"
python3 nvl-mode.py check --game "$GAME_COPY"  # ADV
```

Only the six exact-hash overrides are removed, after backing them up. Saves and archives are retained. Re-enable with:

```bash
python3 nvl-mode.py enable --game "$GAME_COPY"
```

## Updating

Close the game and disable the old patch using the instructions and manifest from that version. Keep its backups. Then update the repository, regenerate the resources, and install the new version. This avoids treating an older DLL as an unknown override. Do not mix files from different versions or change manifest hashes to suppress an error.

## How it was made

Analysis of the existing Ghidra project identified native NVL functionality already present in the target's `01gamenov.msc` setup. Four ordinary ADV entry points were adapted to use that native presentation. The target's own parser and renderer still handle Japanese text and scenario commands.

Itsusora turned out to use **BGI/Ethornell**, not the same engine. It therefore serves as a visual and behavioral reference. No raw executable offsets or machine code were copied from it. On/off comparisons of its reading window informed the panel's geometry, transparency and corner coverage.

The generated panel uses a native BGRA bitmap inside an MGR resource. The normal reading area is 688×528 pixels at (56, 36), with a 13.25-pixel corner radius. Native text starts at (80, 58), uses 25 full-width columns and 13 rows, and accumulates paragraphs.

Two runtime hooks address native NVL edge cases:

- A scoped message-preparation hook reserves space before a paragraph, invokes the native page clear when needed, preserves its queued voice record and displays the visible speaker inline.
- A save hook temporarily restores the original message prefix during native serialization so display-only speaker formatting cannot corrupt hidden identities in saves.

The page estimate never inserts line breaks or positions glyphs. The engine retains CP932 parsing, native measurement, kinsoku, ruby, waits, voice timing and backlog formatting. Menus, choices and special text layouts are not globally redirected. See [engine notes](docs/ENGINE.md) for addresses, commands, safeguards and implementation details.

## Build the proxy from source (Linux toolchain)

The prebuilt `patch-files/winmm.dll` is the runtime-tested binary. To build a separate development DLL, install Python, Clang, LLD and a **32-bit Wine `libkernel32.a` import library**:

```bash
export WINE_KERNEL32_LIB="/usr/lib/wine/i386-windows/libkernel32.a"
bash hook/build.sh
```

The result is `hook/build/winmm.dll`; the script does not replace the installed DLL. Set `NVL_BUILD_DIR` to use another build directory. Existing build DLLs receive timestamped backups.

The verified toolchain was Python 3.14.7, Clang 22.1.8 and LLD 22.1.8, targeting `i686-pc-windows-msvc`. The checked rebuild had identical code/data sections to the tested binary; its PE timestamp changed. Do not simply overwrite an installed DLL or bypass the manifest. Changes intended for release require an updated payload manifest and fresh runtime validation.

## Diagnostics and troubleshooting

Tracing is disabled by default. For a short diagnostic session on Windows, launch from PowerShell:

```powershell
$env:ASAIRO_NVL_TRACE = "1"
Start-Process -FilePath "$GameCopy\asairo.exe" -WorkingDirectory "$GameCopy" -Wait
Remove-Item Env:ASAIRO_NVL_TRACE
```

On Linux / Wine:

```bash
ASAIRO_NVL_TRACE=1 bash ./launch-target.sh
```

The game copy receives `nvl-trace.bin` and `nvl-state.bin`. The Wine launcher backs up prior traces and saves at launch; on Windows, copy any diagnostics you want to keep before starting another session. The first records raw CP932 message bytes and pagination decisions. The second records scoped native name/voice state. These are binary diagnostic files, not UTF-8 text files. Disable tracing for normal play.

| Symptom | Check |
| --- | --- |
| Unsupported executable | Compare the SHA-256; this patch supports one executable version. |
| Missing payload file | Run `tools/prepare_payload.py` before installation. |
| `INCOMPLETE` state | Close the game and follow the repair or removal steps for your platform. |
| Unknown override or symlink refusal | Check for another mod or redirected directory. The installer leaves it untouched. |
| ADV appearance remains | Check for `NVL` and inspect `nvl-hook-status.txt`; use `launch-target.sh` on Wine. |
| Missing/tofu Japanese glyphs | Check Japanese fonts and the locale setup used for the original game (inside the private prefix on Wine). Do not change scenario encoding. |
| Voice is silent | Check native master/voice/character settings and your audio output device. |
| A special scene looks different | Some centered/cinematic layouts are intentionally preserved. |
| NVL save fails after disabling | Re-enable NVL before loading that save. |

See [validation and limitations](docs/TESTING.md) for the exact test scope. Report a reproducible issue through the repository's Issues tab using the bug-report template. Include the executable hash, Windows version or Wine/Proton runtime, font, hook status and steps; do not upload the game or a full scenario dump.

## Project layout

```text
readme.md                  Installation and usage
LICENSE                    MIT license for original project code
docs/                      Engine notes and validation scope
nvl-mode.py                Payload checks; Linux installation and rollback
launch-target.sh           Private-prefix Wine launcher
tools/                     Local resource generation and source export
hook/                      Proxy source, export catalog and build scripts
patch-files/manifest.json  Reviewed payload hashes
patch-files/winmm.dll      Tested original-code proxy
tests/                    Disposable installation checks
```

To export a clean local source tree, choose a directory that does not already exist:

```bash
python3 tools/export_source.py --output /path/to/new/asairo-nvl-source
```

The export includes the files above and a checksum manifest. It does not publish or contact GitHub. Generated resources, game installations, prefixes, saves, extracted material and local research artifacts are excluded from source export and version control. The development workspace may contain them locally; they are not repository dependencies to redistribute.

## Contributing

Keep experiments inside independent Copies. Preserve native text parsing and calling conventions, tie binary changes to understood code, retain backups, and document actual gameplay checks. Test the affected layout plus save/load, voice and choices when relevant. Do not replace native Japanese wrapping with byte or character slicing.

On Linux, prepare the payload and close the game before running the disposable installation checks (these exercise the installer that requires `pgrep`):

```bash
python3 tests/check_installation.py --game "$GAME_COPY"
```

A fixture test does not establish full-game compatibility. Include remaining limitations in changes and issue reports. Avoid committing game files, generated game-derived overrides, proprietary scenario text, fonts, saves or Wine prefixes.

## Credits and license

Reverse engineering and validation used Ghidra, Wine/Proton, Clang/LLD and GARbro's MPK/MGR format research. Itsusora supplied the presentation reference. The target and reference games remain the work of their respective creators.

The project's original code and documentation are available under the **[MIT License](LICENSE)**. Game material and third-party components are excluded from that grant; see [third-party notices](THIRD_PARTY_NOTICES.md).
