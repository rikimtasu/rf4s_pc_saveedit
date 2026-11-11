# Extra orders, maximum soil and staff gear shortcuts

These are **native desktop** features. Close RF4S and back up the whole save folder first. Nothing is written to game files or your save folder until export. The legacy browser interface is unchanged.

For the local portable build, run **`start.bat`** or **`dist/order-soil-gear/RF4S Save Editor.exe`**. Earlier executables and the published v0.4 ZIP are retained unchanged.

## Extra orders

Open a slot save and choose **Extra orders**:

- Enemy level increase: **0–10**. The CT's unsafe 127 value is deliberately rejected.
- Disable combat EXP, disable skill EXP, disable town events.
- Show enemy levels / HP.
- Appearance order: default, opposite-gender protagonist appearance, or the CT-listed NPC appearance IDs. Save and reload; this does **not** change dialogue gender. Unsupported models/script paths can still fail in-game.

For the **menu unlock**, open **`rf4_sys.sav` → System save unlocks → Prepare extra-orders unlock**. This prepares only system bit 0 at `0x10`; Apply/export it separately. It does not advance a slot's story, run an ending, award achievements or change save-slot availability bitmaps. Export's optional appearance reset still overrides an appearance-order edit in the exported copy.

### Layout evidence and limits

The v12.3 CT names fields relative to `RF4D`; v13 places the corresponding fields relative to `ExpGainPtr`. The **already audited** persistent appearance selector is v12.3 `RF4D+2A798` / v13 `ExpGainPtr+24` (hex) → save `0x20740`. That common block anchor maps the other entries as follows; neither runtime pointer is treated as an absolute file offset:

| Setting | Slot offset | Storage |
| --- | --- | --- |
| Disable town events | `0x2071E` | bit 5 |
| Disable combat / skill EXP | `0x2071F` | bits 3 / 4 |
| Show enemy level / HP | `0x2071F` | bits 5 / 6 |
| Enemy level increase | `0x2072C` | u8, guarded 0–10 |
| Appearance selector | `0x20740` | i32, explicit choices only |

The surrounding currency/order blocks and appearance save/load anchors are documented in [save-layout.md](save-layout.md). **The new order labels are CT-derived, not independent gameplay-consumer verification.** Byte tests cover masked writes, PC/Switch CRC, rollback and undo; they do not prove in-game behavior. Requests, event payloads, typhoon state and other unknown order-block fields are not edited.

## Maximum soil

In **Soil editor**, choose a field/patch and click **Prepare maximum soil stats (raw)**. This stages maximum magnitudes, defense, health, base levels and XP/progress, with all three negative sign bits **cleared**, not maximized.

The existing **Apply changed fields to every used patch on this field** checkbox is retained. Unchecked affects one patch; checked affects all used patches on that field. The shortcut preserves this scope choice. Apply/export makes one undoable edit; crops, unused seasonal patches and unknown soil bits stay untouched.

