# Additional saved fields

Offsets are file-relative, common to the supplied PC / extracted Switch slots. These controls preserve unrelated bytes and do not modify game definitions. Evidence comes from the supplied executable's serialization / load paths, inert CT labels and pinned rf4-modkit / Venti definitions. Storage verification and in-memory tests are not in-game acceptance tests.

## Skills

The serializer copies `player + 0x138` to save `0x5964` at `0x7DBEF..0x7DC7D`: 40 records ×8 bytes. Only the 38 named skills are editable; the final two dummy records are preserved. Each record has level (u16) at +0, an unused halfword at +2, and XP (u32) at +4. `0x21DE2F..0x21DE36` increments that level, and `SetPlayerSkillXp` writes the +4 counter. `Player_gainEXP` (`0xB3DE0`) caps XP at `0xFFFFFF`, skills 17–20 / 26–32 at 99, and the others at 999. Direct edits do not execute stat gains; XP and levels are independently editable.

## Containers

All records below use the bag's 28-byte representation. Serializer `0x7E1BC..0x7E30A` and deserializer `0x7F3E4..0x7F519` copy these arrays with matching counts and item-manager pointers. Actual saved contents corroborate their food / material / weapon / armor roles.

| Container | Offset | Serialized records | End (exclusive) |
| --- | --- | --- | --- |
| Bag | `0x5BD8` | 60 | `0x6268` |
| Fridge | `0x62A4` | 990 | `0xCEEC` |
| Storage | `0xCEEC` | 990 | `0x13B34` |
| Weapon box | `0x13B34` | 120 | `0x14854` |
| Armor box | `0x14854` | 120 | `0x15574` |

Spell tables, equipped / held positions, the later 150-record array and shipping arrays are not relabelled as these containers. Filling later records does not unlock capacity. Same-ID edits preserve metadata and mixed unit levels; replacements / clearing reset the record. Level changes alone do not recalculate saved equipment bonuses.

## Friendship

Main-character ids 1–23 have 44-byte records at `0x1DB40 + (id - 1) * 44`. Friendship points are signed 32-bit integers at +0, copied from runtime record +0xC at `0x7E6B6..0x7E6BD`. Only nonnegative values within the executable's `0x333E71` limit are interpreted. `Npc_FriendshipPointsToLevel` (`0x2279B0`) uses thresholds `[0,16,42,83,140,226,322,429,704,1009,1345]` through level 10; higher thresholds are `level * 336 - 2015`, with a level ceiling of 10,000.

Guest ids 24 / 25 (Barrett / Raven) use the array at `0x1DF34`, 8-byte records indexed by `id - 24`; the u16 at +4 stores level shifted left by two, with the bottom two bits preserved. `0x227A6F..0x227AAD` decodes it. Editing points does not run event / dating / marriage / achievement handlers. Children are labelled son / daughter rather than assuming personal names.

## People and tamed monsters

Person base stats use `0xB8 + character_id * 100` (only ids 1–26 offered). Monster base stats use `0xB44 + monster_slot * 100` (200 slots). Serializer `0x7DA46..0x7DAC9` copies runtime stats +0x1A0 for people, and `0x7DB3C..0x7DBBD` uses the tamed monster's slot id for the second array. This is a 100-byte base-stat record, not a pointer or template-table offset.

| Field | Record offset | Storage |
| --- | --- | --- |
| Maximum / current HP | +0 / +4 | i32 |
| Maximum / current RP | +8 / +10 | u16 |
| Strength / intelligence / vitality | +12 / +16 / +20 | low 24 bits; upper bytes retained |
| Combat level | +24 | u16; conservative editor range 1–65,530 |
| XP | +28 | u32 |

No automatic derived-stat recalculation or XP reset occurs. Uninitialized / inconsistent stats are not proof of an existing actor. These edits do not recruit, spawn, restore a story NPC or initialize new monsters.

The 200 monster-roster records start at `0x1BDB0`, stride 36. Serializer `0x7E52E..0x7E535` copies this runtime roster block. Saved names are read-only; species byte +20, barn bytes +21 / +22 and flags +32 are preserved. `GetTamedMonsterCount` (`0x212F50`) tests flags bit `0x1000` for occupied slots, so empty slots are never presented as editable tamed monsters.

Monster friendship is u16 at +24. `Monster_PointsToLevel` (`0x1E58C0`) uses `[0,8,20,36,56,80,108,140,176,212,255]` through level 10, then `10 + floor((points - 255) / 64)` capped at 1,000. A combined monster-stat / friendship edit is one atomic undo entry. Name, species, barn, chores, sibling records and unknown flags stay untouched.

## Recipes

Venti's `Recipe` definition is 20 bytes: result u16 at +0, recommended difficulty u16 at +14, learned_flag_id u32 at +16. Save recipe state is only a bit: `FLAGS_OFFSET` bit `4096 + 0x426 + learned_flag_id`. Reader `0x47CD6..0x47CF8` adds the flag-zone base and `0x426`, then performs a normal LSB-addressed bit test. It is not an editable asset difficulty field.

The supplied 21 recipe tables contain 637 recipe variants using 620 unique learned flags (bits 5159–5804). Some handmade / medicine alternatives share a flag and result despite different difficulty levels. Their shared state changes together; unrelated flag collisions are rejected. Bulk actions deduplicate these aliases and edit only the filtered unique flags. Placeholder result-zero records are omitted. Missing personal metadata does not enable guessed recipes; extracted definition tables can be imported read-only.

## Trophy / result records

Twenty-five developer-named `FLG_RESULT_*` / `REG_RESULT_FES_*` fields are offered with their existing widths and MSB-first register assembly. Single-bit states are recorded / not recorded; two-bit festival ranks are none, first / gold, second / silver, third / bronze. `RecordFestivalPlacement` (`0x2195B0`) corroborates the fishing / harvest / quiz / cooking / crafting fields. These are recorded achievement / festival results, not a complete trophy-room ownership map, physical trophy items or a Steam API unlocker. Setting them does not run rewards or platform achievement calls.

## Validation

Unit tests exercise exact field bounds, high-level threshold inverses, guest packed-bit preservation, container boundaries, linked recipes, atomic monster edits, original immutability, undo and converted CRC output. `node tests/verify_extended_save.mjs "<slot.sav>"` runs read-only checks on a real slot. The new controls were also exercised in the browser for apply, clear, undo and hidden-draft export guards. Test exported copies in-game with backups before relying on progression changes.
