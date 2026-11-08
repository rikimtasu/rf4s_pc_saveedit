# PC slot layout evidence

These additions were corroborated against the supplied `RF4S.exe`, Venti item definitions and one checksum-valid PC save. They are not an in-game acceptance test, a universal format signature, or a complete save map. Game and save files were read only; mutations were tested in memory. Offsets below are relative to the start of the 140,424-byte save; executable addresses are RVAs, not absolute process addresses.

## Historical original sample

- SHA-256: `fbb25bef45bcec44f2f966ee3ae9cd7b371ba67b0170055955cc8be46e900acf`.
- Stored and computed CRC: `0xE508FD13`.
- Calendar: Spring 2, year 1.
- Money: 200; health: 25 / 25; rune points: 56 / 56; strength: 5; intelligence: 5; vitality: 4.
- Bag slots 1–4: broadsword (328) ×1, cheap hoe (559) ×1, turnip seeds (753) ×9, turnip seeds (753) ×4. All level 1.

No real save or executable is bundled. The byte-exact original round trip and controlled player / bag edits are reproducible using `tests/verify_real_save.mjs`. The file's hash is rechecked after testing.

This is a historical sample, not the expected hash of the current save. The current PC save has since changed; verification compares each file against its own bytes and hash at the start of that run, never restores this older sample.

## Serialization anchors

- Slot buffer RVA: `0xE728F8`.
- Save serializer: `0x7D6F0..0x7F1D6`.
- Item deserializer: `0x7F1E0..0x7F76F`.
- Item initializer: `0x41C10..0x41CB6`.
- New-game base attributes: `0x88BB5..0x88C2D`.
- Money load clamp: around `0x7F912`; money addition: `0x3AFA0`.

Use `python scripts/inspect_executable.py <RF4S.exe> --function <RVA>` to view a function. `--start`, `--length`, `--refs`, `--span` and `--contains` support focused read-only inspection. RIP-relative references into the slot buffer are annotated as save offsets. Arbitrary ranges may begin in the middle of an instruction; function unwind metadata does not cover every small leaf function. This tool is an analysis aid, not automatic field verification.

## Player

| Field | Save offset | Storage | Editor range |
| --- | --- | --- | --- |
| Lumber | `0x3C` | Signed 32-bit | 0–50,000 |
| Material stone | `0x40` | Signed 32-bit | 0–50,000 |
| Fertilizer | `0x44` | Signed 32-bit | 0–50,000 |
| Money | `0x4C` | Signed 32-bit | 0–2,000,000,000 |
| Maximum health | `0x54` | Signed 32-bit | 1–2,147,483,647 |
| Current health | `0x58` | Signed 32-bit | 0–maximum health |
| Maximum rune points | `0x5C` | Unsigned 16-bit | 1–65,535 |
| Current rune points | `0x5E` | Unsigned 16-bit | 0–maximum rune points |
| Strength | `0x60` | Low 24 bits of unsigned word | 1–16,777,215 |
| Intelligence | `0x64` | Low 24 bits of unsigned word | 1–16,777,215 |
| Vitality | `0x68` | Low 24 bits of unsigned word | 1–16,777,215 |
| Order points (prince/princess points) | `0x20710` | Signed 32-bit | 0–99,999 |

All integers are little-endian. The upper byte of each attribute word is retained. Money, order-point and material ceilings are corroborated by executable clamps; other numeric ceilings are storage limits, not established gameplay caps. Minimum base attributes of 1 and nonzero maxima are conservative editor guards. Extreme values may be clamped or cause derived-stat overflow in-game; use reasonable values and backups.

Original attributes satisfying the checks enable named controls and subsequent export validation. An unrecognized original is not silently rewritten or blocked from earlier calendar / raw functionality. Plausible attributes do not authenticate the entire file.

The sample's base values also match row zero of `rf3Parameter.bin` interpreted through Venti's `LevelUp` definition. Word `0x70` contains 2, but is not established as player level; no level / XP control is exposed.

### Order-point serialization

`GetPrincePoints` (`0x21DFB0`) reads the signed currency at runtime RVA `0xE9AC08`; `AddPrincePoints` (`0x21DFD0`) clamps additions to 0–99,999. Serializer instructions `0x7EABE..0x7EAD3` copy the block beginning at that runtime address to save `0x20710`. The matching load at `0x80037` copies it back. The runtime address is not used as a save offset. These points do not establish or edit whether a particular order is unlocked.

## Export gender and appearance

| Field | Save offset | Verified meaning / write mask |
| --- | --- | --- |
| Gender | `0x36` | One byte: 0 = male / Lest, 1 = female / Frey |
| Appearance-swap flag | `0x38` | Bit 0 only; optional reset clears this bit |
| Outfit selection | `0x74` | Packed bits 18–23, mask `0x00FC0000`; optional reset clears these bits |
| Persistent appearance override | `0x20740` | Signed 32-bit selector; optional reset writes 0 and preserves the following word |

Serializer `0x7DC8B..0x7DC9F` writes gender as 0 when the actor's `0x08000000` male bit is set, otherwise 1. The loader uses save `0x36` at `0x840CC` / `0x84139`. Appearance-swap, outfit and persistent appearance-selection state are separate from this byte; resetting them preserves neighboring bits and does not rename the player. The three supplied Switch slots and the earlier PC sample read as 1 / Frey; the later failing save reads as 0 / Lest.

