# State-machine map

## Decision

Keep small, domain-owned state machines at existing module interfaces; do not add a framework or a single app-wide machine. Make the export checkpoint explicit in the shared `SaveDocument` first, because losing an unexported undo is a user-data risk in **both** UIs.

Validate external data at its load/import/edit interface, then use the accepted model internally. Keep one-off display and branching logic at its call site rather than extracting pass-through helpers. Catch failures only where recovery matters: transaction cleanup, user-facing file operations, or unavailable previews. Derived state is not another validation pass; each edit is new input and still needs validation before it can commit.

- **UX:** undo/reset after exporting still warns before closing or replacing a save. Native overview distinguishes imported, pending, unexported and exported edits. The browser says **download requested**, not that it verified a disk write.
- **DX:** one implementation owns export-state comparisons. Neither UI maintains a second payload snapshot. Byte editing, validation, history and export algorithms are unchanged.
- **AX:** named states, transition rules, source locations and executable tests give agents a navigable map rather than combinations of loosely related booleans.

## Scope and vocabulary

This is a source audit of first-party runtime code: `desktop.py`, `native_*.py`, `serve.py`, and authored `web/*.js`, including the optional legacy browser UI. Generated bundles/reference tables and vendored game tools are not independent app implementations. Build/release scripts are sequential tooling, not interactive app state machines.

A machine here has remembered state that changes what a later action can do. The map also identifies **derived guards** and **configuration axes** so they are not mistakenly rewritten as independent mutable machines. State names below describe existing behavior; except for `exportState`, they are analytical names, not new code enums. Families group repeated instances, rather than counting every form, record or flag separately.

## Runtime inventory: 23 families

