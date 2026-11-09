import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemo, SaveDocument, INVENTORIES } from '../web/save-core.js';
import { ItemCatalog } from '../web/game-reference.js';
import { itemDetails, editInventoryItem, equipmentElement, planElement } from '../web/item-details.js';

function catalog() {
  const records = Array.from({ length: 1024 }, () => ({ category: 51, max_stack: 9 }));
  records[328] = { category: 15, max_stack: 1 }; records[559] = { category: 33, max_stack: 1 };
  records[777] = { category: 55, max_stack: 9 };
  return new ItemCatalog({ tables: { item: { count: 1024, records }, equipment: { count: 1024, records: Array.from({ length: 1024 }, () => ({ gear_params: 0 })) } } });
}

test('equipment attachments decode exact 10-bit groups and preserve every neighboring bit', () => {
  const save = createDemo(); const cat = catalog(); const offset = save.bagSlot(0).offset;
  save.transact('Seed unrelated metadata', bytes => { bytes.fill(0xff, offset + 2, offset + 28); bytes[offset + 4] = 0; });
  const before = save.data.slice();
  editInventoryItem(save, 'bag', 0, { id: 328, quantity: 1 }, cat.bagDefinition(328), cat, { inherited: 559, totalLevel: 150, rarityBonus: 200, craft0: 839, craft1: 862, craft2: 870, upgrade0: 872, upgrade8: 882 });
  const details = itemDetails(save, 'bag', 0);
  assert.equal(details.inherited, 559); assert.equal(details.rarityBonus, 200); assert.equal(details.totalLevel, 150);
  assert.deepEqual([details.craft0, details.craft1, details.craft2], [839, 862, 870]);
  assert.equal(details.upgrade0, 872); assert.equal(details.upgrade8, 882);
  assert.equal(details.upgrade1, 1023); assert.equal(save.bagSlot(0).level, 10);
  assert.equal(save.view().getUint32(offset + 8, true) & 0xfffc0000, before[offset + 10] << 16 & 0xfc0000 | before[offset + 11] << 24);
  for (const relative of [15, 19, 23, 27]) assert.equal(save.data[offset + relative] & 0xc0, before[offset + relative] & 0xc0);
  for (let index = 4; index < save.size; index++) if (index < offset || index >= offset + 28) assert.equal(save.data[index], before[index]);
  save.undo(); assert.deepEqual(save.data, before); save.redo(); assert.equal(new SaveDocument(save.build()).crcValid, true);
});

test('same transaction covers replacement, metadata and upgrade level in every container', () => {
  for (const container of Object.keys(INVENTORIES)) {
    const save = createDemo(); const cat = catalog(); const slot = INVENTORIES[container].slots - 1;
    editInventoryItem(save, container, slot, { id: 328, quantity: 1 }, cat.bagDefinition(328), cat, { craft1: 1023, upgrade2: 839 });
    assert.equal(save.undoStack.length, 1); assert.equal(save.inventorySlot(container, slot).level, 4);
    assert.equal(itemDetails(save, container, slot).craft1, 1023);
    const exported = new SaveDocument(save.build({ platform: 'switch', experimental: true }));
    assert.equal(exported.crcValid, true); assert.equal(itemDetails(exported, container, slot).upgrade2, 839);
    save.undo(); assert.deepEqual(save.data, save.original);
  }
});

test('invalid attachment ranges and stacked items fail atomically and retain redo', () => {
  const save = createDemo(); const cat = catalog(); save.setPlayer({ money: 400 }); save.undo();
  for (const changes of [{ inherited: 839 }, { craft0: 1024 }, { craft1: 777 }, { upgrade0: -1 }, { totalLevel: 151 }, { rarityBonus: 201 }, { unknown: 0 }, { craft0: '' }]) {
    assert.throws(() => editInventoryItem(save, 'bag', 0, { id: 328, quantity: 1 }, cat.bagDefinition(328), cat, changes));
    assert.deepEqual(save.data, save.original); assert.equal(save.redoStack.length, 1);
  }
  assert.throws(() => editInventoryItem(save, 'bag', 0, { id: 839, quantity: 1 }, cat.bagDefinition(839), cat, { craft0: 872 }), /nonstackable/);
  assert.deepEqual(save.data, save.original);
});

test('element changes follow game crystal toggles without deleting existing attachments', () => {
  const save = createDemo(); const cat = catalog();
  cat.local.tables.equipment.records[328].gear_params = 2;
  editInventoryItem(save, 'bag', 0, { id: 328, quantity: 1 }, cat.bagDefinition(328), cat, { craft0: 839, upgrade0: 862, element: 1 });
  let details = itemDetails(save, 'bag', 0);
  assert.equal(details.craft0, 839); assert.equal(details.upgrade0, 862);
  assert.equal(details.upgrade1, 872); assert.equal(details.upgrade2, 872);
  assert.equal(save.bagSlot(0).level, 4); assert.equal(equipmentElement(328, details, cat), 1);
  editInventoryItem(save, 'bag', 0, { id: 328, quantity: 1 }, cat.bagDefinition(328), cat, { element: 0 });
  details = itemDetails(save, 'bag', 0); assert.equal(details.upgrade3, 870); assert.equal(equipmentElement(328, details, cat), 0);
  assert.throws(() => planElement(328, details, 10, 4, cat), /unused upgrade slots/);
  assert.equal(equipmentElement(328, { ...details, headerFlag: true }, cat), null);
  assert.throws(() => planElement(328, { ...details, headerFlag: true }, 4, 2, cat), /recognized element/);
});
