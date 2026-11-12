# v0.5 — MyGO desktop GUI with Nord theme

An offline save editor for PC/Steam saves, extracted Switch saves and `rf4_sys.sav` system saves. Download **RF4S-Save-Editor-v0.5-win-x64.zip**, extract it and open **RF4S Save Editor.exe** on Windows 10/11 x64. Fonts, curated game references and item icons are bundled. No installation, Python, Node, Qt, browser or game-folder reading is required.

- Replaced the default Qt GUI with MyGO native Go widgets and a Nord palette. The shared save algorithms run in Goja inside the executable; no WebView or local server is used.
- Added a grouped sidebar, a section selector for compact windows, a virtualized inventory icon grid, searchable record/item selectors and scrolling forms. English/Chinese interface captions and seven game-name languages are available; some helper text remains English.
- Carried over the save-editing areas, including equipment attachments/effect previews, recipes, relationships, orders, soil, system names/unlocks, experimental roster creation and story tools. Valid drafts apply before switching records/pages or exporting; invalid drafts remain visible and block those actions.
- Kept undo/redo, explicit export, JSON reports and managed backups. Converting between PC and Switch output requires selecting the output platform and checking the experimental-conversion acknowledgement under **Review & export**. Exports and restores back up the destination first and retain up to ten matching editor backups after success.
- Added a synthetic demo with export disabled. `start.bat` prefers the MyGO build; the Qt and browser source entry points remain available.

## Verification and limits

All 173 JavaScript tests and the MyGO Go tests passed. The Go tests cover native controls at desktop and 640×480 sizes, invalid drafts, atomic edits, undo/redo, checksums, UTF-8 names, PC/Switch output and backup retention/restoration. Standalone Windows startup/rendering and the packaged executable were checked. No in-game acceptance testing was performed.

**Back up your entire save folder and close the game before exporting or restoring.** A valid checksum does not guarantee gameplay compatibility. Story, romance, roster and order edits do not execute game scripts or reconstruct missing world state. PC/Switch conversion remains experimental. Handle Steam Cloud conflicts separately.

