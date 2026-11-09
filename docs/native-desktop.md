# Native Windows save editor

Open `dist/RF4S Save Editor.exe`. No installation, browser, server, Python or Node is required. The interface uses native Qt Widgets. The bundled scripting interpreter runs only shared save algorithms; it does not display web pages.

1. Close the game and back up your save directory.
2. Click **Open save** for a PC / extracted Switch slot or `rf4_sys.sav`.
3. If references are missing, click **Read game folder** and choose the installation containing `Bundle`. This never modifies the game. Extracted item, recipe and language tables can also be imported from Save overview.
4. Choose a page on the left, check **Enable editing**, change values and click **Apply changes**.
5. Use **Review & export** to inspect and export a new `.edited.sav`. The source is not automatically overwritten. Handle Steam Cloud separately.

## Items and attachments

Select a container and saved slot. **Show empty slots** exposes positions for adding items; this does not unlock capacity. The filter searches localized names/slots. Item dropdowns support typing to find a matching entry; choose the entry rather than leaving arbitrary typed text.

Replacements reset prior metadata. Unchanged fields are preserved. Blank level preserves mixed unit levels. Zero removes an attachment; attached IDs are restricted to 0–1023. Equipment supports three crafting and nine upgrade attachments, inherited equipment, total-level and rarity bonuses. Elements append crystals to unused upgrades, raise the level and never silently remove attachments. Full equipment is refused. Special effects remain the game's responsibility; in-game acceptance is not guaranteed.

## Marriage and other editors

Spouse, anniversary, ring acceptance and wedding memory are grouped with candidate marriage/newlywed flags. Selecting an event candidate does not change spouse. Apply drafts as one undoable edit. This does not initialize pregnancy, children, schedules or system unlocks, or replay wedding events.

Calendar/player, skills, individual/bulk recipes, friendship, people/monster stats, trophy records and system flags retain their existing limits. Expert pages expose full-width named flags, progress profiles and bounded raw integers/bytes. Review/export includes original backup, JSON changes, undoable restore, optional gender/appearance correction and experimental PC ↔ Switch conversion.

Drafts persist across pages and disabled editors. Apply/clear before switching records or exporting. Undo/redo shares the same binary-edit history. Opening another save or closing prompts before discarding unexported work. Synthetic demo exports are disabled.

Seven game-name languages are available when present in your game; instructions remain English. Nothing is uploaded. Backups and in-game testing remain essential.
