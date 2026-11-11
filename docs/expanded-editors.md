# End-game shortcut, soil, experimental relationships and roster creation

These features ship in **v0.4+** and the native source. `start.bat` prefers the local `dist/v0.41/RF4S Save Editor.exe` release build when present; prior local/published builds are retained. Only the end-game shortcut is also added to the legacy browser UI; the new soil/roster/experimental relationship controls are native-first.

**Close the game and back up the complete save folder first.** All operations edit working memory, share undo/redo and export through the existing checksum/backup flow. A correct CRC does not make an unsupported character or story state playable. Prefer Save as for experiments. No game executable, scripts, models or definitions are modified.

## 1. End-game shortcut

In **Expert: story flags**, click **Stage end-game flags (experimental)**. This prepares the **Story jump planner** with exactly:

```json
{
  "REG_MAIN_SCENARIO": 511,
  "FLG_SYELZA_ERACE": 0,
  "FLG_SYELZA_SUBEV_STOP": 0
}
```

It does not apply immediately, overwrite an existing story draft, or grant rewards. Read the preview, acknowledge incomplete dependencies, then Apply/export. It is one undoable edit. These are the final numeric marker and two documented adjacent Ventuswill-related flag clears, **not a complete ending preset**.

The separate system save, ending/achievement-related runtime path, third adjacent script clear, Ventuswill actor/schedule, map/party state, other quests, event cleanup, 250-tourist/3000-point rewards and prerequisites are not reconstructed. [Story-jump details](story-jump-planner.md) and [primary evidence](story-flag-investigation.md) explain why an early-game slot cannot be guaranteed to become a coherent end-game world by setting these three flags.

## 2. Soil editor

Choose **Soil editor**, field and soil-patch number. Edit health, growth/yield/quality/size, defense or packed base-level/progress fields. Values are labelled **raw** because their exact magnifying-glass units and percentages are not established. Sign bits are exposed separately from the lower bits; the editor does not apply an undocumented signed-number conversion.

**Prepare soil health 255** stages only that health field. To apply changed fields to all used patches of the selected field, check the all-patches option. It does not copy an entire patch or alter other soil attributes. Applying a bulk edit is one undo entry. Changing the selected patch applies valid old-patch drafts first; an invalid draft keeps both the old selection and draft.

The serializer at PC relative virtual address (RVA) `0x7DF09..0x7DF57` copies nine arrays of 18 records ×16 bytes from field-manager pointers at `+0x90`, saving them at **`0x1AEB4`**. Loader `0x7FAD0..0x7FB08` restores the same representation. A patch begins at:

```
0x1AEB4 + (field_index * 18 + patch_index) * 16
```

The nearby crop block at `0x18EA4` contains different, 12-byte records and is **never edited by the soil tool**. Locked-field flags, tilled state/crops, weather, growth simulation and unused patches are preserved.

Bit positions below are conventional LSB-first **within the soil record**, unlike the MSB-first value encoding of GameFlags registers:

| Field | First bit | Width |
| --- | ---: | ---: |
| Growth boost | 4 | 7 |
| Yield lower bits / sign | 11 / 21 | 10 / 1 |
| Quality lower bits / sign | 22 / 31 | 9 / 1 |
| Size lower bits / sign | 32 / 41 | 9 / 1 |
| Defense / health | 42 / 48 | 6 / 8 |
| Yield / quality / size base levels | 68 / 72 / 76 | 4 each |
| Overall / speed / yield / quality / size progress | 81 / 89 / 97 / 105 / 113 | 7 each |
| Overall / speed base levels | 120 / 124 | 4 each |

Field names, used-patch masks and raw field interpretations come from reading the supplied v12.3 Cheat Engine table (CT) soil entries as data; **the CT is never executed**. Used masks: all 18 for each of the five home fields; spring `0..7`, summer `0..3`, autumn `0,1,3,4,6,7`, winter `0..11`. UI numbers are one-based versions of those indexes, not independently verified map coordinates. The physical save/load mapping was independently verified in the local executable. Display scaling and the code that uses each field have not all been verified.

## 3. Non-candidate dating and spouse records

### Dating & nicknames

Marriage candidates allow dating-status edits without experimental consent. For another **main NPC ID 1–23**, check **Experimental non-candidate flags**, then edit Saved dating status. This edits only bit `0x400000` in that NPC's 44-byte record. It does not add confession/date scripts, special schedules, romance dialogue or a marriage event. Consent is off by default and resets after applying/clearing/switching records.

Guest IDs 24/25 have a different compact save block with no audited corresponding persisted dating bit. The editor does **not** write a main-NPC-shaped record over guest/header data. A literal “every NPC can date” feature therefore requires game-script/mod work beyond this save editor; it is not claimed here.

### Marriage flags

Spouse choices expose the five-bit register's complete **1–31** range plus None. Non-candidates require the same explicit experimental consent. IDs ≥32 cannot fit and are rejected, never truncated. Wedding/newlywed event fields target only the original 12 candidates; selecting a different spouse does not create missing non-candidate event flags.

