# Validation and limitations

This is an implemented, tested experimental patch. Full-route compatibility is not claimed.

## Gameplay evidence

The extended final-payload run recorded **21,829 live message preparations**, **2,714 native pre-message clears**, and **7,766 adjacent source-message boundary checks** with **zero failures** and **zero oversized reservations**. Preparations include repetitions after save/load. Boundary checks cover directly adjacent source-message pairs, not every pair separated by VM commands.

Uniquely matched records identify the modules `asairo0104`, `0105`, `0106`, `0201`, `0202` and the tested branch of `0203`. Ambiguous shared strings are not counted as proof of visiting another module. The run contained 671 ruby-bearing messages, 563 hidden-name messages and 231 messages with embedded effects. There were 1,292 preparations outside ordinary geometry, left to native behavior. No invalid voiced actor index was recorded in scoped diagnostics.

| Check | Observed result |
| --- | --- |
| Boot, title, start, existing saves, normal UI exit | Passed; native exit returned process status 1 |
| Narration, names, rapid speakers, long Japanese dialogue | Passed in sampled actual content |
| Ruby, explicit breaks and click pauses | Passed, including later NAK viewpoint |
| Native skip, auto and text speed | Passed; read-only skip restored |
| Sprites, CGs, full-screen effects and transitions | Passed in sampled scenes |
| Later choices | Native hiding, keyboard selection and mouse selection observed |
| Backlog | Native names, text, breaks and ruby retained |
| Native centered and cinematic layouts | Entry, return and save/load passed |
| Long ruby/effect page | Display and effects retained after save/load |
| Rounded panel | Measured CG transmission 0.45033; corner radius 13.25 pixels |
| Rollback | Original ADV title/new game/exit checked; NVL re-enabled |
| Original installations | Renewed 181-file hash/size/mtime check passed, 2026-09-12 |

Voice comparisons used isolated game audio and the corresponding original clips. Earlier normal and backlog replay correlations were 0.9904 and 0.99997; hidden-speaker save/load replay was 0.99147. The final long ruby/effect save replay matched the **full 13.479-second clip** at **0.98445 correlation**. This completes an earlier partial capture; that earlier attempt lost its output device and must not be reported as a full-clip pass. Temporary test sinks were removed after recording.

The source rebuild produced identical `.text`, `.rdata`, `.data` and `.reloc` sections to the tested prebuilt DLL; only the PE build timestamp changed. Generated resources reproduce all reviewed payload hashes. Installation checks use disposable Copy fixtures and cover installation, rollback backups, idempotence, unknown overrides, version refusal, parent-directory symlinks and staging-symlink protection. The live-process refusal was also checked against the running desktop game.

## Not fully verified

- Every route, later `asairo03xx`/`0400` modules, every unusual command, gamepad input and every legacy save state.
- Every possible punctuation placement at a wrap boundary. Native kinsoku is preserved, but that is not exhaustive visual proof.
- `asairo0203` message 7401, a 224-byte run of 112 full-width middle dots. It follows a choice-title/state setup in the script; the tested branch ended at message 6682 and did not reach it. Its actual runtime context and rendering remain unverified.
- Exact BGI pagination parity. Target-native page clears and a conservative capacity estimate are used; pages can clear earlier than Itsusora.
- Other executable versions, other WinMM export catalogs, native Windows, other Proton/Wine builds or different fonts.

NVL saves reference the generated native panel and should be loaded with NVL enabled. Use a pre-NVL save or new game after disabling. The shared black panel replaces the ordinary viewpoint-colored window artwork, reducing that original visual cue.

## Reproduce installation checks

Prepare the payload first and close every game instance. From the repository root:

```bash
python3 tests/check_installation.py --game "$GAME_COPY"
```

The test copies only the supplied Copy's executable into a temporary fixture and does not execute it or modify the supplied installation. Gameplay/audio verification requires the full game, a configured private prefix and a working desktop/audio session; the fixture test is not a substitute for those checks.
