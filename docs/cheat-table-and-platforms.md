# Cheat tables, system saves and platform evidence

## Inputs and limits

Inspected both user-supplied CT XML files, three extracted Switch slots, one Switch system save, the previously supplied PC slot, the existing PC system save and `RF4S.exe`. Reads were inert: no Lua / assembly execution, process attachment, original save writes or game-file changes. Runtime hooks, addresses and CT pointer chains were not copied into the save editor as file offsets.

`scripts/inspect_save_samples.py` prints a read-only save / CT inspection. `scripts/build_save_metadata.py` reads the game's symbol table and XML descriptions, validates flag ranges against the developer definitions, and emits `web/save-metadata.js`. The original CT files remain unchanged.

## Containers

| Container | Bytes | CRC storage | CRC coverage |
| --- | --- | --- | --- |
| PC slot | 140,424 | `[0, 4)` | `[4, 140200)` |
| Supplied Switch slots | 140,416 | `[0, 4)` | `[4, 140192)` |
| PC / supplied Switch system | 9,304 | `[4, 8)` | `[8, 9304)` |

System saves begin with `RF4D`; slot saves lack a reliable magic signature. Each original passes its own CRC, not the other platform's slot CRC span. Both slot formats have a 224-byte trailer outside CRC. The observed calendar, player, bag and GameFlags offsets are common to the supplied slots. That does not establish every unknown field's platform layout.

The converter is deliberately experimental: it assumes the eight-byte difference is candidate padding at the end of the covered body. It inserts zero bytes at Switch body end for PC output, or refuses to remove nonzero PC bytes there for Switch output, then preserves the trailer and rebuilds CRC. This assumption gives byte-exact back-conversion for all supplied slots. It is not evidence that every converted save loads or behaves correctly in either game. No in-game conversion acceptance has been performed. System containers need no length conversion, but unknown settings are not semantically remapped.

Original hashes are checked by `tests/verify_attached_saves.mjs` before and after in-memory testing. The supplied Switch hashes are:

- Slot 1: `9e84f872eab01b2c8992af66b8f0c42997562ea79aaa3788ef2d88db943b173b`.
- Slot 2: `37d8c37e62053433dff1ad7d6326c9116c97ed23e9f96d5ba921e5c8018aa7f8`.
- Slot 3: `d8a272bbc251eaf3337e334b12703e53908723cf95ed7f8e4e7f9ac8be7aa0a9`.
- System: `f86955823e287af44850a4ae62c3e0571090d37f21a6c986346d13f175828425`.

## Useful CT findings

| Area | Result |
| --- | --- |
| Money / base attributes / bag items | Useful cross-check of previously mapped runtime structures; already supported |
| Lumber / material stone / fertilizer | Added after corroborating direct save serialization and executable clamps |
| GameFlags single-bit entries | 92 inert descriptions mapped; 17 match existing symbols and 75 add zone-2 labels |
| Main story | CT v13 reads only 3 bits, conflicting with the 9-bit developer register; rejected |
| Several tutorial, barn and expansion entries | Conflict with wider developer registers; rejected rather than corrupting neighbors |
| Active request / required item / completion fields | Runtime `ExpGainPtr` fields, not verified as direct save offsets; not automatically mapped |
| Level / XP, name strings, friendship, soil, upgrade fields | Useful leads, but storage / encoding / display semantics are not fully corroborated; not exposed as new named fields |
| Multipliers, forced Runeys, instant tame, inventory hooks, scripts | Runtime code changes, not persisted scalar save fields; not added |

Both tables are useful for identifying candidate structures. V13 adds the extensive flag reference groups; V12.3 is mainly pointer / runtime-hook data. V13's 17-bit material displays are not trusted as gameplay limits: the executable's addition routines clamp the full stored values to 50,000.

The supplied executable serializer at `0x7D921..0x7D93F` stores lumber / material stone / fertilizer at save `0x3C`, `0x40`, `0x44`. Runtime fields are `0xE94FA4`, `0xE94FA8`, `0xE94FAC`. Addition routines `0xB4090`, `0xB40D0`, `0xB4110` clamp each to `0..50000`. These named edits use signed 32-bit storage.

Flag-copy evidence: serializer `0x7E798..0x7E7C7` copies the live bit buffer into save `0x1E8C4`. CT chains through `RF4S_TablePTR_Address` with final offset 8 refer to that live header's bit-buffer pointer. Single-bit descriptions can therefore be mapped physically; multibit CE interpretation must not replace the game’s MSB-first register representation. Physical mapping does not independently validate each CT label's meaning.

## System flags

`RF4S.exe` system-buffer RVA is `0xE704A0`; script-visible config flags are at `0xE704A8`, corresponding to system save offset 8. Signature / CRC generation is visible at `0x8230F..0x82345`: magic `0x44344652`, CRC over 0x2450 bytes starting eight bytes into the container.

The pinned upstream opcode reference supplies semantic evidence, checked against matching handlers in the supplied executable:

- Bit 0: ending / extra-orders flag, setter `0x21F690`, used after story progress 430 and in a debug ending path.
- Bit 2 / bit 3: wedding-recorded variants; the marriage handler sets different bits depending on spouse ID. The GUI keeps the variants numeric rather than guessing gender labels.
- Bit 4: setter `0x21F6C0`, used alongside story progress 511. Its readers / exact meaning are not established; the GUI explicitly marks this incomplete.
- Bit 5: setter `0x21F6F0`, data-transfer-order unlock, with a matching game dialogue reference.

Other system bits and settings are preserved unless edited through the advanced view. Changing these flags does not replay an ending, complete a slot or grant platform achievements.

Primary sources: [opcode table](https://github.com/arryndoestech/rf4-modkit/blob/799828a433d0e5be537b977918d5a7c773ad1200/refdata/opcode_table.json) and [town-event analysis](https://github.com/arryndoestech/rf4-modkit/blob/799828a433d0e5be537b977918d5a7c773ad1200/rf4s_modkit/subevents.py), plus the attached CT XML and supplied executable.

## Story and subquest scope

The developer `REG_MAIN_SCENARIO` spans bits 0–8. `AdvanceStoryProgress` at `0x21DB10` reads nine bits, writes encoded field `0x8000`, and advances only when the proposed stage is greater than the current stage. An offline register edit can rewind as well, which bypasses that game guard and may leave later state behind.

Town-event registers include `REG_SUBEV_RSV` (bit 153, width 9), `REG_SUBEV_NOW` (162, 9), `REG_SUBEV_AFTER` (171, 9), day / hour counters and event-specific working flags. `StartReservedSubEvent` also alters request state, initializes event scripts / participants and registers a calendar callback. Setting NOW / RSV alone does not recreate those side effects.

The editor now supplies named groups, full-width numeric stage editing, atomic named-value profiles and scoped donor snapshots. Main-story scope includes main symbols and mapped barriers; quest scope includes town-event / request flags. The all-flags scope can alter unrelated discovery / relationship / chest state. Neither scope automatically copies NPC records, request payloads, party/location, reward history or inventory.

A fully playable jump to any checkpoint is not implemented or claimed. Complete presets require controlled before / after saves or comprehensive path-dependent script analysis, followed by in-game validation. Checksum correctness and a reversible profile alone do not prove that a story jump is safe.