`SaveDocument.build()` preserves gender and cosmetics by default. Optional gender choices are `original`, `male` and `female`; `original` reads the frozen loaded byte and rejects unrecognized values rather than guessing. `resetAppearance` clears the two masks above and the four-byte persistent appearance selector, and requires a gender-correction choice. The output copy is corrected before CRC rebuilding and any experimental platform conversion. Original / working bytes and undo history are untouched.

Earlier browser downloads from the female PC sample matched the initial builder's byte writes, but those tests did not catch the missing persistent selector. Unit tests now cover that selector, adjacent bytes, native / converted output, trailers, invalid choices and original immutability. See the targeted reproduction below; byte checks alone are not proof of correct visuals.

### Male dialogue with Frey visuals: reproduction and fix

The later failing sample has SHA-256 `9c781e4da35852b9a8ee62fa7d964f2e4cbf7ca357c6d5207050607ff721421b`, valid CRC, gender 0, cleared appearance-swap flag / outfit, and signed value 9,999 at `0x20740`. This is a per-run historical fingerprint, not a hash to enforce on future saves.

Serializer `0x7EAE8..0x7EAF7` copies the block beginning at runtime RVA `0xE9AC38` to save `0x20740`; loader `0x8004C..0x80062` restores it. Load branch `0x84094` checks whether that selector is nonzero. At `0x840F7..0x84132`, values at least `0x188` (392) are passed to the appearance routine as 0. `0x165EB0` handles that fallback by switching protagonist visuals through `0x166060`, then restoring the previous actor-gender bit. This explains male dialogue with Frey visuals. The appearance-order handler at `0x1EAE54..0x1EAEA6` writes the same runtime selector; asset-table offsets are not used as save offsets.

`tests/replay_appearance.py` runs the actual instructions for `0x84087..0x841B1`, `0x165EB0` and `0x166060` in Unicorn. It starts from a normal Lest actor, restores the sampled selector and captures the body / portrait selections at actor offsets `0x220` / `0x22C`. It skips external resource / equipment-loading calls, refuses unaudited builds and non-default NPC-table paths, and never attaches to or launches the game. Its audited executable SHA-256 is `cb64f88be1f40ac932607188de85dab98c44f43a6a023c92a85e17dd18a2b803`.

Before the fix, the replay using the editor's male + reset output fails: actor gender remains male, but body / portrait are `0x4D1` / `0x4D2` (Frey). Clearing only save `0x20740..0x20743` in memory makes it select `0x4C1` / `0x4C2` (Lest). The corrected builder passes for both male and female. The adjacent word, order points, names, original bytes and undo history are preserved. No corrected copy has yet been tested in-game.

Optional read-only replay; requires `pefile`, `capstone` and `unicorn`, not runtime GUI dependencies:

```powershell
python tests/replay_appearance.py "<game-folder>/RF4S.exe" "<slot.sav>" --expect male --export-reset
```

Fully restart the game before an acceptance test so a previously loaded swapped actor cannot remain resident. Do not overwrite the original without a separate backup.

## Bag records

`0x5BD8 + slot * 28`, with zero-based slots 0–59. The final record starts at `0x624C`; the bag ends exactly at `0x6268`, where a different compact spell table begins. The 11 preceding 28-byte entries are not bag slots. The cheap waterpot at `0x5AC0` is in that preceding equipped / held area; its position label remains unknown.

| Record bytes | Meaning |
| --- | --- |
| 0–1, bits 0–10 | Item ID, mask `0x7FF` |
| 0–1, bits 11–14 | Quantity |
| 0–1, bit 15 | Unknown flag, preserved for same-ID edits |
| 2–3 | Unmapped metadata, preserved for same-ID edits |
| 4 onward | Zero-based item level entries |
| Remaining bytes | Unmapped metadata, preserved for same-ID edits |

The initializer clears all 28 bytes and initializes one level entry for nonstackable items or nine for stackable items. `max_stack > 1` selects the nine-entry representation; otherwise the limit is one. Level bytes are exposed as 1–10. Explicit level edits initialize every entry in that representation; blank preserves existing individual levels and newly added units inherit the first unit's level. Same-ID quantity writes use the `0x87FF` preserve mask. Removal and replacement clear the whole record, including flag and upgrade metadata.

The GUI requires real item-definition records, checks index bounds and rejects category 55 (category placeholders). It does not infer material names, equipment upgrade fields, other container labels or capacity unlock flags from asset offsets. All 60 serialized records are exposed, which does not establish that every slot is currently accessible in-game.

## Integrity

CRC-32 / IEEE is stored at bytes 0–3 and covers `[4, 140200)`. The final 224 bytes remain outside CRC and must be preserved. Player / bag edits and CRC rebuilding are exercised on the original sample in memory, with unchanged bytes checked outside the explicitly edited ranges. In-game loading, balance and semantic acceptance remain untested.

Switch / system containers, material-clamp verification, CT-derived flag labels and the experimental conversion policy are documented separately in `docs/cheat-table-and-platforms.md`.
