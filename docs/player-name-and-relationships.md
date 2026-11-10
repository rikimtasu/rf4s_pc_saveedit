# Player names, dating and nickname editing

These features were introduced in v0.2. In v0.3, edit directly: valid drafts apply automatically before switching records or exporting. Export explicitly writes to the game save folder with a same-folder backup first; Save as creates a separate copy. v0.2 retains its historical editing opt-in/manual Apply workflow. Game files are never changed.

## Dating & nicknames

Open an individual slot save, choose **Dating & nicknames**, then select a main NPC. The 12 marriage candidates have an editable dating-status checkbox; all 23 main NPC records have independent **NPC calls player** and **Player calls NPC** pickers. Barrett/Raven are not exposed here because their relationship/address layout is not established.

The pickers always offer the verified Lest/Frey default selectors and preserve the current stored ID, including unknown IDs. v0.3 bundles all seven localized nickname tables; optional reference reload/import accepts `rf3TxtHeroNickName` overrides. Labels follow **Game names**, with English fallback; Interface changes captions only. The player-name substitution token is shown as **[Player name]**, not mistaken for a literal nickname. Options list the complete audited table, not only the choices normally offered to that character by dialogue. Unsupported combinations may look unusual.

Current local builds add **Reset NPC calls player**, **Reset player calls NPC**, and **Reset both for current gender** buttons for the selected NPC. These stage only the requested nickname field(s), leaving saved and pending dating/friendship values alone. The target label shows **Lest** or **Frey** from the current working slot's gender byte, not its appearance, original gender or export-only gender choice. Unknown gender disables the shortcuts instead of guessing. Defaults for NPC ID `i` are NPC→player `23+i` / player→NPC `i` for Lest, or `70+i` / `47+i` for Frey. Apply or export to save the draft; resetting both applies as one undoable edit. Existing nickname drafts in the reset direction are intentionally replaced; unrelated drafts remain intact. All 23 main NPC records work without loaded nickname tables; guest layouts remain unsupported.

An edit changes only main-record `+8` bit 22 (`0x00400000`), `+12` u8, and/or `+20` bits 7–14 (`0x00007F80`). Friendship, other flags and other records remain untouched. Dating and nicknames are independent: clearing dating does not silently reset a nickname. No confession, breakup, gender eligibility, marriage or story prerequisite is simulated. If export dating cleanup is enabled, it overrides these fields for its listed targets.

The loader and relationship-query evidence is in [extended layout](extended-layout.md#dating-and-special-forms-of-address). `tests/test_replay_relationships.py` also verifies per-character edits against the actual dating predicate and address selection for all 12 candidates.

## Player name

**Open `rf4_sys.sav`**, choose **Player name**, and select the matching bank/slot. The game keeps 40 name records in two banks of 20; bank selection follows system config bit 6. Empty slots remain protected. Renaming a metadata record does not create an individual save or change its gender.

Names allow at most **6 Unicode characters / 18 UTF-8 bytes**. The 19-byte buffer includes its NUL terminator; overlong names, control characters and invalid Unicode are rejected, never truncated. Game fonts may not support every Unicode glyph. Unknown original name bytes remain untouched until an explicit replacement is applied.

**Reset player name to game default** prepares an empty-name draft. Export the system save to apply it (manual Apply is optional in v0.3). On the next load, the game getter generates the default name from the loaded actor's gender and its language branch: the audited branches produce **Lest / Frey** or **レスト / フレイ**. The editor does not translate personal names or guess from possibly stale system-record gender metadata.

Evidence for the audited executable:

- System buffer: `0xE704A0`, signature/CRC writer `0x8230F..0x8234A`.
- Metadata records: `system + 0x4F0 + record * 0xA4`.
- Name field: record `+0x14`, i.e. `system + 0x504 + record * 0xA4`, 19 bytes. The next farm-name field starts at `+0x27`.
- `0x800A5..0x8014E` selects the record and copies the current name there. `0x7F79F..0x7F7F0` selects it and restores its UTF-8 string through the real getter.
- Runtime name: `0xE94E60`. `0x89A30..0x89B26` returns it and regenerates a gender/language-specific default when its first byte is zero.
- Slot availability: system u32 bitmaps at `+8` / `+12`, set by `0x80440`; name edits preserve them and all adjacent metadata/farm names.

`tests/replay_player_names.py` replays the actual loader/getter instructions in a read-only emulator. Its language probes are explicit English/Japanese boolean stubs, and actor gender is a synthetic runtime input. Tests cover all 40 record offsets, default branches for both genders/banks, byte preservation, native UTF-8 marshalling, drafts, undo/redo and rebuilt system CRCs. They do not launch the game or substitute for in-game verification.

## System-flag safety correction

Named unlock flags are at **system `+0x10`**, not `+8`. The player-name audit caught the earlier editor's incorrect use of a slot-availability bitmap. Current source/local builds correct that offset and replay the actual data-transfer getter (`0x21F6D0`) as a regression. If an older build edited system flags, start from a pre-edit system-save backup when reapplying them; do not guess how to repair missing/extra slot-availability bits.