These are **packed storage maxima**, not confirmed magnifying-glass/gameplay caps: health 255, defense 63, growth 127, yield 1023, quality/size 511, base levels 15 and progress 127. The game may clamp or reinterpret them. See [soil evidence](expanded-editors.md#2-soil-editor).

## Equipment shortcuts

Choose **Equipment shortcuts**. Read both previews and the warnings, acknowledge the experimental presets, then choose:

- **Give balanced staff gear** — INT-oriented staff set with elemental/status protection and utility inheritance.
- **Give maximum-damage staff gear** — more INT-focused attachments; **Strange Pendant ignores enemy DEF/M.DEF and your own DEF/M.DEF**. This is a deliberate survivability tradeoff, not a universally stronger set.

Both add **six level-10 items**: Sorcerer's Wand, Rune Shield, Four Dragons' Vest, Crown, Fairy Boots and Art of Magic. Total-level/rarity metadata is set to **150/200**. Existing worn gear and occupied inventory records are never overwritten. Allocation is conservatively restricted to six empty slots within the **first 15 bag slots**, avoiding unverified expansion-capacity assumptions. If there is no room, free slots in-game or with the item editor. No capacity/order flag is silently enabled. Equip the items in-game after export.

Valid pending edits and the grant apply together as one atomic undo entry. An invalid pending edit, missing reference table or full bag leaves all bytes/history/drafts intact. Consent resets after a successful grant or opening another save. Both Lest and Frey can receive the same set; gender, appearance, base stats, recipes and skills are unchanged.

### Source and deliberate adaptations

Read [wingblade98's “My take on the best equipment” and replies](https://gamefaqs.gamespot.com/boards/258612-rune-factory-4-special/80987735), supplied by the user. This is a **community theoretical build**, not executable evidence or a tested proof of an optimum. It supplies the INT/Gold Juice approach, four-core sets, Object X/Mealy Apple resistance approach, equipment bases and staff accessory/boot combinations. Replies dispute the status-resistance assumptions and discuss Magical Shield inheritance; we do **not** silently substitute that shield and lose Rune Shield's light/dark resistance.

- Staff craft attachments: **Dragon Fin ×3**. Upgrades: **Dragon Fin → 10-Fold Steel → Dragon Fin → Double Steel → Blue Scale → Yellow Feather → Wind Dragon Tooth → Dragon Bones → Rainbow Waterpot**. The final three preserve the established staff charge order; the supplied post itself did not remember that order.
- Each shield/armor/head/shoes/accessory contains all four different **Green/Red/Yellow/Blue Cores**.
- Fairy Boots carry **Rocket Wing, Strider Boots and Fast Step Boots** in the three craft slots.
- Balanced Art of Magic carries **Magic Ring, Fluffy Scarf and Hand-Knit Scarf**; damage replaces Hand-Knit Scarf with **Strange Pendant**.
- Balanced shield/head carry Object X and Mealy Apples; an additional Object X is placed **before** positive cloth/fins/cores rather than intentionally inverting their positive stats. Ancient Orc Cloth + 10-Fold Steel is on the head; Broken Box + 10-Fold Steel is on the boots. This adapts the post's protection ideas instead of copying its contradictory “inverted cloth” claim.
- The maximum-damage variant favors Dragon Fin crafting/steel combinations over Mealy Apples and cloth/box protection. Boot utility inheritance and four-core sets remain.

The previews list **every actual attachment and its order** in the selected Game names language. They are authoritative for what gets saved; the source post is not copied verbatim. Item/material IDs and base/upgrade/special-effect records are checked against the bundled catalog. See Venti's pinned `equipment_param.h` for Art of Magic, scarf, ring, boot and Strange Pendant meanings.

New grant records are initialized completely and carry the CT-described **crafted/homemade marker at item-relative `+2`**. This interpretation is CT-derived, not a separate gameplay replay. Per-material level/scaling information beyond the existing attachment representation is not invented.

### Required gameplay context / unverified effects

The source's resistance and INT targets assume **level-10 Gold Juice** and high resistance skills. The shortcut neither consumes/gives that food nor changes skills or saves temporary buffs. Do those in-game. Its claimed full immunity, the reply's 49% skill bonus, repeated-material penalties, material-level multipliers, Object X/steel interactions, special four-core behavior, boot/accessory inheritance and staff charge spells are **not fully simulated or gameplay-tested** here. No exact final-stat/immunity numbers are advertised.

This is a curated optimized preset, **not a mathematical maximum over all equipment, skills, buffs, enemies and upgrade combinations**. In particular, maximizing saved bonus metadata does not prove that this exact recipe could be crafted with those bonuses in-game. Keep an unedited backup and test exported copies.

## Verification

- `tests/order-soil-gear.test.js`: both platforms, exact packed conservation, both preset byte ranges/attachments, CRC/undo/redo, validation, missing tables/full bag, source-inspired sequence checks and mixed-batch rollback.
- `tests/test_order_soil_gear_ui.py`: real Qt controls, draft/consent lifecycle, localization/640×480 layout, pending-edit failures and separate system unlock.
- `scripts/desktop_smoke.py`: standalone catalog-backed grant previews, both grants, maximum soil and Extra Orders on synthetic saves only.
