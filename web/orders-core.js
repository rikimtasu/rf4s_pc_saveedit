// CT v12.3 RF4D+2A774..2A798 and v13 ExpGainPtr cross-check.
// The persisted order block is save+2071C. Separate named GameFlags use the
// developer's full-width MSB-first encoding, NOT CT's numeric bit interpretation.
import { integer, writeFlag } from './save-core.js';
import { SAVE_METADATA } from './save-metadata.js';

export const ORDER_GROUPS = [
  { id: 'effects', name: 'Order effects' }, { id: 'licenses', name: 'Licenses' },
  { id: 'shops', name: 'Shops & services' }, { id: 'expansions', name: 'Storage & fields' },
  { id: 'other', name: 'Other saved orders' },
];
function named(key, label, symbol, group = 'other') {
  const flag = SAVE_METADATA.symbols.find(field => field.name === symbol);
  if (!flag) throw new Error('Missing developer order symbol.');
  return { key, label, flag: { name: flag.name, bitOffset: flag.bitOffset, width: flag.width }, group, min: 0, max: 2 ** flag.width - 1 };
}
const packed = (key, label, offset, bit, group) => ({ key, label, offset, bit, width: 1, group, min: 0, max: 1 });

// Order IDs 58..63 write REG_BGM_TYPE = order ID - 58 (PC 1EA934).
export const ORDER_BGM = ['Rune Factory 4', 'Rune Factory 1', 'Rune Factory 2', 'Rune Factory 3', 'Rune Factory Frontier', 'Rune Factory: Tides of Destiny'].map((name, id) => ({ id, name }));
// PC 1EA7D2..1EA855 writes the caller ID to runtime E9AC20 -> save 20728.
export const MORNING_CALLERS = [
  { id: 0, name: 'Cancel morning call' },
  ...[1, 2, 3, 6, 12, 14, 18, 19].map(id => ({ id })),
  { id: 309, name: 'Pico' },
];

export const ORDER_FIELDS = [
  { key: 'enemyLevel', label: 'Enemy level increase (0–10)', offset: 0x2072c, min: 0, max: 10 },
  { key: 'noExp', label: 'Disable combat EXP', offset: 0x2071f, bit: 3 },
  { key: 'noSkillExp', label: 'Disable skill EXP', offset: 0x2071f, bit: 4 },
  { key: 'noTownEvents', label: 'Disable town events', offset: 0x2071e, bit: 5 },
  { key: 'showEnemyLevel', label: 'Show enemy levels', offset: 0x2071f, bit: 5 },
  { key: 'showEnemyHp', label: 'Show enemy HP', offset: 0x2071f, bit: 6 },
  { key: 'appearance', label: 'Appearance order (reload required)', offset: 0x20740, type: 'i32', min: 0, max: 9999 },
  ...[
    ['forgeLicense', 'Forging license', 0x2071c, 0],
    ['chemistryLicense', 'Chemistry license', 0x2071c, 1],
    ['craftingLicense', 'Crafting license', 0x2071c, 2],
    ['basicCookingLicense', 'Basic cooking license', 0x2071c, 3],
    ['proCookingLicense', 'Pro cooking license', 0x2071c, 4],
    ['businessLicense', 'Business license', 0x2071e, 3],
    ['airshipLicense', 'Airship license', 0x20738, 0],
  ].map(args => packed(...args, 'licenses')),
  ...[
    ['blossomFurniture', 'Blossom furniture stock', 0x2071c, 6],
    ['flowerShopStock', 'Flower shop stock expansion', 0x2071c, 7],
    ['furnitureShop', 'Furniture shop', 0x2071d, 2],
    ['blossomGroceries', 'Blossom grocery stock', 0x2071d, 3],
    ['badoAccessories', 'Bado accessory stock', 0x2071d, 4],
    ['badoBargains', 'Bado bargain stock', 0x2071d, 5],
    ['clothingShop', 'Clothing shop', 0x2071d, 6],
    ['fishMarket', 'Fish market', 0x2071d, 7],
    ['jewelryShop', 'Jewelry shop', 0x2071e, 0],
    ['magicShop', 'Magic shop', 0x2071e, 1],
    ['runeAbilityShop', 'Rune ability shop', 0x2071e, 2],
    ['nationalizeBaths', 'Nationalize baths (free baths)', 0x2071e, 6],
  ].map(args => packed(...args, 'shops')),
  packed('expandedCookingTools', 'Expanded cooking tools flag (no furniture delivered)', 0x2071e, 7, 'other'),
  { key: 'princeRank', label: 'Prince / princess rank (raw 0–31)', offset: 0x20718, bit: 0, width: 5, min: 0, max: 31, group: 'other' },
  named('bagExpansion', 'Bag expansion level (raw 0–3)', 'REG_STORAGE_RUCK_LV', 'expansions'),
  named('fridgeExpansion', 'Fridge expansion level (raw 0–7)', 'REG_STORAGE_REFRIGERATOR_LV', 'expansions'),
  named('storageExpansion', 'Storage expansion level (raw 0–7)', 'REG_STORAGE_LV', 'expansions'),
  named('bookshelfExpansion', 'Bookshelf expansion level (raw 0–3)', 'REG_STORAGE_BOOK_LV', 'expansions'),
  named('weaponBoxExpansion', 'Weapon box expansion level (raw 0–3)', 'REG_STORAGE_WEAPON_LV', 'expansions'),
  named('armorBoxExpansion', 'Armor box expansion level (raw 0–3)', 'REG_STORAGE_CLOTH_LV', 'expansions'),
  named('toolStorageExpansion', 'Tool storage expansion level (raw 0–3)', 'REG_STORAGE_FARM_LV', 'expansions'),
  named('shippingBoxExpansion', 'Shipping box expansion level (raw 0–3)', 'REG_STORAGE_SHIPMENT_LV', 'expansions'),
  named('fieldExpansion', 'Home field expansion level (raw 0–7)', 'REG_FARM_LV', 'expansions'),
  named('bag60Order', '60-slot bag expansion order unlocked', 'FLG_ORDER_RUCK_SIZE_60', 'expansions'),
  named('morningCallOrder', 'Morning-call menu unlocked (global)', 'FLG_MORNING_CALL_ORDER'),
  { key: 'morningCaller', label: 'Morning-call NPC', offset: 0x20728, type: 'i32', min: 0, max: 309, group: 'other' },
  named('sharanceMaze', 'Sharance Maze enabled', 'FLG_SHIA_DUNG'),
  named('everyoneSwimsuits', 'Everyone wears swimsuits order', 'FLG_MIZUGI_FES'),
  named('hideInnShopkeeper', 'Hide inn NPC shopkeeper order', 'FLG_ORDER_SHOP_MOB_OFF'),
  named('bgm', 'BGM selection', 'REG_BGM_TYPE'),
].map(field => ({ group: 'effects', min: 0, max: field.bit === undefined ? undefined : 1, ...field,
  kind: ['appearance', 'bgm', 'morningCaller'].includes(field.key) ? 'choice' : (field.flag?.width ?? (field.bit === undefined ? 0 : field.width || 1)) === 1 ? 'bool' : 'number' }));
