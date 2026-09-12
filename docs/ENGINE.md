# Implementation notes

## Engine comparison

The target, **きっと、澄みわたる朝色よりも、**, uses a Propeller engine with MPK archives and MSC scripts. Itsusora (**いつか、届く、あの空に。**) uses **BGI/Ethornell**, despite the initial expectation of a common engine. No executable offsets or machine code were transplanted between them.

Itsusora supplied the visual measurements: about 45% CG transmission through the reading area and a 13.25-pixel corner radius. The target already has native NVL setup logic in `01gamenov.msc`. The implementation adapts that logic and keeps the target's own scenario parser, glyph renderer and message state machine.

## Native resource overrides

The engine searches loose files before MPK archive entries. Four ordinary setup entry points receive the same generated native NVL setup:

- `Scenario/01game.msc`
- `Scenario/01game_HIY.msc`
- `Scenario/01game_OTH.msc`
- `Scenario/01game_NAK.msc`

The three viewpoint variants were verified to match the normal ADV code after normalizing their four window-resource names and length prefixes. The generator validates the resulting output hashes and the supported executable before producing files.

The native message origin becomes (80, 58), with 25 full-width columns (50 native half-width units), 13 rows and the native 25-pixel font setting. Native transparency is 45%, giving approximately 55% black opacity. `BG/NV00.mgr` is a generated 688×528 black BGRA panel at (56, 36), with corner alpha coverage for radius 13.25. Coordinates exclude the Windows menu bar.

The generator prepends the native transparency setter and relocates both native nine-byte label tables by the inserted instruction length. It does not transcode or rewrite story dialogue. The executable and MPK archives remain unchanged on disk.

## Native functions and commands

Addresses below apply only to the validated executable, image base `0x400000`.

| Function | VA | Role |
| --- | --- | --- |
| Resource lookup | `0x4451c0` | Loose-file and archive lookup |
| LoadMSCModule | `0x457e10` | MSC code and label tables |
| ProcessScenarioOpcode | `0x4519e0` | VM command groups |
| ProcessMessageOpcode | `0x44d3b0` | Messages, layout, mode, native page clear |
| ProcessSystemOpcode | `0x44f050` | Dimensions, kinsoku and settings |
| PrepareScenarioMessage | `0x44c220` | Names, message state, voice/history preparation |
| RenderScenarioMessageFrame | `0x44ae30` | Incremental native text layout/rendering |
| SaveScenarioSnapshot | `0x447230` | Current message and page serialization |
| Native glyph measurement | `0x404590` | `GetTextExtentPoint32A` |
| Native glyph rasterization | `0x4048c0` | `ExtTextOutA` |

Relevant commands include `05 00` (message), `05 05` (NVL mode), `05 06` (native page clear), `01 0a` (dimensions), `01 0b` (kinsoku), `01 1c` selector `0x14` (transparency), and `06 02` (queue voice and its saved-page record).

## Two scoped runtime hooks

The original-code `winmm.dll` proxy forwards the validated Proton WinMM's 189 exports, including ordinal-only entries. Initialization resolves the real DLL by an absolute system-directory path. Generated assembly forwarding stubs preserve argument layout, general registers and flags; the real WinMM function supplies the original calling convention and return value.

1. **Message preparation, RVA `0x4c220`.** The hook calls the original native preparation exactly once. It reserves page capacity only for the live caller at RVA `0x4d45c` and only for the exact ordinary NVL mode and geometry. If necessary it invokes native `05 06` before the message, carrying the queued voice slot into the new page. After native parsing, it reuses unused prefix-buffer space to display the visible speaker inline. Alternate identities stay hidden and remain available to voice/history handling.
2. **Save snapshot, RVA `0x47230`.** The engine serializes its current display buffer. This hook temporarily restores the original prefix bytes during the original save call, then restores the inline display label. It prevents presentation-only changes from damaging hidden identities in saved messages. A narrow compatibility path handles the exact prefix damage found in early local prototype saves.

Unique signatures, reviewed RVAs, PE architecture and prologues are checked before hook installation. Module-relative addressing accounts for ASLR. The message trampoline copies six bytes; the save trampoline copies eight bytes, including a loader-relocated cookie operand. See `hook/nvl_guard.c` for the full signatures and calling conventions.

## Japanese and special layouts

Scenario text remains CP932/Shift-JIS. Native glyph measurement, full-/half-width handling, kinsoku tables, ruby base/reading layout, punctuation, waits and embedded commands remain in use. The capacity estimator scans complete native multibyte sequences; it does not insert breaks or position glyphs. Its conservative byte-length estimate can clear a page earlier than the reference game.

The native state machine still owns speed, auto/skip, voice timing, click waits, history and choices. Native centered (`01gameNov`) and cinematic (`01gameCi`) layouts remain distinct. Their different geometry excludes them from ordinary pagination/name changes. No global text renderer or menu renderer is replaced.
