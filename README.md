# Rune Factory 4 Special save editor

A local, offline save editor for **PC / Steam**, **extracted Switch saves**, and **`rf4_sys.sav` system saves**. It edits saves only—not game files or mods.

## Quick start

### Portable Windows app — no installation

Download **v0.1** from [GitHub Releases](https://github.com/rikimtasu/rf4s_pc_saveedit/releases/tag/v0.1). Extract the portable Windows package and open `RF4S Save Editor.exe`. Public builds exclude personal references; use **Read game folder** to load yours.

Double-click **`dist/RF4S Save Editor.exe`**. This is a **native Qt Widgets GUI**, not a browser-based app: no Chromium, WebView, HTML interface or local server. Python and required native Qt libraries are bundled, so nothing needs installing. Windows 10/11 x64 is supported. First launch unpacks its runtime into a temporary folder.

`start.bat` also opens the native EXE. The current private build is **27.3 MiB**, reduced from approximately 203 MiB by removing the unused browser and rendering runtime.

Use **Read game folder** in its toolbar to select your RF4S installation. This reads item definitions, recipes and available language names without changing the game. Private builds may already contain these references. Save files remain in the editor until you explicitly export a new file.

### Native source version (developers)

Install the build requirements, run `npm run build:native-core` once, then run `python desktop.py` with that Python environment. Node/esbuild compiles the existing save algorithms for Qt's small standalone scripting interpreter, not a browser. Node is not needed by users of the EXE.

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
| Calendar and player | Date, money, order points, materials, health, rune points and base attributes |
| Bag and storage | Items, quantities, levels, inherited equipment, 3 crafting attachments, 9 upgrade attachments, level/rarity bonuses and crystal-based weapon/tool elements |
| Skills and recipes | 38 skill levels and XP; learned recipes individually or by group |
| Friendship and people | Friendship levels and stored character stats |
| Marriage | Spouse register, anniversary, ring acceptance, wedding memory and per-candidate marriage / newlywed event flags |
| Monsters | Stats and friendship for existing tamed monsters |
| Trophy records | 25 recorded achievement / festival fields—not Steam achievements |
| System saves | Persistent ending, wedding and data-transfer unlock flags |
| Export and expert tools | Optional gender correction, experimental PC ↔ Switch conversion, story flags, progress profiles and raw edits |

Undo, redo, original-file exports and JSON change reports are included. Native pages require explicit editing opt-in. Hidden or disabled editors keep drafts and block export until applied or cleared.

**Game names** offers English, Japanese, French, German, Korean, Traditional Chinese and Simplified Chinese when present in your game. It changes item, recipe-result, character and skill names; editor instructions remain in English. Missing names fall back to English. Choose a different language without changing save bytes.

## Edit and export safely

1. **Back up your entire save folder and close the game.**
2. Open a save in the editor.
3. Enable the editor you need, change its values, then click **Apply**.
4. Review the changes and download the `.edited.sav` file.
5. With the game still closed, manually replace the intended save slot using its original filename. Keep your backup and handle Steam Cloud conflicts separately.

Your save is **not uploaded or automatically overwritten**. Edits stay in application memory until exported. Export rebuilds the checksum; unapplied drafts block export, even when their editor is hidden or disabled.

For gender correction, use **Review & export → Character gender**. The optional appearance reset also clears cosmetic overrides and outfits; it never renames the player. Both options affect only the exported copy.

## Enable item and recipe editing

A fresh copy of the repository does not include personal game-reference data. Item editing needs `rf3ItemList.bin` definitions; recipe editing needs the relevant `rf3Recipe*.bin` tables.

Import extracted tables using **Read tables** in the item reference tools or **Read recipe tables** in Recipes. Alternatively, generate references from your own game installation:

```powershell
python scripts/gather_game_data.py "<game-folder>"
python scripts/gather_save_references.py "<game-folder>"
python scripts/gather_languages.py "<game-folder>"
```

Replace `<game-folder>` with your installation folder, then restart or reload the editor. These commands read game files without modifying them. Generated references stay local and are excluded from Git. Venti does not need to be installed.

Extracted `rf3TxtItem_split2_1.*`, `rf3TxtNpc_split2_1.*` and `rf3TxtSkill_split2_1.*` TEXT tables can also be imported in **Overview → Game references & languages**. Do not choose `_split2_2` description tables.

For equipment attachments, enable editing in **Bag & storage**. Unchanged fields are preserved; 0 removes an attachment. Leave level blank to preserve mixed unit levels. Attached IDs are limited to 1023 by their 10-bit storage. Element selection adds crystals to unused upgrade slots without removing existing attachments and raises the level accordingly. Full equipment is refused. Element selection is for weapons/tools, not armor resistances.

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
.venv-desktop\Scripts\python scripts/build_desktop.py
```

The output is `dist/RF4S Save Editor.exe`. The default build excludes personal game references. For a private build with your generated references, add `--include-local`; do not publish that build. Source builds stay portable across machines and require no hard-coded game paths.

Verify the actual executable (synthetic test save only):

```powershell
& "dist/RF4S Save Editor.exe" --self-test "dist/gui-check" --self-test-game "<game-folder>"
```

The test exercises actual native controls, all editor pages, game names, attachment / element / marriage edits, draft guards and the exported checksum. It writes a synthetic save, screenshot and test result. Keep source available when redistributing the GPL editor and comply with Qt/PySide notices. The native build excludes browser engines, QML scenes/plugins, unused rendering libraries and web UI assets. `scripts/inspect_desktop_bundle.py` reports its compressed contents.

### Credits and licenses

- [rf4-modkit](https://github.com/arryndoestech/rf4-modkit) — original save-format work, MIT license.
- [Venti](https://codefloe.com/droopy_dingo/venti) — read-only data definitions, GPL-3.0 license.

Venti-derived components follow GPL-3.0. See [Attribution](ATTRIBUTION.md) and [COPYING](COPYING) for licensing details. No game binaries or real saves are bundled.
