import { VENTI_TABLES, ITEM_NAMES } from './game-schema.js';
import { integer } from './save-core.js';

export { ITEM_NAMES };
export const ITEM_TABLE_TYPES = ['item', 'equipment', 'use', 'upgrade'];
export const ITEM_CATEGORIES = VENTI_TABLES.item.fields.category.enum;
export const ITEM_FLAGS = VENTI_TABLES.item.fields.flags.enum;
export const ITEM_GROUPS = [
  { id: 'produce', label: 'Produce and plants', categories: [0, 1, 2] },
  { id: 'seeds', label: 'Seeds', categories: [46] },
  { id: 'food', label: 'Food and ingredients', categories: [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14] },
  { id: 'medicine', label: 'Medicine', categories: [3] },
  { id: 'weapons', label: 'Weapons', categories: [15, 16, 17, 18, 19, 24, 25, 26] },
  { id: 'tools', label: 'Farm tools', categories: [27, 28, 29, 30, 31, 32, 40, 41, 45] },
  { id: 'equipment', label: 'Armor and accessories', categories: [33, 34, 35, 36, 37] },
  { id: 'materials', label: 'Crafting materials', categories: [51, 54] },
  { id: 'fish', label: 'Fish', categories: [52] },
  { id: 'supplies', label: 'Farming supplies', categories: [47] },
  { id: 'spells', label: 'Spells and abilities', categories: [48, 49, 50] },
  { id: 'bread', label: 'Recipe bread', categories: [57] },
  { id: 'other', label: 'Other items', categories: [] },
];

export function itemGroup(category) {
  return ITEM_GROUPS.find(group => group.categories.includes(category)) || ITEM_GROUPS.at(-1);
}

export function detectItemTable(filename) {
  const name = filename.split(/[\\/]/).pop().toLowerCase();
  for (const type of ITEM_TABLE_TYPES) {
    if (VENTI_TABLES[type].variants[0].file.toLowerCase() === name) return type;
  }
  throw new Error('Choose an extracted item, equipment, item-use or strengthening table.');
}

export class ItemTable {
  constructor(input, type) {
    if (!ITEM_TABLE_TYPES.includes(type)) throw new Error('Unsupported item reference table.');
    this.type = type;
    this.schema = VENTI_TABLES[type];
    this.bytes = new Uint8Array(input).slice();
    this.view = new DataView(this.bytes.buffer);
    const size = this.bytes.length;
    if (size < 28 || size > 16 * 1024 * 1024 || String.fromCharCode(...this.bytes.slice(0, 4)) !== 'NLCL') throw new Error('Expected an extracted NLCL item-reference table.');
    this.count = this.view.getUint32(24, true);
    const end = this.view.getUint32(20, true);
    if (this.view.getUint32(16, true) !== 1 || 28 + this.count * this.schema.size !== end || end > size) throw new Error('Reference table layout does not match its Venti definition.');
    this.filename = this.schema.variants[0].file;
  }

  record(idInput) {
    const id = integer(idInput, 0, this.count - 1, 'Reference item index');
    return Object.fromEntries(Object.entries(this.schema.fields).map(([name, spec]) => {
      const getter = `get${spec.signed ? 'Int' : 'Uint'}${spec.bits}`;
      const offset = 28 + id * this.schema.size + spec.offset;
      const value = this.view[getter](offset, true);
      return [name, spec.shift === undefined ? value : (value >>> spec.shift) & 15];
    }));
  }
}

export class ItemCatalog {
  constructor(local = null) {
    this.tables = new Map();
    this.local = local;
    this.itemIndex = null;
  }

  add(table) {
    if (!(table instanceof ItemTable)) throw new Error('Expected an item reference table.');
    this.tables.set(table.type, table);
    this.itemIndex = null;
  }

  count(type) { return this.tables.get(type)?.count ?? this.local?.tables?.[type]?.count; }

  record(type, idInput) {
    if (!ITEM_TABLE_TYPES.includes(type)) throw new Error('Unknown reference table.');
    const id = integer(idInput, 0, 0xffffffff, 'Item ID');
    if (this.tables.has(type)) return this.tables.get(type).record(id);
    const table = this.local?.tables?.[type];
    if (!table) return null;
    integer(id, 0, table.count - 1, 'Reference item index');
    return table.records[id];
  }

  name(id) { return ITEM_NAMES[id] || `Unknown item ${id}`; }

  browse({ query = '', group = 'all', editableOnly = false } = {}) {
    if (group !== 'all' && !ITEM_GROUPS.some(entry => entry.id === group)) throw new Error('Unknown item group.');
    if (!this.itemIndex) {
      const count = this.count('item');
      const ids = count === undefined ? Object.keys(ITEM_NAMES).map(Number).filter(id => id > 0 && id <= 0x7ff) : Array.from({ length: Math.max(0, Math.min(count, 2048) - 1) }, (_, index) => index + 1);
      this.itemIndex = ids.map(id => {
        const record = this.record('item', id);
        return Object.freeze({ id, name: this.name(id), category: record?.category ?? null, group: itemGroup(record?.category).id, editable: Boolean(record && record.category !== 55) });
      }).sort((a, b) => a.name.localeCompare(b.name, 'en') || a.id - b.id);
    }
    const text = String(query).trim().toLowerCase();
    return this.itemIndex.filter(item => (!editableOnly || item.editable) && (group === 'all' || item.group === group) && (!text || `${item.id} ${item.name}`.toLowerCase().includes(text)));
  }

  groups({ editableOnly = false } = {}) {
    const items = this.browse({ editableOnly });
    return ITEM_GROUPS.map(group => ({ id: group.id, label: group.label, count: items.filter(item => item.group === group.id).length })).filter(group => group.count > 0);
  }

  validateItem(id) {
    const count = this.count('item');
    return integer(id, 0, count === undefined ? 0xffffffff : count - 1, 'Item ID');
  }

  bagDefinition(idInput) {
    const id = integer(idInput, 0, 0x7ff, 'Item ID');
    if (!id) return null;
    const definition = this.record('item', id);
    if (!definition) throw new Error('Read the item definition table before editing bag items.');
    return definition;
  }
}

export function categoryName(value) {
  return Object.keys(ITEM_CATEGORIES).find(name => ITEM_CATEGORIES[name] === value) || `Unknown category ${value}`;
}

export function decodeItemFlags(value) {
  const bits = integer(value, 0, 0xffffffff, 'Item flags');
  const flags = Object.entries(ITEM_FLAGS).filter(([, mask]) => mask > 0 && (bits & mask) === mask).map(([name]) => name);
  const knownMask = Object.values(ITEM_FLAGS).reduce((mask, bit) => (mask | bit) >>> 0, 0);
  const unknown = (bits & ~knownMask) >>> 0;
  if (unknown) flags.push(`Unknown bits 0x${unknown.toString(16).toUpperCase()}`);
  return flags.length ? flags.join(' | ') : 'None';
}

export function semanticValue(input, meaning) {
  const dictionary = meaning === 'category' ? ITEM_CATEGORIES : meaning === 'flags' ? ITEM_FLAGS : null;
  if (!dictionary || typeof input !== 'string' || /^\s*(?:0x[\da-f]+|\d+)\s*$/i.test(input)) return input;
  const names = input.split('|').map(name => name.trim());
  if (meaning === 'category' && names.length !== 1) throw new Error('Choose one item category.');
  let value = 0;
  for (const name of names) {
    if (!Object.hasOwn(dictionary, name)) throw new Error(`Unknown ${meaning}: ${name}.`);
    value = Number(BigInt(value) | BigInt(dictionary[name]));
  }
  return value;
}