| ID / family | State representation and transitions | Owning module / interface | Decision |
| --- | --- | --- | --- |
| R01 Workspace | No document → slot (`pc` / `switch`) or system (`shared`); demo is a separate source axis. Successful open replaces the document and clears drafts/export options. Invalid parse retains the previous document. | `web/save-core.js`: `SaveDocument`, `saveLayout`; `web/native-core.js`: `open` / `state`; `native_ui.py`: `open_bytes`; `web/app.js`: `openDocument` | Keep format/source separate from edit state. Never infer demo status from a valid CRC. |
| R02 Payload export checkpoint | `original` / `unexported` / `exported`, derived from current payload versus import or last export checkpoint. Edits, undo, redo, reset and export acknowledgement change the projection. | `web/save-core.js`: `exportState`, `markExported()`; native `state.exportState` | **Made explicit and shared.** Details below. |
| R03 Undo history | No history, undo available, redo available, or both. `transact` adds a patch group and clears redo; undo/redo transfer groups; reset is itself undoable. No-op/failed edits leave history alone. | `web/save-core.js`: `transact`, `undo`, `redo`, `reset` | Already a deep module. Stack depth is not evidence of unexported bytes. |
| R04 Form drafts | Clean ↔ pending raw input; apply success clears it, apply failure retains it. A pending draft may be valid or invalid; readiness is a separate guard. Re-render overlays drafts onto base values. | `native_ui.py`: `EditForm.track`, `changes`, `set_data`, `clear`, `apply_form`; browser `playerDrafts`, `bagDrafts`, `flagDrafts`, date/raw/typed inputs, `ExtendedUI.drafts`, `MarriageUI.drafts` | Preserve raw text and unknown IDs. Do not mark a draft valid merely because it parses locally; domain validation is authoritative. See instance list below. |
| R05 Atomic pending-edit batch | Idle → collecting callbacks → staging writes → commit or abort → idle. Nested Python collection is rejected; JS permits only bounded whitelisted edits. Any failure must retain all source bytes, history and drafts. | `native_save.py`: `_batch`, `apply_callbacks`; `web/native-core.js`: `applyOperations`; `native_ui.py`: `apply_all_drafts` | Keep this real seam: one undo entry for all valid pending edits, no partial application. |
| R06 Record identity / selection | Current record → requested record. Native applies the previous draft before accepting a switch; failure restores selection. Browser refuses record switches with pending drafts. Filters may preserve an existing drafted selection outside the visible results. | `native_ui.py`: `change_name_record`, `change_container`, `change_inventory_slot`, `change_record`, `change_candidate`, `change_flag`, recipe/flag filters; browser `selectBagSlot`, container handler, `ExtendedUI`, `MarriageUI` | Never retarget a draft to the newly selected record. Keep native automatic-apply and legacy manual-apply policies distinct. |
| R07 Save loading / replacement | Browser idle → file read (`loading`) → parsed candidate → accepted, failed, or awaiting discard confirmation (`pendingReplacement`) → confirmed/cancelled. Native performs synchronous picker/read/parse after discard consent. | `web/app.js`: `loadFile`, `openDocument`, replacement buttons; `native_ui.py`: `open_file` | A candidate is not the active document until accepted. Async reads remain a separate lifecycle from document edits. |
| R08 Close / discard consent | Clean workspace exits/replaces immediately; unexported bytes or drafts require confirmation. Cancel leaves it intact. Native `closing` bypass is for controlled teardown; browser `beforeunload` is a guard, not a guaranteed custom dialog. | `native_ui.py`: `discard_confirmation`, `closeEvent`; browser `beforeunload`, `rf4sHasUnsavedChanges` | Consume R02 plus R04. Do not use `dirty` alone. |
| R09 Export eligibility | Derived allowed/blocked projection over loaded/real source, save validation, drafts, target format/type and export options. Native applies drafts automatically; browser blocks while drafts exist. CRC repair/conversion consent differs by UI. | `native_ui.py`: `update_export`, `export_bytes`, `export_options`, `export_file`; `web/app.js`: `updateExportButton`, `exportOptions`, `conversionIssue`, `genderIssue`; `SaveDocument.build` | Preserve final domain validation even if a button is enabled. Native export stays enabled with pending drafts so it can validate/apply them. |
| R10 Native persistence | Validate/build → choose destination → create unique backup → flush/sync backup → atomic target commit → acknowledge. Save as uses picker → write → acknowledge without the direct-export backup step. Cancel/failure does not acknowledge. | `native_export.py`: `export_to_game_folder`, `atomic_write`; `native_ui.py`: `write_dialog`, `export_file`, `save_as` | Backup must precede replacement; never enable direct-write fallback. A successful build or report is not a save. |
| R11 Browser download resources | Build output → Blob URL created → link clicked/removed → request acknowledged → URL revoked later. Original/report/profile downloads do not acknowledge edited-save export. | `web/app.js`: `download`, `exportSave`, original/report/profile handlers | Preserve browser request semantics: the app cannot prove download completion or game-folder replacement. |
| R12 Reference import / replacement | Bundled/local/absent definitions → parse candidate tables/catalogs → validate → merge/replace, or retain old references on rejection. Pending edits guard replacement; imports are read-only with respect to saves/game files. | `native_ui.py`: `load_references`, `read_game`, `read_tables`, `read_languages`, `read_symbols`; `web/native-core.js`: reference/import operations; `web/app.js` import handlers; `ExtendedUI` recipe import; `LanguageCatalog`, `SaveReferences` | Stage before publishing. Do not conflate successful imports with save edits. Async draft/catalog checks must be rechecked at commit if these flows are changed. |
| R13 Reference/display caches | `ItemCatalog.itemIndex`: invalid/unbuilt → built. Native item pickers share three indexed models; icons load on demand. Slot rows are cached by native revision/container/language, with a separate filtered projection. Native state snapshots are reused until a successful mutating call. `GameIcons.cache` holds loaded icons or empty fallbacks. | `web/game-reference.js`: `ItemCatalog.add`, `browse`; `native_ui.py`: `_ItemChoices`, `_InventoryRows`, `render_inventory_grid`; `native_save.py`: `call`, `revision`; `native_icons.py`: `GameIcons.icon` | Display caches only. Imports/name changes invalidate choices; open/edit/undo/redo/profile/batch/export acknowledgement invalidate native state. Only successful operations advance the native revision; collected/uncommitted edits do not. |
| R14 Game-name language | English/default → selected loaded language; imports add choices; missing names fall back. Browser remembers selection in local storage and invalidates localized item indexing. Native uses `language` and bundled names. | `web/language-core.js`: `LanguageCatalog.select`, `name`; browser `renderLanguages`; `native_ui.py`: `update_languages`, `select_language`, `name` | Configuration axis. Stable record IDs and save bytes must survive label changes. |
| R15 Native interface language | Persisted `auto` / `en` / `zh-CN` → resolved captions. `auto` resolves from system locale; retranslation updates existing controls and Qt dialog translations. | `native_ui.py`: `select_ui_language`, `system_ui_language`; `native_i18n.py`: `UiLanguage`, `install_qt_translator` | Separate from R14; no control recreation or draft application on caption changes. |
| R16 Browser theme | `system` / `light` / `dark`, restored from local storage; DOM theme attribute and icon reflect selection. Storage failure is tolerated. | `web/app.js`: `applyTheme`, theme handler; `web/styles.css` | Configuration axis; no save-state coupling. |
| R17 Navigation, filters, pagination | Native active page/readiness and record filters; browser active navigation via click/intersection, item/flag page indices and query/group/view filters. Counts clamp page indices. Drag enter/leave/drop adds/removes visual highlighting. | `native_ui.py`: `select_page`, `refresh`, table/filter renderers; `web/app.js`: `refreshLayout`, `renderFlags`, `renderBag`, navigation observer, drop handlers; `ExtendedUI.filteredRecipes` | View state only, except explicitly guarded selection transitions in R06. Filtering must not discard drafts. |
| R18 Native responsive layout | Compact/wide navigation; one/two form columns; labels above/beside inputs; horizontal/stacked rows. Resize/font/layout events recompute mode without replacing controls. | `native_ui.py`: `resizeEvent`, `EditForm.reflow`; `native_layout.py`: `ResponsiveRow.reflow` | Derived layout modes. Preserve controls, focus, IDs and drafts. |
| R19 Preview / disclosure | Collapsed/expanded preview or expert details; current/draft preview tabs. Preview computation can produce available, unknown, or invalid/unavailable results. | `native_ui.py`: inventory preview, `render_item_preview`, `render_flag_impact`; `web/item-effects.js`: `previewItemEdit`; `web/flag-help.js`: `previewFlagEdit`; browser details/nav handlers | Read-only projections. Unknown effects/eligibility are not zero or false. Previews never alter source history or acknowledge export. |
| R20 Progress staging / risk acknowledgement | No profile → parsed/staged profile or donor snapshot → clear/apply. Story stage and named flags have separate drafts. Legacy application requires flag editing plus story acknowledgement; native profile application asks confirmation. | `web/app.js`: `profileDraft`, `storyValueDraft`, profile/donor/story handlers; `web/progress-core.js`: `parseProfile`, `snapshot`; `native_ui.py`: `read_profile`, `read_symbols` | Staging is not gameplay progression. Preserve sparse flag edits and reject overlap/unknown symbols. |
| R21 Editing opt-ins / expert guards | Legacy per-section disabled/enabled, combined with format/reference/record guards. Bag disable is refused with drafts; disabling legacy flags clears flag drafts; other disabled drafts may remain pending. Native `EditForm.allow` is an internal compatibility switch, automatically checked, not a user opt-in. | `web/app.js`: `allow-*` handlers; `ExtendedUI.enabled`, `MarriageUI`; `native_ui.py`: `EditForm.set_ready`, `changes` | Existing policies differ. Do not reintroduce native opt-in checkboxes or silently clear disabled drafts everywhere. |
| R22 Action feedback | Normal message ↔ warning/error. Native catches expected edit/file errors, uses a status bar/dialog, or records `test_errors` in test mode; browser changes notice text/warning styling. | `native_ui.py`: `attempt`; `web/app.js`: `attempt`, `notify`; `ExtendedUI.attempt`, `MarriageUI` submit | Feedback state is not commit state. Only successful operations clear drafts/acknowledge export. |
| R23 App hosting | Native startup initializes Qt/window/references → deferred save picker or self-test → event loop → accepted close. Legacy server binds loopback → retries with an ephemeral port if occupied → serves → interrupt/context exit closes it. Request guards accept/reject host/path and may supply absent optional reference modules. | `desktop.py`: `main`; `serve.py`: `main`, `EditorHandler.safe_request`, `empty_reference_module`; native close guard in R08 | Host lifecycle, not document lifecycle. Preserve loopback-only binding, read-only static serving and no automatic real-save loading. |

