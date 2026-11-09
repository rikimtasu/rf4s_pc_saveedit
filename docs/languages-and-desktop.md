# Game languages and the portable app

## TEXT tables

The game manifest contains `rf3TxtItem_split2_1`, `rf3TxtNpc_split2_1` and `rf3TxtSkill_split2_1` with `.eng`, `.jpn`, `.fra`, `.deu`, `.kor`, `.twn` and `.chn` extensions. Each begins with `TEXT`, a little-endian u32 count, then count × (byte length u32, absolute offset u32) pairs. Strings are UTF-8 and NUL terminated. Readers validate all counts, bounds, termination and UTF-8 before importing anything. IDs are the original array indices, not search-result positions.

The supplied game has 1108 item names, 1000 NPC text entries and 40 skill entries per language. Only the editor's known character/skill IDs are exposed. `_split2_2` files contain descriptions and are deliberately rejected as name inputs. The Simplified Chinese names are in `bundlePatch2.mbundle`; archive precedence is Patch2, Patch1, then main. Nothing is written to a game archive. Language selection never modifies a save's own language/settings.

Generated `web/local-languages.js` stays ignored alongside the other personal references. Public builds emit null reference modules and use native **Read game folder** or extracted table imports. Private `--include-local` builds embed personal reference data and should not be published.

## Marriage controls

Controls use exact developer-symbol names and widths from the bundled `emdeb.bin` metadata. `REG_WIFE_ID` (bit 198, width 5) is labelled spouse for either protagonist; anniversary uses `REG_MARRIGE_SEASON` (277, width 2) and `REG_MARRIGE_DAY` (279, width 5). `FLG_PROPOSE` is ring acceptance, **not** a married flag. All 12 candidates have separate `MARRIAGE_CLEAR` and `JUST_MARRIED_CLEAR` event records. Editing a candidate record does not implicitly select that spouse.

Only drafted fields are written. Unknown stored spouse IDs remain visible and untouched until an explicit valid replacement is chosen. Loaded symbol tables must match the original marriage layouts. Pregnancy, child state, friendship, NPC schedules and `rf4_sys.sav` are not synthesized. The GUI supports reviewing selected flags, not a one-click guaranteed playable marriage/divorce preset.

## Desktop runtime

`desktop.py` and `native_ui.py` use actual Qt Widgets controls. There is no browser widget, HTML renderer, Chromium subprocess or local HTTP server. Native dialogs select references and save destinations; exports use `QSaveFile` to avoid partially written files.

`native_save.py` is a narrow save-operation seam reusing the tested binary algorithms. `npm run build:native-core` compiles them for Qt's `QJSEngine`, a standalone scripting interpreter—not a browser or QML scene. This avoids a second implementation of save-format logic in Python. Only fixed save operations and a UTF-8 decoder are exposed; game values are escaped JSON, never game-supplied executable code.

PyInstaller bundles Python and required Core/Gui/Widgets/Qml/Network DLLs. Qml supplies the interpreter only: QML plugins/scenes and all Quick/WebEngine rendering libraries are excluded. The build policy follows audited PE import chains: Widgets → Gui → Core; Qml → Network → Core. No HTML/CSS/font UI assets or browser engine are shipped. Windows' ICU is part of supported Windows 10/11, not an installer prerequisite; the build preflight avoids Conda's incompatible ICU shadowing it.

Closing prompts before discarding unexported changes. Private builds include personal references; public builds use native imports. `--self-test` exercises native controls, draft/export guards, all pages and an exported checksum. Engine-adapter tests verify exact round trips, conversion, packed attachments, marriage/story flags, monster UTF-8 and system saves.
