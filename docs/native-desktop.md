# Native Windows save editor

The native editor bundles data and icons, applies valid drafts automatically and exports directly to the game save folder with backups. It includes tourist-count edits, named Extra Orders, soil/staff shortcuts and [Backups & rollback](save-history-and-order-names.md). See the [standalone workflow](standalone-workflow.md) for export details. This guide covers v0.41; earlier packages remain unchanged.

Extract the v0.41 ZIP and open `RF4S Save Editor.exe`, or use `start.bat` for a local build. No installation, browser, server, Python or Node is required. The interface uses native Qt Widgets. The bundled scripting interpreter runs only shared save algorithms; it does not display web pages.

The app uses the Nord palette (Polar Night backgrounds, Snow Storm text and Frost highlights) with Fusion rendering across the GUI, dropdowns and search suggestions. It has 11-point Noto Medium body text, 24-pixel picker/portrait icons, 40-pixel tile icons and 48-pixel selected-item previews. `start.bat` prefers `dist/v0.41/RF4S Save Editor.exe`; build it with `python -m scripts.build_desktop --output dist/v0.41` after installing the desktop build requirements. Earlier local builds remain fallbacks and previous published releases are unchanged.

1. Close the game and back up your save directory.
2. The launch save picker starts at `%APPDATA%\Rune Factory 4 Special`; if absent, it uses your home folder. Select a PC / extracted Switch slot or `rf4_sys.sav`, or cancel and use **Open save** later. No save is auto-loaded.
3. References, seven name languages and icons are already bundled. Optional reload/import controls in Save overview allow overrides without modifying game files.
4. Choose a page and change values directly. Apply is optional; valid drafts apply automatically before switching records or exporting.
5. Use **Review & export** to inspect the target, then **Export edited save** to write it directly into `%APPDATA%\Rune Factory 4 Special` with a same-folder backup first. Use **Save as…** for separate copies or extracted Switch output. Handle Steam Cloud separately.

## Items and attachments

Select a container and saved slot in the icon grid. Tiles show quantity badges, level and the real saved slot number; hover for the full name and mixed unit levels. **Show empty slots** is checked by default; uncheck it to show occupied slots only. Showing/editing later positions does not unlock capacity. The filter searches localized names/slots. Item dropdowns offer large-icon search suggestions; choose a matching entry rather than leaving arbitrary typed text.

Storage uses one decoded slot list per document revision. Pickers share three indexed catalogs and load icons on demand, so selecting a slot does not rebuild thousands of entries. Popup/grid sizing does not decode the entire icon archive for closed controls. Filtering or selecting a slot reuses the models. Imports/language changes invalidate the appropriate display caches; edits, undo, redo and opening another save refresh the slot data.

Changing an item ID resets the previous item's metadata, including attachments. Same-ID edits preserve unchanged fields. Blank level preserves mixed unit levels. Zero removes an attachment; attached IDs are restricted to 0–1023. Equipment supports three crafting and nine upgrade attachments, inherited equipment, total-level and rarity bonuses. Elements append crystals to unused upgrades, raise the level and never remove attachments automatically. An element change is blocked if there are not enough free upgrade slots. Special effects remain the game's responsibility; in-game acceptance is not guaranteed.

The current/draft **Item effect preview** is read-only and uses the same item-edit algorithm on a copy. Game tables supply base equipment and use effects, inherited-equipment references, and individual craft/upgrade material bonuses. Percentages are decoded from fixed-point values; unknown/missing references remain unknown. The planned element is shown separately. Final stats, material-level scaling, repeated-material penalties, total-level/rarity bonuses, special multipliers, inheritance combinations and actor stats are not simulated.

## Recipes

In **Learned recipes**, click **Learn all recipes** or press **Ctrl+Shift+L** to learn every loaded recipe across all groups, ignoring the current search/filter. Linked variants are deduplicated, and any selected recipe draft joins the operation in one undoable edit. It changes memory only; export to save. The shortcut is disabled for system saves or missing definitions. Filtered learn/forget buttons affect only their filtered lists.

## Marriage and other editors

