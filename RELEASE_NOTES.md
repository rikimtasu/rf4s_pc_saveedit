# v0.3 — Standalone icons, tourists and direct export

Download **RF4S-Save-Editor-v0.3-win-x64.zip**, extract it and run **RF4S Save Editor.exe**. Windows 10/11 x64; executable approximately **34.8 MiB**. No installation, Python, Node, browser, local server or game-folder reading is required.

## New features

- **Tourists** in Player values: 0–99,999,999, verified against the actual game loader/getter while preserving neighboring order points.
- Removed per-page editing opt-ins and the synthetic-demo button. Valid drafts apply automatically before switching records or exporting; export applies pending drafts atomically as one undoable edit.
- **Export edited save** (Ctrl+S) writes directly to `%APPDATA%\Rune Factory 4 Special`. A unique timestamped `.bak` is created beside the destination before replacement, preserving its current on-disk bytes. If the destination does not exist, the imported original is backed up instead.
- **Save as…** remains available for copies, other locations and extracted Switch saves. Choose the intended target slot if an imported file has a nonstandard filename.
- Bundled all four item/effect tables, **637 recipe records**, seven name languages including nicknames, **1,108 item-icon mappings** and **25 NPC portraits**. Icons appear in inventory, item/attachment/inheritance pickers, recipe selectors and relevant NPC/marriage pickers.
- Chinese/system-language detection, manual overrides and drafts across resizing/language changes are retained.

## Minimal protections and limitations

Close the game before exporting and keep an independent full-folder backup. Basic filename/type checks, value/bit-field limits, checksum rebuilding, conversion data-loss protection and unsaved-close confirmation remain. An invalid draft does not partially apply the other pending edits or change the disk. Undo affects memory; export again to save it, with another backup. Handle Steam Cloud conflicts separately.

A valid checksum does not guarantee in-game acceptance. Marriage/story edits do not simulate events or prerequisites; PC ↔ extracted Switch conversion remains experimental. The v0.2 friendship and system-flag corrections are retained; reapply edits made by older affected builds from pre-edit backups rather than guessing repairs.

## Verification and notices

117 JavaScript tests passed. Native regression checks, standalone GUI/export checks and the read-only tourist loader/getter replay passed. The portable executable was checked without a game-folder argument and with no installed Python or Node on its PATH.

Documentation, editor/runtime licenses and a game-assets notice are included. Game-derived reference text and images retain their owners' copyright; they are not relicensed under the editor GPL. No personal saves, game executable, voices or full game archives are included. Previous v0.1/v0.2 releases remain unchanged.

---

# v0.2 — Names, relationships and Chinese interface

Download **RF4S-Save-Editor-v0.2-win-x64.zip**, extract it and run **RF4S Save Editor.exe**. Windows 10/11 x64, approximately 28 MiB. No installation, Python, Node, browser or local server is required.

## New features

- English / Simplified Chinese interface, system-language detection and remembered manual overrides. Game-name language remains independent.
- Compact layouts down to 640×480, wrapped labels and collapsible current/draft item previews; resizing and language switching retain drafts.
- Individual dating status for the 12 marriage candidates, plus both nickname pickers for the 23 main NPCs. Read your game folder to load localized nickname labels.
- Player-name edit and game-default reset: open **rf4_sys.sav**, select the bank/slot, then Apply and export. Names allow 6 characters / 18 UTF-8 bytes. Reset uses the game's default at next load; individual slot files do not contain this name field.
- Optional export-only cleanup of incompatible dating and special addresses during gender correction; friendship and story/date history are preserved.
- Definition-based item-effect previews, bilingual flag help/evidence and read-only flag-impact previews. Exact derived stats and playable story checkpoints are not promised.
- Save picker starts in `%APPDATA%\Rune Factory 4 Special`; no save is auto-loaded.

## Fixes and important backup warning

- Corrected Barrett / Raven friendship fields; checked all 25 NPC friendship writes and all main-NPC thresholds through level 10,000 against the audited game code.
- Fixed blank standard dialog buttons and truncated confirmation titles.
- Corrected system unlock flags to **offset 0x10**, preserving the save-slot availability bitmaps.

**If an older build edited Barrett/Raven friendship or system flags, reapply those edits from a pre-edit backup.** Older guest edits wrote into unrelated header bytes; older system-flag edits could change slot availability. v0.2 does not guess how to repair those changes.

## Safety and verification

Back up the entire save folder and close the game first. All edits remain opt-in, undoable and export-only. Dating, nickname, marriage and story edits do not simulate events or prerequisites. A valid checksum does not guarantee in-game acceptance; PC ↔ extracted Switch conversion remains experimental.

115 JavaScript tests and 55 Python tests were verified across the native/replay environments, including 12 read-only executable replays. Actual native GUI/export and portable-executable checks passed. Public packages exclude personal saves and game-reference data; use **Read game folder** for your own references.

Documentation and runtime/source license notices are included. The previous v0.1 release remains available.

---

# v0.1 — Native Windows save editor

First public native desktop release for Rune Factory 4 Special.

## Download and run

Download **RF4S-Save-Editor-v0.1-win-x64.zip**, extract it and open **RF4S Save Editor.exe**. Windows 10/11 x64; nothing needs installing. No browser, Chromium, WebView or local server. The executable is approximately 27 MiB, about 87% smaller than the previous browser-engine build.

Public packages exclude personal game references and real saves. Click **Read game folder** to read item definitions, recipes and language names from your own installation; game files are not modified.

## Features

- Edit bag/storage items, quantities, levels, inherited equipment, crafting/upgrade attachments and crystal-based weapon/tool elements.
- Select seven game-name languages when available: English, Japanese, French, German, Korean, Traditional Chinese and Simplified Chinese. Editor instructions remain English.
- Manage spouse, anniversary and candidate marriage/newlywed flags in a dedicated editor.
- Calendar/player values, skills, recipes, friendship, people/monster stats, trophy records and system-save flags.
- Undo/redo, draft/export guards, original backups, JSON reports and checksum rebuilding.
- Expert named flags/raw edits, optional gender/appearance correction and experimental PC ↔ extracted Switch conversion.

## Safety and limitations

**Back up the complete save folder and close the game first.** Files are not uploaded or automatically overwritten. Marriage/story flag edits do not replay events or initialize world/family state. A valid checksum is not a guarantee of in-game acceptance. Conversion and progression edits remain experimental; test exported copies with backups.

The source and build instructions are included in this repository. Runtime/source attribution and license notices are included in the portable package.
