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
- Exact-version checks, refusal of unknown overrides, and backups before removal or replacement.

## Requirements

### To install and play

- Your own complete, working installation of the game, copied into a **separate directory whose name ends in `(Copy)`**. Do not use a symlink to the original.
- The supported `asairo.exe`, with SHA-256:

  ```text
  40457ef359392a16a7486cb31a0ff7b0446fd4463822847b5e0a5c5dd6e3ef24
  ```

- Linux, Bash, **Python 3.11+**, and `pgrep` from procps/procps-ng. The installer/resource generator needs no third-party Python packages.
- A Wine/Proton installation capable of running the original game and its 32-bit dependencies. The tested environment is **CachyOS Wine 11.0**, supplied by `proton-cachyos-slr`.
- An already prepared **private Wine prefix inside the game Copy**, with the game's normal dependencies and Japanese fonts. The tested font is **MS Gothic**. Fonts, codecs and Windows components are not supplied by this patch.
- The `ja_JP.UTF-8` locale and a working graphical session. Audio playback additionally needs a working audio output.

The development prefix was a private clone of an existing Japanese-ready Textractor prefix. Textractor itself is not required. If cloning a prefix, close applications using the source first and localize profile-folder symlinks; do not run this patch against a shared original prefix. Setting up a new Wine installation or acquiring fonts is outside this patch's installer.

The prebuilt proxy is included; a compiler and Ghidra are **not required to play**. Other executable versions, native Windows and other Wine/Proton builds are not validated. The WinMM forwarding catalog is specific to the tested environment.

## Installation

Download or clone this repository. Run the following commands **from its root directory**.

1. Make an independent Copy of the working game and set its absolute path:

   ```bash
   export GAME_COPY="$HOME/Games/Asairo (Copy)"
   ```

   This directory must already contain `asairo.exe`, `Scenario.mpk` and the rest of the original game. Changing the variable does not copy or install the game.

2. Verify the executable:

   ```bash
   sha256sum "$GAME_COPY/asairo.exe"
   ```

   It must match the supported hash above. Do not bypass the version check.

3. Generate the native resources from your own Copy:

   ```bash
   python3 tools/prepare_payload.py --game "$GAME_COPY"
   ```

   This reads `Scenario.mpk` and creates the reviewed files under `patch-files/`. It leaves the game unchanged and verifies every generated file against the manifest. Game-derived scripts and graphics are generated locally rather than distributed in the source package.

4. Close every instance of the game, then install:

   ```bash
   python3 nvl-mode.py enable --game "$GAME_COPY"
   python3 nvl-mode.py check --game "$GAME_COPY"
   ```

   The check should print `NVL`. Unknown loose overrides are refused rather than overwritten; review any existing mod conflict before proceeding.

5. Configure the launcher and start:

   ```bash
   export ASAIRO_GAME_DIR="$GAME_COPY"
   export ASAIRO_PREFIX="$GAME_COPY/.wine-prepared"
   export ASAIRO_WINE="/usr/share/steam/compatibilitytools.d/proton-cachyos-slr/files/bin/wine"
   bash ./launch-target.sh
   ```

   `ASAIRO_PREFIX` must point to an existing prepared prefix inside the Copy. Set `ASAIRO_WINE` to an absolute path if your compatible runtime is installed elsewhere. These variables apply to the current shell; set them again or use a local wrapper for future launches.

The launcher checks the installed payload, selects the native WinMM proxy, sets the Japanese locale and snapshots saves before launching. Logs go to `logs/target-runtime.log`. `nvl-hook-status.txt` inside the game Copy should report that the native NVL hooks are active.

### Files installed

| File | Purpose |
| --- | --- |
| `Scenario/01game.msc` | Ordinary native NVL setup |
| `Scenario/01game_HIY.msc` | Ordinary viewpoint setup |
| `Scenario/01game_OTH.msc` | Ordinary viewpoint setup |
| `Scenario/01game_NAK.msc` | Ordinary viewpoint setup |
| `BG/NV00.mgr` | Generated rounded native panel |
| `winmm.dll` | Version-checked forwarding proxy and scoped hooks |

The executable and MPK archives are not edited. Backups are stored in the Copy's `_nvl_backups/` directory with unique timestamps. Leave space for save snapshots; they accumulate across launches.

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

Close every game instance first:

```bash
python3 nvl-mode.py disable --game "$GAME_COPY"
python3 nvl-mode.py check --game "$GAME_COPY"  # ADV
```

Only the six exact-hash overrides are removed, after backing them up. Original archive resources then take effect. Saves and archives are retained.

**Load NVL saves with NVL enabled.** They reference the generated native panel. After disabling, use a pre-NVL save or start a new game. Re-enable with:

```bash
python3 nvl-mode.py enable --game "$GAME_COPY"
```

## Updating