See the [MyGO guide](https://github.com/rikimtasu/rf4s_pc_saveedit/blob/v0.5/docs/mygo-desktop.md) for usage and source builds; it is also included as `docs/mygo-desktop.md` in the ZIP. Previous releases are unchanged.

---

# v0.41 — Extra orders, staff gear and backup rollback

Download **RF4S-Save-Editor-v0.41-win-x64.zip**, extract it and run **RF4S Save Editor.exe**. Windows 10/11 x64; no installation, Python, Node, browser or game-folder reading is required. Standalone references, icons and English/Chinese fonts are included. Previous releases remain available.

- Named BGM choices (six soundtrack families) and a separate named morning-call NPC selector, including Pico. The global morning-call menu unlock remains independent. Direct order fields now total 44.
- Backups & rollback page: timestamps, CRC, size/hash, calendar/player/currency details; confirmed byte-exact disk restore with a pre-rollback backup. Successful direct exports/restores retain the newest 10 managed backups per save, with cleanup failures reported safely. See [usage and evidence](docs/save-history-and-order-names.md).
- Extra Orders expanded to **44 direct fields in five tabs**: seven licenses, twelve shop/service switches, raw storage/field levels, rank and other saved flags, plus named BGM/caller choices. Named registers use full developer widths; CT-derived raw settings retain explicit limits/warnings. Hidden-tab invalid drafts block export atomically.
- Both staff presets now search **all 60 saved bag slots**, including scattered empty slots after slot 15. Six free slots are required; existing items/capacity are untouched.
- Extra Orders editor: enemy level increase 0–10, EXP/skill EXP toggles, town-event toggle, enemy level/HP display and appearance orders. Separate `rf4_sys.sav` menu-unlock draft button.
- Maximum soil shortcut: positive packed maxima, with negative signs cleared; preserves the selected patch/field scope, crops and unused patches.
- Separate balanced and maximum-damage optimized staff gear grants, informed by the supplied [GameFAQs thread](https://gamefaqs.gamespot.com/boards/258612-rune-factory-4-special/80987735). Full attachment previews, maximum saved level/rarity bonuses, empty-slot-only allocation and atomic undo.
- Damage preset uses Strange Pendant, which ignores **your** defenses as well as the enemy's. No mathematical optimum or complete immunity is claimed; food buffs, skills and final-stat simulation are not changed/implemented.
- Native English/Chinese controls and compact layouts. The previously published v0.4 download remains unchanged. See [usage and evidence](docs/order-soil-gear-shortcuts.md).

## Verification and safety

Focused Python checks passed: 10 export/backup checks, 3 native backup/order-name checks and 2 translation checks. No additional JavaScript tests or EXE smoke tests were run for this update, as requested. The portable package is checked for private reference data and unwanted browser/save assets before publication.

**Back up the entire save folder and close the game before exporting or restoring.** A valid checksum does not guarantee gameplay compatibility. Unlock flags do not run order/event scripts or build facilities; raw expansion/rank values are not verified gameplay caps. Rollback does not manage Steam Cloud conflicts. Gear presets use empty slots only and do not unlock bag capacity; equip the granted items in-game.

---

# v0.4 — Story, soil, experimental roster and nickname resets

Download **RF4S-Save-Editor-v0.4-win-x64.zip**, extract it and run **RF4S Save Editor.exe**. Windows 10/11 x64; executable approximately **49.4 MiB**. No installation, Python, Node, browser, local server or game-folder reading is required. Previous releases remain available.

## New editors and shortcuts

- **Story jump planner:** preview a target stage plus explicit supporting flags, exact byte/mask changes, candidate conditions and unresolved dependencies. Apply atomically with undo; rewinds require separate acknowledgement. Story-bearing profiles stage into the native planner.
- **Experimental end-game shortcut:** stages progress 511 and two documented Ventuswill-related clears for review. It does not execute the ending, initialize the world, clean active events, grant rewards/achievements or modify the separate system save.
- **Soil editor:** raw packed health, growth/yield/quality/size, defense and level/progress values. Edit one patch or changed fields across used patches of one field. Crop records and unused seasonal patches are preserved.
- **Experimental relationships:** opt-in dating-bit editing for all 23 audited main NPC records; opt-in spouse IDs within the five-bit 0–31 range. Does not add missing confession/date/wedding scripts. Guests do not have an audited persisted dating field and remain unsupported there.
- **Experimental roster creation:** add species IDs 1–255 into empty tamed-monster slots, using basic or copied saved stats. Requires built-room capacity (four per room); existing monsters are never overwritten. NPC species can lack usable monster AI/models/behavior and are not guaranteed to spawn or survive gameplay transitions.
- **Nickname reset shortcuts:** reset NPC→player, player→NPC, or both for the selected NPC using the current saved **Lest/Frey** gender. Resets stage drafts only and preserve dating/friendship. Unknown gender is not guessed.

## Readability and retained functionality

- A synthetic 990-slot fridge selection measured approximately 1.97 seconds before the picker-cache change and 0.15 seconds afterwards on the development machine; timings vary by machine and this is not a game-load benchmark.
- Bundled **Noto Sans Medium (500)** and **Noto Sans CJK SC Medium** replace Inter/system-dependent Chinese fallback. No font installation or runtime network access is needed; both SIL OFL notices are included.
- Compact **11pt** body text, **16pt** page headings, smaller tiles/icons/picker rows and Nord colors. Forms still reflow at 640×480; drafts survive resizing and English/Chinese switching.
- Game-style inventory grid, shared lazy picker models, **Learn all recipes / Ctrl+Shift+L**, standalone references/icons and all v0.3 direct-export/backups and atomic-draft behavior are retained.

## Verification and important limits

150 JavaScript tests passed, including all 512 stored story targets, soil bit preservation, PC/Switch CRC/undo, experimental relationship bounds, roster capacity and failed-batch rollback. Native UI/layout tests and standalone executable smoke tests cover the new editors and nickname reset behavior. Narrow read-only executable replays verify soil copy loops, main-NPC dating queries and roster occupancy counting; **they do not prove in-game story, romance or NPC-monster compatibility**.

**Back up the entire save folder and close the game before editing.** A valid checksum is not proof of gameplay acceptance. Use **Save as…** for experimental copies and test in-game before replacing important saves. Undo changes memory, not an already exported file. PC ↔ extracted Switch conversion remains experimental. See [expanded editors and executable evidence](docs/expanded-editors.md), [story-jump details](docs/story-jump-planner.md), and [nickname guidance](docs/player-name-and-relationships.md).

The public package excludes personal saves, raw private reference modules, game executables and full game archives. Curated game-derived editor references/icons retain their owners' copyright and notices. Editor/runtime/font license documents are included.

---

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
