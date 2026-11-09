# Rune Factory 4 Special save editor

A local, offline save editor for **PC / Steam**, **extracted Switch saves**, and **`rf4_sys.sav` system saves**. It edits saves only—not game files or mods.

## Quick start

### Portable Windows app — no installation

Download **v0.3** from [GitHub Releases](https://github.com/rikimtasu/rf4s_pc_saveedit/releases/tag/v0.3). Extract **RF4S-Save-Editor-v0.3-win-x64.zip** and open `RF4S Save Editor.exe`. Item/effect definitions, recipes, seven name languages and item/NPC icons are bundled; no game-folder reading is required.

This is a **native Qt Widgets GUI**, not a browser-based app: no Chromium, WebView, HTML interface or local server. Python and required native Qt libraries are bundled, so nothing needs installing. Windows 10/11 x64 is supported. First launch unpacks its runtime into a temporary folder.

`start.bat` also opens a locally built native EXE in `dist/`. The v0.3 executable is approximately **34.8 MiB**, including its standalone references and icons; no installation is needed.

Close the game, open your save, edit values, then click **Export edited save**. It writes directly to `%APPDATA%\Rune Factory 4 Special`, backing up the current destination there first. Edits stay in memory until you explicitly export. **Save as…** creates copies or exports extracted Switch format.

### Native source version (developers)

Install the build requirements, prepare the bundled catalog/icons with `python -m scripts.generate_builtin "<game folder>"`, run `npm run build:native-core`, then run `python desktop.py`. Node/esbuild compiles the existing save algorithms for Qt's small standalone scripting interpreter, not a browser. Node and the game folder are not needed by users of the new standalone EXE.

### New in v0.3

**Tourists**, automatic draft application, direct save-folder export with backups, and bundled definitions, 637 recipes, seven name languages, all 1,108 item-icon mappings and 25 NPC portraits. Editing opt-in checkboxes and the demo button are removed; basic value/file protections remain. See [standalone workflow and asset evidence](docs/standalone-workflow.md).

### Optional legacy browser version

You need **Python 3.10+** and a modern browser for the source-only browser version. No extra packages are needed for this mode.

To explicitly run the legacy browser version, use this from the project folder:

```powershell
python serve.py
```

The editor opens in your browser, normally at `http://127.0.0.1:8764`. Keep the terminal open while using it. Do not open `web/index.html` directly.

## What you can edit

| Section | Supported edits |
| --- | --- |
| Calendar and player | Date, money, order points, tourists, materials, health, rune points and base attributes |
| Bag and storage | Items, quantities, levels, inherited equipment, 3 crafting attachments, 9 upgrade attachments, level/rarity bonuses and crystal-based weapon/tool elements |
| Skills and recipes | 38 skill levels and XP; learned recipes individually or by group |
| Friendship and people | Friendship levels and stored character stats |
| Dating & nicknames (v0.2+) | Per-candidate dating flag; NPC-to-player and player-to-NPC nickname pickers |
| Player name (v0.2+) | Edit/reset the selected name in `rf4_sys.sav`; 6 characters / 18 UTF-8 bytes |
| Marriage | Spouse register, anniversary, ring acceptance, wedding memory and per-candidate marriage / newlywed event flags |
| Monsters | Stats and friendship for existing tamed monsters |
| Trophy records | 25 recorded achievement / festival fields—not Steam achievements |
| System saves | Persistent ending, wedding and data-transfer unlock flags |
| Export and expert tools | Optional gender correction, experimental PC ↔ Switch conversion, story flags, progress profiles and raw edits |

Undo, redo, Save as and JSON change reports are included. No per-page editing opt-in is needed. Valid drafts apply automatically before switching records or exporting; invalid drafts remain visible and block export without partially applying other pending edits.

**Game names** offers bundled English, Japanese, French, German, Korean, Traditional Chinese and Simplified Chinese. It changes item, recipe-result, character, nickname and skill names; missing names fall back to English. Choose a different language without changing save bytes.

v0.2 also offers an independent **Interface / 界面** selector: **Follow system** chooses Simplified Chinese for Chinese Windows locales, English otherwise. Manual English/Chinese overrides are remembered. Switching captions preserves drafts, IDs and save bytes. On launch the save picker starts at `%APPDATA%\Rune Factory 4 Special` (home-folder fallback); no save is automatically loaded.

Compact windows are supported down to **640×480**. Forms reflow instead of clipping labels, and long pages scroll vertically through the Apply/Clear controls. Item previews use current/draft tabs; uncheck their heading to collapse the preview. Resizing does not discard drafts.

Current source builds add a game-inspired icon grid with quantity badges, 12-point body text and larger item/portrait icons. Nord colors apply consistently to controls and dropdowns; **Ctrl+Shift+L** or **Learn all recipes** learns every loaded recipe as one undoable edit. Shared lazy picker models and cached slot lists make full storage much faster to browse. Existing release packages are unchanged; the separate local build is `dist/nord/RF4S Save Editor.exe`, preferred by `start.bat` when present. See the [native guide](docs/native-desktop.md).

v0.2 fixes blank confirmation buttons and Barrett / Raven friendship offsets. All 25 NPC friendship writes and every main-NPC level threshold are checked against the audited game code. **Reapply guest friendship edits from a pre-edit backup**: older builds wrote into the guest-block header, which is not automatically repaired. These corrections are not included in the original v0.1 release. See [friendship layout evidence](docs/extended-layout.md#friendship).

## Edit and export safely

1. **Back up your entire save folder and close the game.**
2. Open a save in the editor.
3. Change values directly. Apply is optional; valid drafts apply automatically on export or before switching records.
4. Review the target filename, then click **Export edited save** (Ctrl+S). It backs up the current destination and replaces it in `%APPDATA%\Rune Factory 4 Special`.
5. Keep the game closed until export finishes. Keep your backups and handle Steam Cloud conflicts separately. Use **Save as…** if you want a separate copy instead.

Your save is **not uploaded**. Edits stay in application memory until exported. Direct export explicitly overwrites the chosen save after creating a unique same-folder backup of its current bytes; if absent, the imported original is backed up instead. Export rebuilds the checksum. Undo changes memory, not the on-disk save; export again to save the undo.

For gender correction, use **Review & export → Character gender**. The optional appearance reset also clears cosmetic overrides and outfits; it never renames the player. Both options affect only the exported output.

v0.2 also offers **Clear incompatible dating and their special nicknames (keep friendship)**. Lest export clears the six bachelors; Frey export clears the six bachelorettes. This opt-in preserves friendship, other NPCs and story/date history, and refuses incompatible spouses. See [relationship evidence](docs/extended-layout.md#dating-and-special-forms-of-address). It is not a full romance-event reset or included in the original v0.1 release.

For individual edits use **Dating & nicknames**; localized choices are bundled. For **Player name**, open **`rf4_sys.sav`** and select the bank/slot—the name is not stored in an individual slot file. Reset prepares an empty-name draft so the game generates its default at next load. All edits remain undoable and export-only. v0.2 also corrects system unlock flags to offset `0x10`, preserving the slot bitmaps; reapply older system-flag edits from a pre-edit backup. See [name/relationship usage and evidence](docs/player-name-and-relationships.md).

## Optional reference overrides and legacy browser setup

The v0.3 portable app includes all editor-required references; these steps are optional overrides. A fresh source checkout does not include generated game assets: prepare `builtin/` using the native build instructions below. The source-only legacy browser version uses the separate reference modules described here.

Import extracted tables using **Read tables** in the item reference tools or **Read recipe tables** in Recipes. Alternatively, generate references from your own game installation:

```powershell
python scripts/gather_game_data.py "<game-folder>"
python scripts/gather_save_references.py "<game-folder>"
python scripts/gather_languages.py "<game-folder>"
```

Replace `<game-folder>` with your installation folder, then restart or reload the editor. These commands read game files without modifying them. Generated references stay local and are excluded from Git. Venti does not need to be installed.

Extracted `rf3TxtItem_split2_1.*`, `rf3TxtNpc_split2_1.*` and `rf3TxtSkill_split2_1.*` TEXT tables can also be imported in **Overview → Game references & languages**. Do not choose `_split2_2` description tables.

For equipment attachments, use **Bag & storage**. Unchanged fields are preserved; 0 removes an attachment. Leave level blank to preserve mixed unit levels. Attached IDs are limited to 1023 by their 10-bit storage. Element selection adds crystals to unused upgrade slots without removing existing attachments and raises the level accordingly. Full equipment is refused. Element selection is for weapons/tools, not armor resistances.

The native **Item effect preview / 物品效果预览** compares current and drafted items without applying an edit. Bundled tables supply base equipment/use effects, inheritance references, individual material bonuses and the planned element. It is **definition-based, not a final-stat simulator**: material-level scaling, repetition penalties, special multipliers and total-level/rarity bonuses are explicitly not calculated.

**Expert: story flags** has group filters, Chinese/English meanings, original developer symbols/descriptions, evidence levels and a read-only byte/condition preview. Script-witness stages are not playable presets; unresolved participant queries stay unknown. See [the new story investigation](docs/story-flag-investigation.md).

## Important limits

- **A valid checksum does not guarantee a working save.** Story edits can break progression; progress profiles are not guaranteed playable checkpoints. Checksum repair cannot recover corrupted data.
- Date and skill edits do not simulate daily updates or level-up stat gains. Base-stat edits do not recalculate equipment bonuses.
- Recipes have learned flags, not editable difficulty levels. Variants sharing a flag change together.
- Friendship edits do not trigger dating, marriage or story events. Marriage controls edit selected flags only, not a complete marry/divorce operation; children, pregnancy, schedules and system-save wedding unlocks are untouched. Monster editing cannot create, tame, rename or change species.
- Trophy records are not complete trophy-room ownership, physical trophy items or Steam achievement unlocks. Filling later inventory slots does not unlock capacity.
- **PC ↔ Switch conversion is experimental** and requires an extracted save. It preserves the trailer and refuses to discard nonzero candidate-padding bytes; it does not decrypt or inject console saves.
- The corrected appearance reset, newer editors, conversion and story jumps still need in-game acceptance testing. Keep backups and test exported copies before relying on them.

## More information

- [Native user guide](docs/native-desktop.md)
- [App state-machine map and transition rules](docs/state-machines.md)
- [Legacy browser user guide](web/help.html)
- [Save layout and appearance evidence](docs/save-layout.md)
- [Skills, recipes, storage and actor layouts](docs/extended-layout.md)
- [Story flags and platform evidence](docs/cheat-table-and-platforms.md)

### Tests

Testing also requires **Node.js 20+**; it is not needed to run the editor.

```powershell
npm test
python tests/verify_upstream.py
python -m unittest discover -s tests -p "test_*.py"
```

### Build the portable Windows executable

Build tools (Python, Node.js 20+, esbuild and PyInstaller) are needed **only on the developer's computer**:

```powershell
python -m venv .venv-desktop
.venv-desktop\Scripts\python -m pip install -r requirements-desktop.txt
.venv-desktop\Scripts\python -m scripts.generate_builtin "<game-folder>"
.venv-desktop\Scripts\python scripts/build_desktop.py
```

The output is `dist/RF4S Save Editor.exe`. Catalog/icon preparation reads the game once on the developer's machine; users need no game-folder access. The default build bundles only curated editor references and PNGs, excluding personal legacy reference modules. `--include-local` is for private builds only; do not publish those. Source builds stay portable across machines and require no hard-coded game paths.

Verify the actual executable (synthetic test save only):

```powershell
& "dist/RF4S Save Editor.exe" --self-test "dist/gui-check"
```

The test exercises native controls, bundled names/icons, attachments/elements, automatic drafts, direct export/backups, friendship, dating/nicknames, system names/flags and checksums. It writes synthetic saves, screenshots and results only inside the test output directory, never the user's save folder. Keep source available when redistributing the GPL editor and comply with Qt/PySide notices. The native build excludes browser engines, QML scenes/plugins, unused rendering libraries and web UI assets. `scripts/inspect_desktop_bundle.py` reports its compressed contents.

### Credits and licenses

- [rf4-modkit](https://github.com/arryndoestech/rf4-modkit) — original save-format work, MIT license.
- [Venti](https://codefloe.com/droopy_dingo/venti) — read-only data definitions, GPL-3.0 license.

Venti-derived components follow GPL-3.0. See [Attribution](ATTRIBUTION.md) and [COPYING](COPYING) for licensing details. Game-derived reference text and icons retain their owners' copyright and are not relicensed under the editor GPL. No game executable, full archives or real saves are bundled.
