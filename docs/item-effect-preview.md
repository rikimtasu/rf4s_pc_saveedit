# Read-only item-effect preview

The native inventory page compares the current item with its draft. `web/item-effects.js` creates a separate `SaveDocument`, runs the same `editInventoryItem` operation as Apply, and inspects that copy. It does not modify source bytes, undo/redo, game files or the user's original save. Invalid drafts report a preview error rather than applying a partial edit.

## What is shown

- Base equipment ATK/M.ATK/DEF/M.DEF and other nonzero parameter values, status/resistance percentages and named abilities.
- Inherited-equipment parameters **as a separate reference**, not an invented merged final result.
- Each crafting/upgrade material's raw strengthening bonuses and its saved slot.
- The planned weapon/tool element, following the already-audited crystal transition algorithm in `web/item-details.js`.
- Non-equipment base use effects and raw material bonuses, including healing, status cure/infliction, permanent stat gains and effect duration.

Missing tables/records remain unavailable, not zero. Unknown bitmasks are shown explicitly. A named flag is a source interpretation, not independent verification of every engine consumer. The panels remain **definition-based, not final in-game stats**.

## Primary definitions and units

| Table | Primary source | Interpretation |
| --- | --- | --- |
| `rf3ItemEquipmentParam.bin` | [`EquipmentParam`](../vendor/venti/src/rf/equipment_param.h), comments/fields at lines 151–305 | Flat stat integers; percentage fields use 4096 = 100%; equipment/boot/accessory bitflags follow the source enums. `depth` is ambiguous and is omitted, as is model ID. |
| `rf3ItemStrengthening.bin` | [`Upgrade`](../vendor/venti/src/rf/upgrade.h) | Individual raw material stat bonuses; percentage fields use 4096 = 100%. Unused fields are omitted. |
| `rf3UseItemParam.bin` | [`ItemUseParam`](../vendor/venti/src/rf/item_use_param.h) | Percentage fields use 4096 = 100%; duration unit is 3 in-game minutes. `level_scaling` is shown as its own reference coefficient (4096 = 12.5%), not applied as a final multiplier. |

Tables are read from the user's game with [`GameSource`](../scripts/game_sources.py) or imported as extracted definitions using the existing bounded NLCL readers. No personal tables are added to public builds. The checked source offsets/types are compiled into [`web/game-schema.js`](../web/game-schema.js).

## Deliberately not calculated

Material-level scaling, repeat-material penalties, total-level and rarity bonuses, special material multipliers, complex inheritance/accessory combinations, staff charge effects and actor-adjusted final stats are not simulated. Raw material bonuses are not summed into a misleading “exact” total. Editing an item level therefore changes the displayed saved level but does not fabricate scaled final numbers.

`tests/item-effects.test.js` covers percentage/duration decoding, unknown masks, actual draft element/level planning, missing references, invalid edits and source/history immutability. Native adapter and GUI smoke tests cover marshaling, read-only current/draft panels and language-switch draft preservation. In-game acceptance still requires testing an exported copy.
