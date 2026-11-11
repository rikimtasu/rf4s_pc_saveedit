# Read-only item-effect preview

In native **Bag & storage**, select an item and open **Item effect preview**. Compare the **Current item** and **Draft result** tabs before applying an edit. The preview does not modify source bytes, undo/redo, game files or the user's original save. Invalid drafts report a preview error rather than applying a partial edit.

## Preview contents

- Base equipment ATK/M.ATK/DEF/M.DEF and other nonzero parameter values, status/resistance percentages and named abilities.
- Inherited-equipment parameters as a separate reference; the preview does not merge them into final stats.
- Each crafting/upgrade material's raw strengthening bonuses and its saved slot.
- The planned weapon/tool element, using the crystal transition algorithm in `web/item-details.js`.
- Non-equipment base use effects and raw material bonuses, including healing, status cure/infliction, permanent stat gains and effect duration.

Missing tables/records remain unavailable, not zero. Unknown bitmasks are shown explicitly. A named flag is a source interpretation, not independent verification of every engine consumer. The panels remain **definition-based, not final in-game stats**.

## Primary definitions and units

`web/item-effects.js` creates a separate `SaveDocument`, runs the same `editInventoryItem` operation as Apply, and inspects that copy.

| Table | Primary source | Interpretation |
| --- | --- | --- |
| `rf3ItemEquipmentParam.bin` | [`EquipmentParam`](../vendor/venti/src/rf/equipment_param.h), comments/fields at lines 151–305 | Flat stat integers; percentage fields use 4096 = 100%; equipment/boot/accessory bitflags follow the source enums. `depth` is ambiguous and is omitted, as is model ID. |
| `rf3ItemStrengthening.bin` | [`Upgrade`](../vendor/venti/src/rf/upgrade.h) | Individual raw material stat bonuses; percentage fields use 4096 = 100%. Unused fields are omitted. |
| `rf3UseItemParam.bin` | [`ItemUseParam`](../vendor/venti/src/rf/item_use_param.h) | Percentage fields use 4096 = 100%; duration unit is 3 in-game minutes. `level_scaling` is shown as its own reference coefficient (4096 = 12.5%), not applied as a final multiplier. |

The portable app bundles the required tables. For overrides, read tables from your game with [`GameSource`](../scripts/game_sources.py) or import extracted definitions using the bounded NLCL table readers. No personal tables are added to public builds. The checked source offsets/types are compiled into [`web/game-schema.js`](../web/game-schema.js).

## Calculations not included

The preview does not simulate material-level scaling, repeat-material penalties, total-level and rarity bonuses, special material multipliers, complex inheritance/accessory combinations, staff charge effects or actor-adjusted final stats. It does not sum raw material bonuses into a final total. Editing an item level changes the displayed saved level without calculating scaled final stats.

`tests/item-effects.test.js` covers percentage/duration decoding, unknown masks, actual draft element/level planning, missing references, invalid edits and source/history immutability. Native adapter and GUI smoke tests cover marshaling, read-only current/draft panels and language-switch draft preservation. In-game acceptance still requires testing an exported copy.
