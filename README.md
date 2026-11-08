# Rune Factory 4 Special save editor

A working, offline browser GUI for PC / Steam and extracted Switch saves, based on [arryndoestech/rf4-modkit](https://github.com/arryndoestech/rf4-modkit). Flat surfaces, local Inter typography, Tabler outline icons, responsive layout and light / dark / system themes follow `Visual.md`.

## Run

Double-click `start.bat`. Requires Python 3.10+ and a modern browser. No packages to install.

Alternatively:

```powershell
python serve.py
```

The launcher opens a browser and serves only `web/` on loopback, normally at `http://127.0.0.1:8764`. Keep the terminal open. If the port is occupied, it selects a free port. Use `python serve.py --no-browser --port 0` for a free port without opening a browser. Opening `web/index.html` directly is not supported because browsers restrict local JavaScript modules.

## Features

- Open / drag and drop 140,424-byte PC slots, 140,416-byte Switch slots, and 9,304-byte `rf4_sys.sav` system saves.
- Validate the original CRC-32 and rebuild it on export.
- Edit the verified day, season and year fields.
- Edit executable-verified money, order points (prince/princess points, 0–99,999), materials, current / maximum health and rune points, and base attributes.
- Browse bag items by definition category and select owned / empty slots in grouped lists; opt-in replacement, quantity and level editing.
- Edit fridge / storage (990 serialized slots each), weapon box / armor box (120 each), using the same metadata-preserving item editor.
- Edit 38 skill levels and experience, respecting 99 / 999 level caps.
- Learn / forget recipes individually or by a filtered group, using read-only imported definitions; crafting skill levels are separate from recipe difficulty.
- Edit friendship levels for 23 main characters plus Barrett / Raven, using the game's threshold formulas.
- Edit stored combat level, experience, health, rune points and base attributes for people and existing tamed monsters; edit monster friendship without changing species, barn or chores.
- Edit 25 verified trophy / festival-result records. This is not a complete trophy-room mapper or Steam achievement unlocker.
- Optional export-only gender correction: match the original, choose male / Lest or female / Frey, with a separate appearance / outfit reset.
- Read / edit the main story register, with explicit story-edit opt-in.
- Automatically load 1,822 developer symbols plus nonconflicting CT single-bit labels, with story / request / town-event / barrier filters; optional replacement `emdeb.bin` import.
- Full 9-bit stage editing, scoped donor flag snapshots and JSON progress profiles, applied atomically with undo. These are not simulated checkpoints.
- System ending / wedding / data-transfer flags, protected signature and system-specific CRC rebuilding.
- Experimental PC ↔ Switch slot-container conversion with explicit acknowledgement, candidate-padding checks and trailer preservation.
- Opt-in raw byte editing, bounded patches and a highlighted hex preview.
- Grouped undo / redo, undoable restore, replacement / close guards.
- Byte-exact original download, `.edited.sav` export and JSON change report.
- Export disabled for synthetic demos, unapplied drafts and invalid calendar / recognized-player values.
- Explicit repair consent for a damaged original checksum.
- Read-only item reference lookup with names, categories, item prices, rarity, equipment, consumable and upgrade definitions from your game copy.
- Typed 8/16/32-bit signed / unsigned save edits at an explicitly supplied manual offset, sharing undo / redo and CRC-safe save export.

Files are never uploaded or overwritten. Edits live in browser memory; only the theme preference persists. External project / help links are user-initiated. The Python server has no save API.

The main interface shows applicable slot controls and compact, initially collapsed skills, recipes, friendship, people, monsters and trophy editors; system saves show persistent unlock flags and export. `Expert tools` starts collapsed and contains story / subquest tools, references, raw edits and incompletely identified system flags. Closing any editor does not discard drafts; pending drafts still block export. Exact working-byte changes and the export checksum are also collapsed by default.

## Venti data-table references, save editor only

Venti’s data definitions are used only as reference information. There is no mod builder, TOML editor, ZIP exporter, load-order manager, DLL installation or game-file writer.

The `Expert tools → Item reference` section is read-only. It uses the modkit’s item-name registry and four tables interpreted using Venti’s C++ definitions:

- `rf3ItemList.bin`: item identity, category, buy / sell values, rarity and stack limit.
- `rf3ItemEquipmentParam.bin`: base equipment properties.
- `rf3UseItemParam.bin`: consumable effects.
- `rf3ItemStrengthening.bin`: upgrade-material properties.

Your supplied game copy was inspected read-only. These tables contain 1,108, 1,106, 318 and 1,150 records respectively, with record sizes matching Venti’s definitions. Local reference values are in the ignored `web/local-game-data.js`; no binary game assets were unpacked into the game or changed. Use `Read tables` to supply extracted reference files directly, or regenerate metadata without modifying the game:

```powershell
python scripts/gather_game_data.py "<game-folder>"
```

`Copy ID to typed field` only prepares a save-edit draft. It does not insert an item, locate inventory or write bytes. You must enable raw editing and supply an independently confirmed save offset before applying it. Category and item-flag names are decoded from Venti’s definitions, but those definitions do not establish their positions in a save file.

Venti does not need to be installed. If personal reference metadata is absent, the server supplies an empty module and the editor still works with the name registry / manually imported tables. See `web/help.html#references` for limitations.

## Important limitations

This is not a complete save map. Calendar and GameFlags follow upstream; additional fields were corroborated against the supplied `RF4S.exe` and real saves, not copied from the community 3DS map. Equipped-position labels, farming, complete trophy-room ownership and the dependent state needed to create / tame actors or safely rewrite relationships remain incomplete. Raw patches are for offsets independently confirmed by the user.

CRC validity is not proof of valid game state. Date changes do not run daily game updates. Story changes can break progression. Checksum repair does not recover corrupted data. Real saves passed byte-exact round trips and in-memory checks. The user's in-game load of a prior export exposed the incomplete appearance reset; the corrected reset, platform conversion and story jumps still need in-game acceptance tests. Executable-verified means layout evidence, not universal semantic acceptance.

Back up your whole save folder, close the game, export a new file, and manually replace the intended slot with its original filename. Handle Steam Cloud conflicts separately. See `web/help.html` for the full workflow and the upstream flag-layout documentation caveat.

## Player and bag editing

Player controls expose stored base values, not computed attack / defense or equipment bonuses. Money is bounded at 2,000,000,000, order points at 99,999, and lumber / material stone / fertilizer at 50,000 by the executable. `Player → Money and order points → Order points` edits the prince/princess currency used for orders, not order-unlock flags. Health uses signed 32-bit storage, rune points unsigned 16-bit storage, and attributes the low 24 bits of their words. Upper attribute bytes are preserved. Other numeric limits are conservative editor / storage limits, not verified gameplay caps. Current health / rune points cannot exceed the respective maxima. Named controls are hidden if the original attributes do not satisfy these checks; such files can still round trip and use calendar / expert features.

Bag editing requires `rf3ItemList.bin` definitions (your local metadata is already loaded) and explicit opt-in. Select a saved slot, choose an item group, and browse without needing a search. Name / ID search narrows that group; `Manual item ID` is collapsed. The default card view shows occupied slots by category. Choose `All slots, including empty` or an empty entry in the saved-slot list to add an item. Groups come from actual definitions; a name-only catalog never guesses categories or enables editing. Quantities are limited to 9 for stackable items and 1 otherwise. Choose `Empty slot / remove item`, or use ID 0 and quantity 0, to clear a slot. Category-placeholder definitions are rejected.

Same-ID edits preserve unknown flags, upgrades and other metadata. Blank level preserves individual stack levels, including mixed levels; extra units use the first existing unit's level. An explicit level of 1–10 sets every level entry. Replacing the ID or clearing a slot resets the entire 28-byte record; fresh items have no custom upgrade metadata. Changing equipment level alone does not recalculate its saved stats. The bag excludes held / equipped entries and the following spell table. All 60 serialized positions are available in the slot selector / all-slots view; extra capacity is not unlocked by inserting an item in a later slot.

The read-only evidence and exact offsets are recorded in `docs/save-layout.md`.

## Gender on export

In `Review & export → Character gender`, enable `Auto-correct gender on export`, then choose `Match original save`, `Male · Lest` or `Female · Frey`. Correction is off by default, so unedited exports remain byte-exact. Matching the original uses the frozen loaded gender byte, not a later raw edit. If the original byte is unrecognized, select male or female explicitly.

The separate, unchecked `Reset appearance, portrait and outfit` option clears the appearance-swap flag, packed outfit selection and persistent appearance override, preserving neighboring bits. This removes those cosmetic choices; leave it off if you want to keep them. The gender byte and displayed appearance are separate, so changing gender alone may not change swapped visuals. Names are never renamed. Overrides affect only the downloaded copy and rebuilt CRC, not the working save, original backup or undo history; the JSON report records the export choice and original / exported cosmetic state separately from working-byte edits. The same override applies before experimental platform conversion.

The reported male-dialogue / Frey-portrait mismatch was reproduced in a read-only replay of the executable's appearance-load branch using the latest supplied save. The original reset missed the signed appearance selector at `0x20740`; its value of 9,999 activates the loader's opposite-protagonist fallback even with swap / outfit bits cleared. The corrected reset clears that four-byte selector too. The replay selects the requested protagonist's body and portrait after correction; it does not render the game or replace an in-game acceptance test. Restart the game fully before testing a corrected copy, and keep backups. See `docs/save-layout.md` for evidence and the optional replay command.

## Skills, recipes, friendship, people and monsters

Each named editor is opt-in and shares undo / redo, draft guards and CRC-safe export. Skills expose level and XP independently; changing a level does not simulate level-up stat gains, and unchanged XP stays intact. Crafting skills and resistances cap at 99, the remaining skills at 999. NPC / monster combat levels use a conservative 65,530 editor ceiling rather than the skill caps.

Recipe difficulty is a game-definition value, not a saved level: the save stores learned flags. `Recipes` can read extracted `rf3Recipe*.bin` definitions without modifying them. Search / group filters narrow the bulk learn / forget buttons. Some recipe variants share one flag and change together. Personal recipe metadata can also be generated read-only:

```powershell
python scripts/gather_save_references.py "<game-folder>"
```

Friendship levels use the executable's point thresholds; guest levels preserve their low packed bits. These edits do not run gift processing, dating / marriage events, achievements or story prerequisites. People and monsters expose stored base stats, not derived equipment bonuses. Only existing tamed-monster slots can be edited; their names, species, barn placement, chores and unknown flags are preserved. New actor creation, monster taming / species replacement and actor renaming are not offered.

`Trophy records` edits verified achievement / festival fields only (festival ranks: none, gold / first, silver / second, bronze / third). It does not award physical trophy items, map every trophy-room entry or unlock Steam achievements. Detailed storage evidence and limitations are in `docs/extended-layout.md`. In-game acceptance of these new edits is still pending.

## Portability

There are no machine-specific save / game folder paths in the app, launcher or runtime scripts. `start.bat` resolves its own directory; `serve.py` resolves `web/` relative to itself. Reference-gathering and real-save checks take paths as CLI arguments. The public repository excludes saves, exports, CT attachments and personal game-reference modules. Missing reference modules receive null fallbacks; item / recipe definitions can be imported through the interface. Runtime operation is offline and does not require the original workspace or game installation path.

## System saves and platform conversion

`rf4_sys.sav` has an `RF4D` signature at bytes 0–3, CRC at bytes 4–7, and checksum coverage `[8, 9304)`. Named system flags and the advanced editor work with its own bounds; slot-only calendar / bag / story controls are hidden. Both supplied system saves use this container, so no size conversion is needed. This does not prove all platform-specific settings have interchangeable meanings. System unlock flags do not complete a slot’s story or grant achievements.

For a slot, choose the target in `Review & export → Output format`. Source format is the default. Cross-platform output requires experimental-conversion consent and a recognized player / calendar profile. The converter retains the common body, inserts eight zero candidate-padding bytes before the PC trailer or removes them for Switch, preserves the final 224 bytes, and rebuilds the target CRC. PC-to-Switch conversion is blocked when those eight bytes contain data. No unknown bytes are silently discarded.

The three supplied Switch slots pass native and conversion-back round trips; both system saves pass native round trips. This is structural verification only. Neither cross-platform output nor the placement of every unknown field has been confirmed by an in-game load. Do not treat conversion as a fully validated migration, and keep the original backups. The editor exports new files; it does not inject saves into a Switch, decrypt containers, manage account IDs or defeat console security.

## Story, town events and requests

Open `Expert tools`, enable story editing and acknowledge jump dependencies to edit `Progress profiles`. The main register is all 9 bits, values 0–511. Only script-backed numeric markers are listed; no guessed chapter presets are advertised. `Story flags` loads developer names automatically; use the request / town-event group filters or search `QUEST`, `SUBEV` or a CT reference label. Multi-bit registers preserve the game’s MSB-first assembly, not Cheat Engine’s numeric bit ordering.

Profiles use `{ "format": "rf4s-progress-v1", "label": "...", "flags": { "REG_MAIN_SCENARIO": 430, ... } }`. Download a scoped snapshot, edit its named values, read it back, review the staged changes, then apply in one undoable transaction. `Read donor save` stages a snapshot at the selected scope without modifying either file. Story scope includes main-story symbols and mapped barriers; quest scope includes request / town-event flags. All-flags scope can also change relationship, discovery, chest and unlock state. Staged profiles can be downloaded for full review.

This is not yet a proper “playable jump to any point” feature. It does not recreate NPC records, party / map position, quest payloads, rewards, inventory or cutscenes. Starting a town event involves queue / participant / initialization state in addition to `REG_SUBEV_RSV` and `REG_SUBEV_NOW`; setting those registers alone is not a safe start preset. Controlled before / after saves and in-game acceptance tests are needed for complete checkpoint profiles. Rewinding can leave later unlocks behind; moving forward can omit prerequisite state.

The CT comparison and source evidence are in `docs/cheat-table-and-platforms.md`. CT Lua / assembly was never executed and no running process was attached.

## Verification

Requires Node.js 20+ for tests, not for running the editor:

```powershell
npm test
python tests/verify_upstream.py
python -m unittest discover -s tests -p "test_*.py"
```

Tests cover CRC vectors, exact sizes, byte preservation, flags, player values, gender / appearance, skills, linked recipes, friendship thresholds, actor stats, containers, atomic monster changes, drafts, references, undo and repair. Eight server tests cover local assets, upload rejection, path / host guards, security headers, absent mod-builder routes and relocated public assets without personal metadata. The Python parity check compares JavaScript output with the pinned upstream `SaveFile` and `EmFlagTable` on a deterministic synthetic fixture.

Optional, read-only verification with your own real save and local item metadata:

```powershell
node tests/verify_real_save.mjs "<PC-slot.sav>"
node tests/verify_extended_save.mjs "<PC-or-Switch-slot.sav>"
```

This never writes the save. It checks original hash stability, byte-exact round trip, in-memory player / bag edits, CRC, unknown-byte preservation and undo. `scripts/inspect_executable.py` is an optional read-only analysis aid requiring `pefile` and `capstone`; neither is needed to run the GUI.

Read-only checks covering the supplied Switch slots and both platform system saves:

```powershell
node tests/verify_attached_saves.mjs "<extracted-Switch-folder>" "<PC-slot.sav>" "<PC-system.sav>"
```

## Source and licenses

- Upstream reference: commit `799828a433d0e5be537b977918d5a7c773ad1200`.
- `web/save-core.js`: dependency-free JavaScript adaptation of upstream `save.py` and packed fields / EMDb parsing from `emflags.py`.
- `web/save-metadata.js`: developer symbol metadata from the supplied game, with inert single-bit CT reference descriptions; generated by `scripts/build_save_metadata.py`. CT descriptions are not an upstream endorsement or independently verified quest semantics.
- `vendor/rf4-modkit/`: unmodified reference sources, not runtime dependencies. MIT license retained.
- `web/assets/Inter.ttf`: copied from the user-provided Inter font; SIL OFL in `Inter-LICENSE.txt`.
- Local Tabler outline font: v3.35.0, MIT; attribution in `web/assets/Tabler-LICENSE.txt`.
- Venti reference: commit `6588b5ff7c28ddd82fd5b2a4591486af3e9c901a`, GPL-3.0. Original definitions and license are in `vendor/venti/`; the derived schema and reference reader follow GPL-3.0. See `COPYING` and `ATTRIBUTION.md`.
- No game binaries, loader DLLs or real save files are bundled.

### Regenerate definition metadata

```powershell
python scripts/build_game_schema.py
```

Generation works offline from the source references and refuses any struct size that differs from the C++ `static_assert`. `scripts/fetch_venti_reference.py` is an optional reference-maintenance tool, not a runtime requirement. The metadata contains table definitions, not save-offset mappings.

Regenerate save-specific developer symbols read-only. CT labels are optional: pass `--table "<table.CT>"` when you have a separate CT attachment; the public repository does not depend on one.

```powershell
python scripts/build_save_metadata.py "<game-folder>"
```
