import { integer, bagStackLimit } from './save-core.js';

export const EQUIPMENT_CATEGORIES = [15, 16, 17, 18, 19, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37];
export const ELEMENTS = [
  { value: 0, name: 'Non-elemental', crystal: 0 },
  { value: 1, name: 'Fire', crystal: 872 }, { value: 2, name: 'Water', crystal: 870 },
  { value: 4, name: 'Earth', crystal: 839 }, { value: 8, name: 'Wind', crystal: 862 },
  { value: 16, name: 'Light', crystal: 880 }, { value: 32, name: 'Dark', crystal: 881 },
  { value: 64, name: 'Love', crystal: 882 },
];
const fields = [
  ['inherited', 8, 0, 10], ['rarityBonus', 8, 10, 8], ['totalLevel', 6, 0, 8],
  ...Array.from({ length: 3 }, (_, i) => [`craft${i}`, 12, i * 10, 10]),
  ...Array.from({ length: 9 }, (_, i) => [`upgrade${i}`, 16 + Math.floor(i / 3) * 4, i % 3 * 10, 10]),
];

export function equipmentItem(definition) { return Boolean(definition && EQUIPMENT_CATEGORIES.includes(definition.category) && bagStackLimit(definition) === 1); }
export function itemDetails(save, container, slot, bytes = save.data) {
  const item = save.inventorySlot(container, slot, bytes);
  const view = save.view(bytes);
  return { ...Object.fromEntries(fields.map(([key, offset, shift, width]) => [key, width === 8 && key === 'totalLevel' ? bytes[item.offset + offset] : (view.getUint32(item.offset + offset, true) >>> shift) & (2 ** width - 1)])), headerFlag: item.headerFlag };
}

function validateAttached(catalog, id, inherited = false) {
  integer(id, 0, 1023, 'Attached item ID (10-bit field)');
  if (!id) return;
  const definition = catalog.bagDefinition(id);
  if (definition.category === 55) throw new Error('Category placeholders cannot be attached.');
  if (inherited && !equipmentItem(definition)) throw new Error('Inherited abilities require an equipment item.');
}

export function crystalElement(current, crystal) {
  const target = ELEMENTS.find(element => element.crystal === crystal && crystal);
  if (!target) return current;
  return current & (127 ^ target.value) ? current & target.value : current | target.value;
}

export function equipmentElement(id, details, catalog) {
  const definition = catalog.bagDefinition(id);
  if (!equipmentItem(definition) || !(definition.category <= 32) || details.headerFlag) return null;
  const base = catalog.record('equipment', details.inherited || id);
  if (!base) return null;
  let value = base.gear_params & 127;
  for (const key of [...Array.from({ length: 3 }, (_, i) => `craft${i}`), ...Array.from({ length: 9 }, (_, i) => `upgrade${i}`)]) value = crystalElement(value, details[key]);
  return value;
}

export function planElement(id, details, level, targetInput, catalog) {
  const target = integer(targetInput, 0, 64, 'Element');
  if (!ELEMENTS.some(element => element.value === target)) throw new Error('Choose a known element.');
  let current = equipmentElement(id, details, catalog);
  if (current === null || !ELEMENTS.some(element => element.value === current)) throw new Error('Read equipment definitions and choose a weapon/tool with one recognized element.');
  const next = { ...details };
  let used = Math.max(integer(level, 1, 10, 'Item level') - 1, ...Array.from({ length: 9 }, (_, i) => next[`upgrade${i}`] ? i + 1 : 0));
  while (current !== target) {
    if (used >= 9) throw new Error('Not enough unused upgrade slots to change element without removing attachments.');
    const crystal = target ? ELEMENTS.find(element => element.value === target).crystal : current === 1 ? 870 : 872;
    validateAttached(catalog, crystal);
    next[`upgrade${used++}`] = crystal;
    current = crystalElement(current, crystal);
  }
  return { details: next, level: Math.max(level, used + 1) };
}

export function editInventoryItem(save, container, slot, changes, definition, catalog, detailChanges = {}) {
  const current = save.inventorySlot(container, slot);
  const details = current.id === changes.id ? itemDetails(save, container, slot) : Object.fromEntries(fields.map(([key]) => [key, 0]));
  if (Object.keys(detailChanges).length && !equipmentItem(definition)) throw new Error('Attachments are only editable on nonstackable equipment, not stacked items.');
  for (const [key, input] of Object.entries(detailChanges)) {
    if (key === 'element') continue;
    const field = fields.find(([name]) => name === key);
    if (!field) throw new Error('Unknown equipment detail.');
    const value = integer(input, 0, key === 'totalLevel' ? 150 : key === 'rarityBonus' ? 200 : 1023, key);
    if (key === 'inherited' || /^(craft|upgrade)/.test(key)) validateAttached(catalog, value, key === 'inherited');
    details[key] = value;
  }
  let level = changes.level ?? (changes.id === current.id ? current.level : 1);
  const hasUpgrades = Object.keys(detailChanges).some(key => key.startsWith('upgrade'));
  if (hasUpgrades) level = Math.max(level, ...Array.from({ length: 9 }, (_, i) => details[`upgrade${i}`] ? i + 2 : 1));
  if (detailChanges.element !== undefined) {
    const planned = planElement(changes.id, details, level, detailChanges.element, catalog);
    Object.assign(details, planned.details); level = planned.level;
  }
  const updateLevel = hasUpgrades || detailChanges.element !== undefined;
  return save.transact(`Item and attachments · ${container} slot ${Number(slot) + 1}`, bytes => {
    const staged = Object.create(save);
    staged.data = bytes;
    staged.transact = (_label, mutate) => { mutate(bytes); return true; };
    staged.setInventoryItem(container, slot, { ...changes, ...(updateLevel ? { level } : {}) }, definition);
    if (!Object.keys(detailChanges).length) return;
    const view = staged.view(bytes);
    for (const [key, relative, shift, width] of fields) {
      if (detailChanges[key] === undefined && !(key.startsWith('upgrade') && detailChanges.element !== undefined)) continue;
      const offset = current.offset + relative;
      if (key === 'totalLevel') { bytes[offset] = details[key]; continue; }
      const mask = ((2 ** width - 1) << shift) >>> 0;
      view.setUint32(offset, ((view.getUint32(offset, true) & ~mask) | (details[key] << shift)) >>> 0, true);
    }
  });
}
