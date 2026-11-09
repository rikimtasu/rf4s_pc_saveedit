# Standalone editing and direct save-folder export

This describes v0.3. The unchanged v0.1/v0.2 packages use their historical manual-apply/copy-export workflows.

## Normal workflow

1. Close RF4S and open the intended save.
2. Edit its values. There are no per-page **Enable editing** checkboxes and no demo button.
3. Click **Export edited save** (Ctrl+S). Valid drafts apply automatically as one undoable edit, and the editor writes to `%APPDATA%\Rune Factory 4 Special`.

The target defaults to the opened file's canonical name (`rf4_sNN.sav` or `rf4_sys.sav`). For an imported file with a different name, choose the intended target slot on **Review & export**. System/slot filename mismatches are blocked. PC save-folder export requires PC output; **Save as…** remains available for other locations and extracted Switch format.

Before replacing a target, the editor backs up the **current bytes on disk**, not a possibly stale loaded snapshot. Backups are created beside the save, named like `rf4_s01.sav.backup-YYYYMMDD-HHMMSS-microseconds-N.bak`. If a target does not yet exist, the imported original is backed up there instead. Repeated exports keep separate backups. Backup creation must succeed before the atomic save write proceeds.

Switching records applies a valid draft to the old record first. Invalid drafts stay visible; export does not partially apply the other drafts or modify the disk. Only basic format, integer/bit-field limits, checksum rebuilding, data-loss protection and unsaved-close protection remain. Unsupported story/family prerequisites are still not simulated. Undo changes memory; export again to write that undo to disk, with another backup.

## Tourists

**Player values → Tourists** edits save `0x20714`, a signed 32-bit integer, range **0–99,999,999**. Serializer `0x7EABE..0x7EAD3` and loader `0x80018..0x80037` copy the block between save `0x20710` and runtime `0xE9AC08`; the tourist counter is the next word at runtime `0xE9AC0C`. Script getter `0x21E050..0x21E060` reads that word; the addition path at `0x21E0A9..0x21E0D5` clamps to 99,999,999. Editing it preserves neighboring order points and does not execute orders/events.

## Bundled references and icons

The executable embeds the four item/effect tables, recipe tables, seven name languages (including nicknames), and game-derived PNG icons. No game-folder reading, network access or installed image library is needed at runtime. Optional reference reload/import controls remain for overrides.

All **1,108 item IDs** map through the executable's ordered icon filename vector (audited RVA `0x97DD44`, stride `0x100`), not through recipe families, sort order or the 3D model index. This preserves distinct giant-crop, equipment and tool icons. The vector uses Switch-style `.bntx` filenames with matching PC `.texture` bundle members. Item pickers, attachments/inherited equipment, inventory rows and recipe selectors show those icons; main-NPC pickers and marriage candidates also use the 25 available normal portraits. Where no established icon mapping exists, text remains available without a guessed image.

BC7 images are decoded from the RES/PIXL descriptor and its image-data offset, excluding the relocation trailer. The texture layout was corroborated with local samples and the [darkxex texture extractor](https://github.com/darkxex/Rune-Factory-4-Special-Texture-Extractor); this repo contains an independently written reader, not copied unlicensed extractor code. Build-time Pillow supplies the BC7 decoder.

For developers, prepare the ignored `builtin/` assets once with:

```powershell
python -m scripts.generate_builtin "<RF4S game folder>"
python scripts/build_desktop.py --output dist/standalone-validated
```

Or pass `--game "<RF4S game folder>"` to the build script. Catalog/icon preparation needs Pillow and pefile; users of the executable do not. Only the editor-required data/images are included, never personal saves, the game executable, voice files or complete archives. Game-derived images/text remain the property of their game rights holders and are not relicensed under the editor's GPL.