This records a spouse ID, not a working wedding/family initialization. Guest/non-candidate IDs may be ignored, misinterpreted or crash unsupported script paths. It does not make monsters or arbitrary high-ID NPCs marriage candidates. Existing export-only dating cleanup continues refusing unknown/nonstandard spouses rather than guessing a repair.

The actual main-NPC load loop and dating query were replayed read-only for all 23 IDs. Each edited bit reached the executable's query. **Dialogue, confession, date and wedding execution were not replayed or tested in-game.**

## 4. Add roster NPC / monster

Choose **Add roster NPC / monster**:

1. Choose a species ID **1–255**, a name of at most six characters/18 UTF-8 bytes, an empty destination slot and a built barn room.
2. Choose basic level-1 stats, or copy the complete 100-byte stat block of an existing monster/NPC. The source ID is explicitly zero-based for monster slots and one-based for NPC IDs. Invalid/uninitialized stat blocks are rejected.
3. Acknowledge experimental roster risks and Apply/export. The new creature then appears in the existing **Tamed monsters** editor for supported stats/friendship edits.

The basic template is HP 100, strength/intelligence/vitality 10, level 1, zero XP/RP. It is **not species-scaled** and does not promise realistic defenses, attacks or produce. Copied templates retain all 100 saved stat bytes, including fields this UI does not interpret; they do not copy source roster flags, party membership or identity.

Allocation requires an empty one of the 200 roster slots, a built room and fewer than four occupied records assigned to that room. Existing monsters are never overwritten. Building/expanding barns is not silently done for you. If no room is available, build/expand a barn in-game before using this editor.

### Audited storage and allocation

- Roster base `0x1BDB0`, stride 36, count 200; serializer `0x7E52E..0x7E535` copies the `0x1C20`-byte runtime block.
- Name bytes `+0..18` (zero-terminated UTF-8), independent slot identity `+19`, species byte `+20`, home-room map `+21`, current map u16 `+22`, friendship u16 `+24`, saved coordinates i16 `+26/+28`, flags u32 `+32`.
- Occupancy mask `0x1000`. New records are zero-initialized then explicitly filled; no transient work/party/follow flags are copied. Current map starts at the assigned home room.
- Room levels are the ten three-bit `REG_MON_HOUSE[0-4]_[LR]_LV` registers at bits `818 + 3*i`; meaningful counts are `0..5`. Map `77 + barn_index*5 + room_index`, four monsters per built room.
- Real taming routine `0x1E3080..0x1E35BB` preserves slot identity, zeroes the roster, sets occupancy/species/friendship, checks built room counts and chooses a room with fewer than four occupants. `0x1E32D5..0x1E3359` establishes the room mapping and capacity. Home coordinate initialization uses X `106..233` and Y `170..232`; the offline tool uses the observed lower bounds, not a new randomization algorithm.
- Matching stat record: `0xB44 + slot*100`. The monster stat loader `0xAEB61..0xAEBC9` copies all 100 bytes. The builder copies/validates or initializes that record atomically with the roster.
- The load/count code at `0x1E3007..0x1E3038` recalculates the live occupied count from flags; the tool does not write a separate persisted monster-count field.

**Important:** accepting an 8-bit species value is not proof that the actor exists or supports barn/monster AI. NPC IDs below 48 follow different actor/script paths; some monster IDs are unused or special variants. This creates an experimental roster entry, not a town-NPC-to-monster conversion or a new model/AI definition. Town NPCs, relationships and other roster slots remain unchanged. Whether any particular NPC renders, follows, survives day changes or can be saved/reloaded is **unverified in-game**.

## Fonts and layout

The app bundles Noto Latin/CJK Medium. Native body text is **11pt**, with **16pt** page titles, **12pt** selected-item captions, **104×108** item tiles / **40px** tile icons, **48px** selected-item icons and **24px** picker icons. Rows use compact padding and control minimum heights. Newly opened windows keep these sizes rather than inheriting an enlarged application font. Forms reflow and scroll at 640×480, and resizing/language changes preserve drafts.

## Tests and limits

- `tests/new-editors.test.js`: packed-bit conservation on every used soil patch, seasonal masks, CRC/undo on PC/Switch, all 23 dating records, all representable spouse IDs, roster creation/template copying/capacity/failed batches and end-game staging.
- `tests/test_new_features_ui.py`: visible controls, acknowledgement gates, draft preservation, undo and compact Chinese pages.
- `tests/test_replay_soil_roster.py`: actual instructions copy all 162 soil records in both directions and count four newly written roster records.
- `tests/test_replay_relationships.py`: actual saved NPC loader and dating query for experimental main-NPC records.

Replay uses the same audited PC executable identified in the existing appearance/story investigations, synthetic mapped memory and a fail-closed instruction allowlist. It is read-only and does not attach to or launch RF4S. Byte-level Switch coverage does not establish gameplay equivalence. Test exported copies in-game with backups before relying on these experimental edits.