Before replacing a previous version, close the game and disable it using that version's installer and manifest. Keep its backups. Then update the repository, regenerate the resources, and enable the new version. This avoids treating an older DLL as an unknown override. Do not mix files from different versions or change manifest hashes merely to suppress an error.

## How it was made

Analysis of the existing Ghidra project identified native NVL functionality already present in the target's `01gamenov.msc` setup. Four ordinary ADV entry points were adapted to use that native presentation. The target's own parser and renderer still handle Japanese text and scenario commands.

Itsusora turned out to use **BGI/Ethornell**, not the same engine. It therefore serves as a visual and behavioral reference. No raw executable offsets or machine code were copied from it. On/off comparisons of its reading window informed the panel's geometry, transparency and corner coverage.

The generated panel uses a native BGRA bitmap inside an MGR resource. The normal reading area is 688×528 pixels at (56, 36), with a 13.25-pixel corner radius. Native text starts at (80, 58), uses 25 full-width columns and 13 rows, and accumulates paragraphs.

Two runtime hooks address native NVL edge cases:

- A scoped message-preparation hook reserves space before a paragraph, invokes the native page clear when needed, preserves its queued voice record and displays the visible speaker inline.
- A save hook temporarily restores the original message prefix during native serialization so display-only speaker formatting cannot corrupt hidden identities in saves.

The page estimate never inserts line breaks or positions glyphs. The engine retains CP932 parsing, native measurement, kinsoku, ruby, waits, voice timing and backlog formatting. Menus, choices and special text layouts are not globally redirected. See [engine notes](docs/ENGINE.md) for addresses, commands, safeguards and implementation details.

## Build the proxy from source

The prebuilt `patch-files/winmm.dll` is the runtime-tested binary. To build a separate development DLL, install Python, Clang, LLD and a **32-bit Wine `libkernel32.a` import library**:

```bash
export WINE_KERNEL32_LIB="/usr/lib/wine/i386-windows/libkernel32.a"
bash hook/build.sh
```

The result is `hook/build/winmm.dll`; the script does not replace the installed DLL. Set `NVL_BUILD_DIR` to use another build directory. Existing build DLLs receive timestamped backups.

The verified toolchain was Python 3.14.7, Clang 22.1.8 and LLD 22.1.8, targeting `i686-pc-windows-msvc`. The checked rebuild had identical code/data sections to the tested binary; its PE timestamp changed. Do not simply overwrite an installed DLL or bypass the manifest. Changes intended for release require an updated payload manifest and fresh runtime validation.

## Diagnostics and troubleshooting

Tracing is disabled by default. Enable it for a short diagnostic session:

```bash
ASAIRO_NVL_TRACE=1 bash ./launch-target.sh
```

The Copy receives `nvl-trace.bin` and `nvl-state.bin`; prior traces and saves are backed up at launch. The first records raw CP932 message bytes and pagination decisions. The second records scoped native name/voice state. These are binary diagnostic files, not UTF-8 text files. Disable tracing for normal play.

| Symptom | Check |
| --- | --- |
| Unsupported executable | Compare the SHA-256; this patch supports one executable version. |
| Missing payload file | Run `tools/prepare_payload.py` before installation. |
| `INCOMPLETE` state | Close the game and run `enable` or `disable` to finish a recognized partial installation. |
| Unknown override or symlink refusal | Check for another mod or redirected directory. The installer leaves it untouched. |
| ADV appearance remains | Launch through this script, check `NVL` status and inspect `nvl-hook-status.txt`. |
| Missing/tofu Japanese glyphs | Check the private prefix's Japanese fonts and locale. Do not change scenario encoding. |
| Voice is silent | Check native master/voice/character settings and the Wine audio output device. |
| A special scene looks different | Some centered/cinematic layouts are intentionally preserved. |
| NVL save fails after disabling | Re-enable NVL before loading that save. |

See [validation and limitations](docs/TESTING.md) for the exact test scope. Report a reproducible issue through the repository's Issues tab using the bug-report template. Include the executable hash, runtime, font, hook status and steps; do not upload the game or a full scenario dump.

## Project layout

```text
readme.md                  Installation and usage
LICENSE                    MIT license for original project code
docs/                      Engine notes and validation scope
nvl-mode.py                Checked installation and rollback
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

Prepare the payload and close the game before running the disposable installation checks:

```bash
python3 tests/check_installation.py --game "$GAME_COPY"
```

A fixture test does not establish full-game compatibility. Include remaining limitations in changes and issue reports. Avoid committing game files, generated game-derived overrides, proprietary scenario text, fonts, saves or Wine prefixes.

## Credits and license

Reverse engineering and validation used Ghidra, Wine/Proton, Clang/LLD and GARbro's MPK/MGR format research. Itsusora supplied the presentation reference. The target and reference games remain the work of their respective creators.

The project's original code and documentation are available under the **[MIT License](LICENSE)**. Game material and third-party components are excluded from that grant; see [third-party notices](THIRD_PARTY_NOTICES.md).
