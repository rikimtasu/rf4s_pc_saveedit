import test from 'node:test';
import assert from 'node:assert/strict';
import { SaveDocument, createDemo, PLAYER_FIELDS, BAG_OFFSET, BAG_SLOTS, ITEM_RECORD_SIZE, CRC_START, CRC_END, crc32, bagStackLimit } from '../web/save-core.js';
import { ItemCatalog } from '../web/game-reference.js';

const stackable = { category: 24, max_stack: 9 };
const equipment = { category: 11, max_stack: 0 };

function signedFixture() {
  const bytes = createDemo().original.slice();
  for (const [index, name] of ['strength', 'intelligence', 'vitality'].entries()) bytes[PLAYER_FIELDS[name].offset + 3] = 0xa0 + index;
  bytes.fill(0x7b, BAG_OFFSET - 28, BAG_OFFSET);
  bytes.fill(0xa6, BAG_OFFSET + BAG_SLOTS * ITEM_RECORD_SIZE, BAG_OFFSET + BAG_SLOTS * ITEM_RECORD_SIZE + 28);
  bytes.fill(0x93, CRC_END);
  new DataView(bytes.buffer).setUint32(0, crc32(bytes.subarray(CRC_START, CRC_END)), true);
  return new SaveDocument(bytes);
}

test('player fields decode and packed attributes preserve all high bytes', () => {
  const save = signedFixture();
  assert.equal(save.playerProfile, true);
  assert.equal(save.player('money'), 200);
  assert.equal(save.player('max_hp'), 25);
  assert.equal(save.player('max_rp'), 56);
  assert.equal(save.player('strength'), 5);
  save.setPlayer({ money: 2000000000, max_hp: 1000, hp: 999, max_rp: 65535, rp: 100, strength: 0xffffff, intelligence: 10, vitality: 12 });
  assert.equal(save.player('money'), 2000000000);
  assert.equal(save.player('strength'), 0xffffff);
  for (const name of ['strength', 'intelligence', 'vitality']) assert.equal(save.data[PLAYER_FIELDS[name].offset + 3], save.original[PLAYER_FIELDS[name].offset + 3]);
  const output = save.build();
  assert.equal(new SaveDocument(output).crcValid, true);
  for (let offset = 4; offset < output.length; offset++) {
    if (offset >= 0x4c && offset < 0x50 || offset >= 0x54 && offset < 0x6c) continue;
    assert.equal(output[offset], save.original[offset], `Unexpected edit at ${offset}`);
  }
  assert.equal(save.undoStack.length, 1);
  save.undo();
  assert.deepEqual(save.data, save.original);
  save.redo();
  assert.equal(save.player('hp'), 999);
});

test('player validation rejects ranges and inconsistent pairs atomically without losing redo', () => {
  const save = signedFixture();
  save.setPlayer({ money: 300 });
  save.undo();
  for (const values of [{ money: -1 }, { money: 2000000001 }, { max_hp: 0 }, { hp: 26 }, { max_hp: 24 }, { rp: 57 }, { max_rp: 55 }, { max_rp: 65536 }, { strength: 0 }, { vitality: 0x1000000 }, { intelligence: '' }, { money: 2.2 }, { level: 10 }]) {
    assert.throws(() => save.setPlayer(values));
    assert.deepEqual(save.data, save.original);
    assert.equal(save.undoStack.length, 0);
    assert.equal(save.redoStack.length, 1);
  }
  save.setPlayer({ hp: 0, rp: 0 });
  assert.equal(new SaveDocument(save.build()).crcValid, true);
  assert.throws(() => save.player('__proto__'));
});

test('valid player profiles block invalid raw export, unknown original profiles still round trip', () => {
  const save = createDemo();
  save.setNumber(0x58, 'i32', 26);
  assert.throws(() => save.build(), /Current health/);
  save.undo();
  save.setNumber(0x4c, 'i32', -1);
  assert.throws(() => save.build(), /Money/);
  save.undo();
  assert.deepEqual(save.build(), save.original);
  const bytes = save.original.slice();
  new DataView(bytes.buffer).setInt32(0x54, 0, true);
  new DataView(bytes.buffer).setUint32(0, crc32(bytes.subarray(CRC_START, CRC_END)), true);
  const unknown = new SaveDocument(bytes);
  assert.equal(unknown.playerProfile, false);
  assert.deepEqual(unknown.build(), bytes);
  unknown.setCalendar({ day: 10, season: 0, year: 1 });
  assert.equal(new SaveDocument(unknown.build()).crcValid, true);
});

test('bag is exactly sixty records, separate from held equipment and spells', () => {
  const save = signedFixture();
  assert.equal(BAG_OFFSET + BAG_SLOTS * ITEM_RECORD_SIZE, 0x6268);
  assert.equal(save.bagItems().length, 60);
  assert.deepEqual(save.bagItems().slice(0, 4).map(({ id, quantity, level }) => [id, quantity, level]), [[328, 1, 1], [559, 1, 1], [753, 9, 1], [753, 4, 1]]);
  save.setBagItem(59, { id: 753, quantity: 9, level: 10 }, stackable);
  const item = save.bagSlot(59);
  assert.equal(item.offset, 0x624c);
  assert.deepEqual(item.levels, Array(9).fill(10));
  assert.deepEqual(save.data.subarray(BAG_OFFSET - 28, BAG_OFFSET), save.original.subarray(BAG_OFFSET - 28, BAG_OFFSET));
  assert.deepEqual(save.data.subarray(0x6268), save.original.subarray(0x6268));
  assert.equal(new SaveDocument(save.build()).crcValid, true);
});