export const ORDER_APPEARANCES = [
  { id: 0, name: 'Default main character' }, { id: 9999, name: 'Opposite-gender appearance (dialogue unchanged)' },
  ...Array.from({ length: 20 }, (_, i) => ({ id: i + 1 })),
  ...[24, 25, 27, 28, 34, 35, 239, 309].map(id => ({ id })),
];

export class OrdersEditor {
  constructor(document) { this.document = document; }
  values() {
    this.document.requireSlot();
    return Object.fromEntries(ORDER_FIELDS.map(field => {
      if (field.flag) return [field.key, this.document.flag(field.flag)];
      const raw = this.document.readNumber(field.offset, field.type || 'u8');
      return [field.key, field.bit === undefined ? raw : (raw >> field.bit) & (2 ** (field.width || 1) - 1)];
    }));
  }
  apply(changes) {
    this.document.requireSlot();
    const fields = Object.entries(changes).map(([key, input]) => {
      const field = ORDER_FIELDS.find(entry => entry.key === key);
      if (!field) throw new Error('Unknown extra order field.');
      const value = integer(input, field.min || 0, field.max === undefined ? 1 : field.max, field.label);
      if (key === 'appearance' && !ORDER_APPEARANCES.some(entry => entry.id === value)) throw new Error('Choose a supported appearance order.');
      if (key === 'morningCaller' && !MORNING_CALLERS.some(entry => entry.id === value)) throw new Error('Choose a supported morning-call NPC.');
      return { ...field, value };
    });
    return this.document.transact('Extra orders', bytes => {
      for (const field of fields) {
        if (field.flag) writeFlag(bytes, field.flag, field.value);
        else if (field.bit !== undefined) {
          const mask = (2 ** (field.width || 1) - 1) << field.bit;
          bytes[field.offset] = (bytes[field.offset] & ~mask) | (field.value << field.bit);
        } else this.document.view(bytes)[field.type === 'i32' ? 'setInt32' : 'setUint8'](field.offset, field.value, true);
      }
    });
  }
}
