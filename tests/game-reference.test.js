import test from 'node:test';
import assert from 'node:assert/strict';
import { ItemTable, ItemCatalog, detectItemTable, categoryName, decodeItemFlags, semanticValue } from '../web/game-reference.js';
import { VENTI_TABLES } from '../web/game-schema.js';
import { SaveDocument, createDemo, NUMBER_TYPES, SAVE_SIZE } from '../web/save-core.js';

function tableFixture(type, count = 3) {
  const schema = VENTI_TABLES[type];
  const end = 28 + count * schema.size;
  const bytes = new Uint8Array(end + 16);
  bytes.set(new TextEncoder().encode('NLCL'));
  const view = new DataView(bytes.buffer);
  view.setUint32(16, 1, true);
  view.setUint32(20, end, true);
  view.setUint32(24, count, true);
  return bytes;
}

test('reference reader only accepts the four item-related table filenames', () => {
  assert.equal(detectItemTable('rf3ItemList.bin'), 'item');
  assert.equal(detectItemTable('RF3ITEMEQUIPMENTPARAM.BIN'), 'equipment');
  assert.equal(detectItemTable('rf3UseItemParam.bin'), 'use');
  assert.equal(detectItemTable('rf3ItemStrengthening.bin'), 'upgrade');
  assert.throws(() => detectItemTable('rf4_s00.sav'));
  assert.throws(() => detectItemTable('rf3NpcParam.bin'));
});

test('reference reader decodes prices and packed nibbles without writes', () => {
  const bytes = tableFixture('item');
  new DataView(bytes.buffer).setUint32(28 + 40 + 8, 2000, true);
  bytes[28 + 40 + 5] = 0xc9;
  const original = bytes.slice();
  const table = new ItemTable(bytes, 'item');
  const record = table.record(1);
  assert.equal(record.buy, 2000);
  assert.equal(record.rarity, 12);
  assert.equal(record.max_stack, 9);
  assert.deepEqual(table.bytes, original);
  assert.deepEqual(bytes, original);
  assert.throws(() => table.record(3));
});

test('reference reader supports signed equipment fields and rejects bad bounds', () => {
  const bytes = tableFixture('equipment');
  new DataView(bytes.buffer).setInt32(28 + VENTI_TABLES.equipment.fields.attack.offset, -10, true);
  assert.equal(new ItemTable(bytes, 'equipment').record(0).attack, -10);
  const malformed = tableFixture('item');
  new DataView(malformed.buffer).setUint32(24, 500, true);
  assert.throws(() => new ItemTable(malformed, 'item'));
  assert.throws(() => new ItemTable(new Uint8Array(100), 'item'));
  assert.throws(() => new ItemTable(bytes, 'npc'));
});

test('catalog uses local data, then explicit imported table references', () => {
  const catalog = new ItemCatalog({ tables: { item: { count: 2, records: [{ buy: 0 }, { buy: 400, category: 15 }] } } });
  assert.equal(catalog.name(1), 'Cabbage');
  assert.equal(catalog.record('item', 1).buy, 400);
  assert.equal(catalog.record('equipment', 1), null);
  assert.throws(() => catalog.validateItem(2));
  assert.deepEqual(catalog.browse({ group: 'weapons', editableOnly: true }).map(item => item.id), [1]);
  const table = new ItemTable(tableFixture('item', 3), 'item');
  catalog.add(table);
  assert.equal(catalog.count('item'), 3);
  assert.equal(catalog.record('item', 1).buy, 0);
  assert.equal(catalog.validateItem(2), 2);
  assert.equal(catalog.browse({ group: 'weapons', editableOnly: true }).length, 0);
  assert.deepEqual(catalog.browse({ group: 'produce', editableOnly: true }).map(item => item.id), [1, 2]);
});

test('categories and item flags are reference definitions, with unknown bits retained', () => {
  assert.equal(categoryName(0), 'Vegetable');
  assert.equal(semanticValue('Vegetable', 'category'), 0);
  assert.equal(semanticValue('Giant | KeyItem', 'flags'), 10);
  assert.equal(decodeItemFlags(10), 'KeyItem | Giant');
  assert.match(decodeItemFlags(0x80000000), /Unknown bits 0x80000000/);
  assert.throws(() => semanticValue('Vegetable | Fruit', 'category'));
  assert.throws(() => semanticValue('MadeUpFlag', 'flags'));
});

test('typed save edits write every integer width little-endian and share undo', () => {
  for (const [type, spec] of Object.entries(NUMBER_TYPES)) {
    const save = createDemo();
    const offset = 0x100;
    save.setNumber(offset, type, spec.max);
    assert.equal(save.readNumber(offset, type), spec.max);
    assert.equal(save.undoStack.length, 1);
    const exported = new SaveDocument(save.build());
    assert.equal(exported.readNumber(offset, type), spec.max);
    assert.equal(exported.crcValid, true);
    assert.equal(save.data[offset], type.startsWith('u') ? 255 : spec.bytes === 1 ? 127 : 255);
    save.undo();
    assert.equal(save.readNumber(offset, type), 0);
    save.redo();
    assert.equal(save.readNumber(offset, type), spec.max);
  }
});

test('typed save edits reject overflow, header writes, missing offsets and file overruns', () => {
  const save = createDemo();
  const before = save.data.slice();
  for (const [offset, type, value] of [[0, 'u32', 1], [3, 'u8', 1], ['', 'u16', 1], [SAVE_SIZE - 1, 'u16', 1], [100, 'u16', 65536], [100, 'i16', -32769], [100, 'u32', -1], [100, 'u8', 1.5], [100, '__proto__', 0]]) assert.throws(() => save.setNumber(offset, type, value));
  assert.deepEqual(save.data, before);
  assert.equal(save.undoStack.length, 0);
});

test('reference lookup alone cannot modify or locate anything in a save', () => {
  const save = createDemo();
  const before = save.data.slice();
  const catalog = new ItemCatalog();
  catalog.add(new ItemTable(tableFixture('item'), 'item'));
  catalog.name(1);
  catalog.record('item', 1);
  categoryName(0);
  decodeItemFlags(1);
  assert.deepEqual(save.data, before);
  assert.equal(save.dirty, false);
});