test('same-item quantity edits retain packed flag, equipment metadata and mixed unit levels', () => {
  const save = signedFixture();
  const offset = save.bagSlot(3).offset;
  save.transact('Synthetic metadata', next => {
    next[offset + 1] |= 0x80;
    next[offset + 2] = 0x74;
    next[offset + 3] = 0x91;
    next.set([0, 1, 8, 3], offset + 4);
    next.fill(0xc7, offset + 13, offset + 28);
  });
  const before = save.data.slice();
  assert.equal(save.bagSlot(3).mixedLevels, true);
  save.setBagItem(3, { id: 753, quantity: 3 }, stackable);
  assert.equal(save.bagSlot(3).headerFlag, true);
  assert.deepEqual(save.bagSlot(3).levels, [1, 2, 9]);
  assert.deepEqual(save.data.subarray(offset + 2, offset + 28), before.subarray(offset + 2, offset + 28));
  save.undo();
  save.setBagItem(3, { id: 753, quantity: 6 }, stackable);
  assert.deepEqual(save.bagSlot(3).levels, [1, 2, 9, 4, 1, 1]);
  assert.deepEqual(save.data.subarray(offset + 13, offset + 28), before.subarray(offset + 13, offset + 28));
  save.setBagItem(3, { id: 753, quantity: 6, level: 7 }, stackable);
  assert.deepEqual(save.data.subarray(offset + 4, offset + 13), new Uint8Array(9).fill(6));
  assert.deepEqual(save.data.subarray(offset + 13, offset + 28), before.subarray(offset + 13, offset + 28));
});

test('same-equipment level edits touch only its level byte, replacement resets the entire record', () => {
  const save = signedFixture();
  const offset = BAG_OFFSET;
  save.transact('Synthetic upgrades', next => { next[offset + 1] |= 0x80; next.fill(0x46, offset + 2, offset + 28); next[offset + 4] = 1; });
  const before = save.data.slice();
  save.setBagItem(0, { id: 328, quantity: 1, level: 10 }, equipment);
  assert.equal(save.data[offset + 4], 9);
  for (let i = 0; i < 28; i++) if (i !== 4) assert.equal(save.data[offset + i], before[offset + i]);
  save.setBagItem(0, { id: 559, quantity: 1 }, equipment);
  assert.equal(save.bagSlot(0).headerFlag, false);
  assert.deepEqual(save.data.subarray(offset + 2, offset + 28), new Uint8Array(26));
  save.setBagItem(0, { id: 753, quantity: 3, level: 4 }, stackable);
  assert.deepEqual(save.data.subarray(offset + 4, offset + 13), new Uint8Array(9).fill(3));
  save.setBagItem(0, { id: 0, quantity: 0 });
  assert.deepEqual(save.data.subarray(offset, offset + 28), new Uint8Array(28));
  save.undo();
  assert.equal(save.bagSlot(0).id, 753);
});

test('bag edits reject invalid indices, definitions, stack limits and levels atomically', () => {
  const save = signedFixture();
  for (const [slot, changes, definition] of [
    [-1, { id: 753, quantity: 1 }, stackable], [60, { id: 753, quantity: 1 }, stackable],
    [4, { id: 2048, quantity: 1 }, stackable], [4, { id: 1, quantity: 1 }, null],
    [4, { id: 1, quantity: 1 }, { max_stack: 9, category: 55 }],
    [4, { id: 753, quantity: 10 }, stackable], [4, { id: 328, quantity: 2 }, equipment],
    [4, { id: 753, quantity: 0 }, stackable], [4, { id: 0, quantity: 1 }],
    [4, { id: 753, quantity: 1, level: 0 }, stackable], [4, { id: 753, quantity: 1, level: 11 }, stackable],
    [4, { id: 753, quantity: 1, level: '' }, stackable], [4, { id: 753, quantity: 1 }, { max_stack: 16, category: 0 }],
    [4, { id: 753, quantity: 1 }, { max_stack: 9 }],
  ]) {
    assert.throws(() => save.setBagItem(slot, changes, definition));
    assert.deepEqual(save.data, save.original);
    assert.equal(save.undoStack.length, 0);
  }
  assert.throws(() => save.bagSlot(60));
  assert.equal(bagStackLimit({ category: 0, max_stack: 2 }), 9);
  assert.equal(bagStackLimit({ category: 0, max_stack: 1 }), 1);
});

test('catalog requires actual item definitions and bounds for bag edits, not just name registry', () => {
  const names = new ItemCatalog();
  assert.equal(names.name(753), 'Turnip Seeds');
  assert.throws(() => names.bagDefinition(753), /definition table/);
  assert.equal(names.bagDefinition(0), null);
  const catalog = new ItemCatalog({ tables: { item: { count: 2, records: [{}, stackable] } } });
  assert.equal(catalog.bagDefinition(1), stackable);
  assert.throws(() => catalog.bagDefinition(2));
  assert.throws(() => catalog.bagDefinition(2048));
});
