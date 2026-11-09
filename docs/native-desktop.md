# Native Windows save editor

v0.3 uses the [standalone workflow](standalone-workflow.md): bundled data/icons, automatic draft application, tourist-count edits and direct save-folder export with backups. v0.1/v0.2 packages remain unchanged and use their historical manual-apply/copy-export workflows.

Open `dist/RF4S Save Editor.exe`. No installation, browser, server, Python or Node is required. The interface uses native Qt Widgets. The bundled scripting interpreter runs only shared save algorithms; it does not display web pages.

1. Close the game and back up your save directory.
2. The launch save picker starts at `%APPDATA%\Rune Factory 4 Special`; if absent, it uses your home folder. Select a PC / extracted Switch slot or `rf4_sys.sav`, or cancel and use **Open save** later. No save is auto-loaded.
3. References, seven name languages and icons are already bundled. Optional reload/import controls in Save overview allow overrides without modifying game files.
4. Choose a page and change values directly. Apply is optional; valid drafts apply automatically before switching records or exporting.
5. Use **Review & export** to inspect the target, then **Export edited save** to write it directly into `%APPDATA%\Rune Factory 4 Special` with a same-folder backup first. Use **Save as…** for separate copies or extracted Switch output. Handle Steam Cloud separately.

## Items and attachments

Select a container and saved slot. **Show empty slots** exposes positions for adding items; this does not unlock capacity. The filter searches localized names/slots. Item dropdowns support typing to find a matching entry; choose the entry rather than leaving arbitrary typed text.

Replacements reset prior metadata. Unchanged fields are preserved. Blank level preserves mixed unit levels. Zero removes an attachment; attached IDs are restricted to 0–1023. Equipment supports three crafting and nine upgrade attachments, inherited equipment, total-level and rarity bonuses. Elements append crystals to unused upgrades, raise the level and never silently remove attachments. Full equipment is refused. Special effects remain the game's responsibility; in-game acceptance is not guaranteed.

The current/draft **Item effect preview** is read-only and uses the same item-edit algorithm on a copy. Game tables supply base equipment and use effects, inherited-equipment references, and individual craft/upgrade material bonuses. Percentages are decoded from fixed-point values; unknown/missing references remain unknown. The planned element is shown separately. Final stats, material-level scaling, repeated-material penalties, total-level/rarity bonuses, special multipliers, inheritance combinations and actor stats are not simulated.

## Marriage and other editors

**Dating & nicknames** adds individual dating flags for marriage candidates and independent NPC/player address pickers for main NPCs. Localized nickname choices are bundled. **Player name** edits the selected record in `rf4_sys.sav` (not an individual slot file), with UTF-8 bounds and a draft-only game-default reset. See [usage and executable evidence](player-name-and-relationships.md). Names, nicknames and dating remain independent; these edits do not simulate romance or family events.

Spouse, anniversary, ring acceptance and wedding memory are grouped with candidate marriage/newlywed flags. Selecting an event candidate does not change spouse. Apply drafts as one undoable edit. This does not initialize pregnancy, children, schedules or system unlocks, or replay wedding events.

Calendar/player (including Tourists), skills, individual/bulk recipes, friendship, people/monster stats, trophy records and system flags retain their value limits. Expert pages expose full-width named flags, progress profiles and bounded raw integers/bytes. Review/export includes direct save-folder export with automatic backups, Save as, JSON changes, undoable restore, optional gender/appearance correction and experimental PC ↔ Switch conversion.

v0.2 adds an off-by-default **Clear incompatible dating and their special nicknames (keep friendship)** export checkbox. Choose Male, Female or Match original gender first. Lest clears the six bachelors; Frey clears the six bachelorettes. Preview lists the targets. Both forms of address reset, but friendship, other NPCs, story/event history, date counts and achievements stay unchanged. An incompatible spouse blocks cleanup; marriage/family state must be handled separately. This is not a simulated breakup or complete romance-event reset.

Drafts persist across pages. Valid drafts apply automatically before switching records or exporting; an invalid draft stays visible and stops export without partially applying other pending edits. Undo/redo shares the same binary-edit history. Opening another save or closing prompts before discarding unexported work. There is no synthetic-demo button.

Compact windows (down to 640×480) use a narrower wrapping navigation list and reflow large forms into one column, with labels above controls when needed. Action rows stack and long consent captions wrap. Item previews use **Current item / Draft result** tabs; uncheck the preview heading to collapse it and make more room. Long pages scroll vertically so Apply/Clear controls remain reachable. Resizing and language switching retain the same controls, drafts and save bytes.

Standard confirmation buttons retain English captions when no Chinese catalog entry exists, rather than becoming blank. Confirmation dialogs reserve enough width for their titles and native window controls; Cancel remains the safe default. Barrett / Raven friendship edits use their corrected packed fields (`0x1DF6C` / `0x1DF74`); all main-NPC friendship mappings and level thresholds are checked against read-only replay of the audited game code. Start from a pre-edit backup when reapplying guest levels exported by older builds: those builds wrote into the guest-block header, and the editor does not guess how to undo those unrelated changes.

**Interface / 界面** is independent of **Game names**. **Follow system** defaults to Simplified Chinese for Chinese system locales and English otherwise; manual English/Chinese overrides are remembered. Switching interface language preserves controls, even partially typed drafts, and does not change save data. The legacy browser UI is not fully localized. Seven game-name languages are bundled.

Story flags retain raw developer identifiers and original descriptions. Human translations, symbol-only interpretations and static script evidence are distinguished. Group/Chinese-description search and the draft impact preview do not apply dependency repairs or simulate events. Memories / 回忆 and The Running Sign / 会跑的广告牌 show numeric/completion gates, but participant-enable queries remain unknown. See [investigation](story-flag-investigation.md). Nothing is uploaded. Backups and in-game testing remain essential.