**Dating & nicknames** adds individual dating flags for marriage candidates and independent NPC/player address pickers for main NPCs. Localized nickname choices are bundled. **Player name** edits the selected record in `rf4_sys.sav` (not an individual slot file), with UTF-8 bounds and a draft-only game-default reset. See [usage and executable evidence](player-name-and-relationships.md). Names, nicknames and dating remain independent; these edits do not simulate romance or family events.

Spouse, anniversary, ring acceptance and wedding memory are grouped with candidate marriage/newlywed flags. Selecting an event candidate does not change spouse. Apply drafts as one undoable edit. This does not initialize pregnancy, children, schedules or system unlocks, or replay wedding events.

Calendar/player (including Tourists), skills, individual/bulk recipes, friendship, people/monster stats, trophy records and system flags retain their value limits. Expert pages expose full-width named flags, progress profiles and bounded raw integers/bytes. Review/export includes direct save-folder export with automatic backups, Save as, JSON changes, **Restore original in memory**, optional gender/appearance correction and experimental PC ↔ Switch conversion. The in-memory restore is undoable; disk rollback is separate and clears the previous undo history after a successful restore.

The **Clear incompatible dating and their special nicknames (keep friendship)** export checkbox is off by default. Choose Male, Female or Match original gender first. Lest clears the six bachelors; Frey clears the six bachelorettes. Preview lists the targets. Both forms of address reset, but friendship, other NPCs, story/event history, date counts and achievements stay unchanged. An incompatible spouse blocks cleanup; marriage/family state must be handled separately. This is not a simulated breakup or complete romance-event reset.

Drafts persist across pages. Valid drafts apply automatically before switching records or exporting; an invalid draft stays visible and stops export without partially applying other pending edits. Undo/redo shares the same binary-edit history. Opening another save or closing prompts before discarding unexported work. There is no synthetic-demo button.

Compact windows (down to 640×480) use a narrower wrapping navigation list and reflow large forms into one column, with labels above controls when needed. Action rows stack and long consent captions wrap. Item previews use **Current item / Draft result** tabs; uncheck the preview heading to collapse it and make more room. Long pages scroll vertically so Apply/Clear controls remain reachable. Resizing and language switching retain the same controls, drafts and save bytes.

Standard confirmation buttons retain English captions when no Chinese catalog entry exists, rather than becoming blank. Confirmation dialogs reserve enough width for their titles and native window controls; Cancel remains the safe default. Barrett / Raven friendship edits use their corrected packed fields (`0x1DF6C` / `0x1DF74`); all main-NPC friendship mappings and level thresholds are checked against read-only replay of the audited game code. Start from a pre-edit backup when reapplying guest levels exported by older builds: those builds wrote into the guest-block header, and the editor does not guess how to undo those unrelated changes.

**Interface / 界面** is independent of **Game names**. **Follow system** defaults to Simplified Chinese for Chinese system locales and English otherwise; manual English/Chinese overrides are remembered. Switching interface language preserves controls, even partially typed drafts, and does not change save data. The legacy browser UI is not fully localized. Seven game-name languages are bundled.

The app uses **Noto Sans Medium (500)** with bundled **Noto Sans CJK SC Medium** for Chinese, including user-entered text and previews. Both fonts load from the app itself without installation or network access.

v0.4 includes **Soil editor**, **Add roster NPC / monster**, a staged **end-game shortcut**, explicit experimental non-candidate relationship/spouse flags, and current-gender **nickname resets**. These are not game-script modifications; unsupported NPCs can remain unplayable. See the [complete instructions and storage evidence](expanded-editors.md).

Story flags retain raw developer identifiers and original descriptions. Human translations, symbol-only interpretations and static script evidence are distinguished. Group/Chinese-description search and the draft impact preview do not apply dependency repairs or simulate events. Memories / 回忆 and The Running Sign / 会跑的广告牌 show numeric/completion gates, but participant-enable queries remain unknown. See [investigation](story-flag-investigation.md). Nothing is uploaded. Backups and in-game testing remain essential.

The **Story jump planner** previews target + explicit JSON supporting flags as a single edit, including event-bank state, partial 442/511 script comparisons and exact byte masks. Profiles containing the main-story register are staged for review, not immediately applied. Risk acknowledgement is required for a changed jump; decreases require separate rewind consent. Valid acknowledged drafts participate in the existing atomic export batch. See the [detailed explanation and workflow](story-jump-planner.md); no playable checkpoint preset is claimed.