### R04 / R06 concrete instances

Native forms cover calendar, player values, player name, inventory, skills, recipes, friendship, relationships, people, monsters, trophies, marriage, system flags, named flags and raw edits. Selection guards apply to player-name bank/slot, inventory container/slot, each record selector, marriage candidate and named flag. Calendar/player/system/raw forms do not switch record identities.

Legacy `ExtendedUI` has six separate draft maps (skills, recipes, friendship, people, monsters, trophies); `MarriageUI` has its own candidate/draft map. The main browser module additionally holds calendar inputs, player/item/named-flag maps, story/profile drafts and raw/typed inputs. Legacy system-flag writes are immediate transactions, not a draft map. These repeated machines share conceptual rules but do not all share the same apply policy.

## R02: the explicit export lifecycle

The small interface is `save.exportState` plus `save.markExported()`. Qt crosses the same seam through `nativeInvoke('state')` and `nativeInvoke('markExported')`.

| State | Exact meaning |
| --- | --- |
| `original` | No export acknowledged yet, and working bytes equal imported bytes. |
| `unexported` | Working bytes differ from the last acknowledged export, or from imported bytes before any export. |
| `exported` | Working bytes equal the copied payload checkpoint of the last acknowledged export. |

| Event | Transition rule |
| --- | --- |
| Open a new document | New checkpoint is empty; state starts `original`. Failed open retains the existing document/checkpoint. |
| Edit / undo / redo / reset | Recompute from bytes; no latched flag or history-depth heuristic. |
| Native export / Save as succeeds | Caller acknowledges **after** writing; copy current working bytes as the checkpoint. |
| Browser edited-save download requested | Caller acknowledges **after** requesting the download. This does not verify on-disk persistence. |
| Build / preview / report / original backup / profile export | No checkpoint change. |
| Failed write / cancelled Save as / rejected validation | No checkpoint change. Drafts may already have validly applied in memory before a subsequent file failure, as before. |

