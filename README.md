# Rune Factory 4 Special save editor

A local, offline save editor for **PC / Steam**, **extracted Switch saves**, and **`rf4_sys.sav` system saves**. It edits saves only—not game files or mods.

## Quick start

You need **Python 3.10+** and a modern browser. No extra packages are needed to run the editor.

On Windows, double-click **`start.bat`**. Or run this from the project folder:

```powershell
python serve.py
```

The editor opens in your browser, normally at `http://127.0.0.1:8764`. Keep the terminal open while using it. Do not open `web/index.html` directly.

## What you can edit

| Section | Supported edits |
| --- | --- |
| Calendar and player | Date, money, order points, materials, health, rune points and base attributes |
| Bag and storage | Items, quantities and levels in the bag, fridge, storage, weapon box and armor box |
| Skills and recipes | 38 skill levels and XP; learned recipes individually or by group |
| Friendship and people | Friendship levels and stored character stats |
| Monsters | Stats and friendship for existing tamed monsters |
| Trophy records | 25 recorded achievement / festival fields—not Steam achievements |
| System saves | Persistent ending, wedding and data-transfer unlock flags |
| Export and expert tools | Optional gender correction, experimental PC ↔ Switch conversion, story flags, progress profiles and raw edits |

Undo, redo, original-file downloads and JSON change reports are included. Advanced editors start collapsed and require explicit opt-in.

## Edit and export safely

1. **Back up your entire save folder and close the game.**
2. Open or drag a save into the editor.
3. Enable the editor you need, change its values, then click **Apply**.
4. Review the changes and download the `.edited.sav` file.
5. With the game still closed, manually replace the intended save slot using its original filename. Keep your backup and handle Steam Cloud conflicts separately.

Your save is **not uploaded or automatically overwritten**. Edits stay in browser memory until you download them. Export rebuilds the checksum; unapplied drafts block export, even when their editor is collapsed.

For gender correction, use **Review & export → Character gender**. The optional appearance reset also clears cosmetic overrides and outfits; it never renames the player. Both options affect only the exported copy.

## Enable item and recipe editing

A fresh copy of the repository does not include personal game-reference data. Item editing needs `rf3ItemList.bin` definitions; recipe editing needs the relevant `rf3Recipe*.bin` tables.

Import extracted tables using **Read tables** in the item reference tools or **Read recipe tables** in Recipes. Alternatively, generate references from your own game installation:

```powershell
python scripts/gather_game_data.py "<game-folder>"
python scripts/gather_save_references.py "<game-folder>"
```

Replace `<game-folder>` with your installation folder, then restart or reload the editor. These commands read game files without modifying them. Generated references stay local and are excluded from Git. Venti does not need to be installed.

## Important limits

- **A valid checksum does not guarantee a working save.** Story edits can break progression; progress profiles are not guaranteed playable checkpoints. Checksum repair cannot recover corrupted data.
- Date and skill edits do not simulate daily updates or level-up stat gains. Base-stat edits do not recalculate equipment bonuses.
- Recipes have learned flags, not editable difficulty levels. Variants sharing a flag change together.
- Friendship edits do not trigger dating, marriage or story events. Monster editing cannot create, tame, rename or change species.
- Trophy records are not complete trophy-room ownership, physical trophy items or Steam achievement unlocks. Filling later inventory slots does not unlock capacity.
- **PC ↔ Switch conversion is experimental** and requires an extracted save. It preserves the trailer and refuses to discard nonzero candidate-padding bytes; it does not decrypt or inject console saves.
- The corrected appearance reset, newer editors, conversion and story jumps still need in-game acceptance testing. Keep backups and test exported copies before relying on them.

## More information

- [User guide](web/help.html) — detailed workflows and troubleshooting; also available through Help in the running editor.
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

### Credits and licenses

- [rf4-modkit](https://github.com/arryndoestech/rf4-modkit) — original save-format work, MIT license.
- [Venti](https://codefloe.com/droopy_dingo/venti) — read-only data definitions, GPL-3.0 license.

Venti-derived components follow GPL-3.0. See [Attribution](ATTRIBUTION.md) and [COPYING](COPYING) for licensing details. No game binaries or real saves are bundled.