`dirty` and `changedBytes` continue to mean **difference from the imported original**, for review/reset purposes. They intentionally remain distinct from `exportState`. For example:

```text
open A → edit B → export B → undo A
dirty = false; exportState = unexported; closing must warn

open A → edit B → undo A (no export)
dirty = false; exportState = original; no byte-change warning

open A → edit B → export B → edit C → edit B
exportState = exported even though history contains more entries
```

The checkpoint copies **working payload bytes**, not rebuilt output bytes. CRC repair, gender/appearance/dating overrides and platform conversion are export-only projections; they do not rewrite the working document or become undo entries. Drafts, demo status, export-option changes, external disk changes and destination identity are separate axes, not encoded by `exportState`. This preserves the existing acknowledgement semantics rather than adding new prompts for export-option changes.

## Save-encoded machines: do not mistake file edits for game transitions

These are persisted domain state that the app can inspect/edit, not game lifecycles implemented by the editor. A complete inventory of the game's own state machines is **not inferable** from this app. Keep unknown consumers and side effects explicit.

| Family | Observed state / transition evidence | Safe editor treatment |
| --- | --- | --- |
| Main story | `REG_MAIN_SCENARIO` stores 0–511. Audited game code advances only to a greater value and also updates runtime state. | `SaveDocument.setFlag` writes the register only. Sparse witnesses, not playable presets: [story investigation](story-flag-investigation.md#2-main-story-a-guarded-numeric-register-not-a-complete-world-state). |
| Town events and completion | Separate reserved/running/last-finished bank IDs (`RSV`, `NOW`, `AFTER`), elapsed counters, completion history, shared working flags and schedules. Start/finish have coupled side effects. | Raw/named edits are not start/finish operations: [event lifecycle evidence](story-flag-investigation.md#3-town-events-reserved--running--recently-finished-plus-separate-history). Eligibility preview retains unresolved participant queries. |
| Romance / marriage / appearance | Dating, both nickname selectors, spouse, anniversary/proposal/wedding/candidate flags, gender and cosmetic overrides are independent stored axes. No proven complete romance enum. | `RelationshipEditor` / `MarriageEditor` preserve unrelated fields. `SaveDocument.build` only performs explicit export corrections/cleanup and rejects incompatible spouses. No automated marry/divorce/event replay. |
| Record presence / player-name default | Monster occupied bit; system bank/slot presence bitmap; valid/unknown name bytes; empty name means game-generated default at load. | `ExtendedSave` edits existing monsters only. `PlayerNameEditor` refuses absent records and validates names; blank is an intentional default request, not corruption repair. |
| Inventory / equipment transformation | Empty ↔ populated item record; same-ID quantity/level change versus replacement/clear; stacked versus equipment; sequential crystal element changes and finite unused upgrade slots. | `setInventoryItem` preserves same-ID metadata and clears replacement metadata. `planElement` appends valid crystals without deleting upgrades and refuses insufficient slots. |
| Learned/recorded/unlock bits | Recipe unknown/known (variants share bits), trophy recorded results, system unlock flags, plus numerous developer/story flags with incomplete meanings. | `ExtendedSave`, system flags and progress profiles write verified fields only. They do not grant physical trophies, platform achievements, rewards or initialize dependent world records. |

Calendar, XP, friendship points and base stats are scalar values, not independent editor lifecycles. Assigning them does not simulate a new day, level-up, confession or derived-stat recalculation.

## Verification and follow-up rules

- `tests/document-state.test.js`: named lifecycle sequences for PC, Switch and system saves, checkpoint copying, no-op/failed edits, history branches, fresh documents and export-only projections.
- `tests/native-core.test.js`: state/acknowledgement through the shared native interface, failed replacement, and refusal to acknowledge inside an edit batch.
- `tests/test_streamlined_ui.py`: real Qt controls, export → undo → discard warning, cancelled/failed writes, successful Save as and pending-draft protection.
- `tests/test_native_inventory.py`: readable fonts/icons, lazy icon loading, full-storage model reuse, filtering/selection guards, search-popup ID selection, language/cache retirement, unknown IDs and unmatched search text; `tests/test_native_save.py` checks cached state ownership and invalidation.
- Nord regression checks cover normal/selected popup colors and reuse of the installed Fusion style. Recipe tests cover the button/hotkey, all-groups scope, linked variants, one-entry undo, no-op reuse and failed-batch draft preservation.
- Existing suites cover atomic drafts, byte preservation, CRC, conversions, selection, localization and compact layouts. Keep testing through the module interface, not by mutating the checkpoint.

Rebuild the ignored native bundle before Qt tests:

```powershell
npm run build:native-core
npm test
python tests/verify_upstream.py
python -m unittest discover -s tests -p "test_*.py"
```

Qt tests require `PySide6-Essentials`; missing optional dependencies can cause skips, not verification. Use synthetic saves and temporary destinations only. No game launch or real-save acceptance is established by these tests. A portable EXE must be rebuilt separately to include source changes.

Further changes should follow a demonstrated failing transition, not migrate every family at once. In particular, async reference/profile imports can outlive the draft/document context checked before their `await`; introducing guarded commit/generation checks deserves separate interleaving tests. Likewise, consolidating native record-switch handling must characterize invalid search text, filtered-out selections and signal reentrancy first. Neither is silently changed by this export-state fix.
