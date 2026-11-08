import test from 'node:test';
import assert from 'node:assert/strict';
import { SaveDocument, createDemo, SAVE_SIZE, SWITCH_SAVE_SIZE, SYSTEM_SAVE_SIZE, CRC_END, SWITCH_CRC_END, FLAGS_OFFSET, STORY_REGISTER, SYSTEM_FLAGS, crc32, convertSlot } from '../web/save-core.js';
import { ProgressCatalog, progressGroup } from '../web/progress-core.js';
import { SAVE_METADATA } from '../web/save-metadata.js';

function systemFixture() {
  const bytes = Uint8Array.from({ length: SYSTEM_SAVE_SIZE }, (_, i) => (i * 17 + 7) & 255);
  bytes.set(new TextEncoder().encode('RF4D'));
  new DataView(bytes.buffer).setUint32(4, crc32(bytes.subarray(8)), true);
  return bytes;
}

test('system container uses RF4D signature and its own checksum without slot interpretation', () => {
  const original = systemFixture();
  const save = new SaveDocument(original, 'rf4_sys.sav');
  assert.equal(save.kind, 'system');
  assert.equal(save.platform, 'shared');
  assert.equal(save.crcOffset, 4);
  assert.equal(save.crcStart, 8);
  assert.equal(save.crcEnd, SYSTEM_SAVE_SIZE);
  assert.equal(save.crcValid, true);
  assert.deepEqual(save.build(), original);
  assert.equal(save.playerProfile, false);
  for (const read of [() => save.get('day'), () => save.player('money'), () => save.bagItems(), () => save.flag(STORY_REGISTER), () => save.setFlag(STORY_REGISTER, 1), () => save.setCalendar({ day: 1, season: 0, year: 1 }), () => save.setPlayer({ money: 1 })]) assert.throws(read, /slot save/);
  const malformed = original.slice();
  malformed[0] ^= 1;
  assert.throws(() => new SaveDocument(malformed), /RF4D/);
});

test('system named flags retain every other bit and payload, and share undo/redo', () => {
  const save = new SaveDocument(systemFixture());
  const values = Object.fromEntries(SYSTEM_FLAGS.map(({ bit }) => [bit, 1 - save.systemFlag(bit)]));
  values[31] = 1 - save.systemFlag(31);
  save.setSystemFlags(values);
  assert.equal(save.undoStack.length, 1);
  for (let bit = 0; bit < 32; bit++) assert.equal(save.systemFlag(bit), values[bit] ?? save.systemFlag(bit, save.original));
  const output = save.build();
  assert.equal(new SaveDocument(output).crcValid, true);
  assert.deepEqual(output.subarray(0, 4), save.original.subarray(0, 4));
  assert.deepEqual(output.subarray(12), save.original.subarray(12));
  assert.equal(save.changedBytes, save.changes().reduce((count, range) => count + range.after.length, 0));
  save.undo();
  assert.deepEqual(save.data, save.original);
  save.redo();
  assert.deepEqual(save.build(), output);
});

test('system signature/checksum are protected and typed/raw bounds use system size', () => {
  const save = new SaveDocument(systemFixture());
  for (const offset of [0, 3, 4, 7]) {
    assert.throws(() => save.patchBytes(offset, 'AA'));
    assert.throws(() => save.setNumber(offset, 'u8', 1));
  }
  assert.throws(() => save.transact('Signature tamper', next => { next[0] ^= 1; }));
  assert.throws(() => save.setNumber(SYSTEM_SAVE_SIZE - 1, 'u16', 1));
  assert.throws(() => save.readNumber(SYSTEM_SAVE_SIZE, 'u8'));
  assert.throws(() => save.setSystemFlags({ 0: 1, 32: 1 }));
  assert.throws(() => save.setSystemFlags({ 1: 2 }));
  assert.deepEqual(save.data, save.original);
  save.setNumber(SYSTEM_SAVE_SIZE - 1, 'u8', 0xa9);
  assert.equal(save.build()[SYSTEM_SAVE_SIZE - 1], 0xa9);
});

test('damaged system checksum requires consent and repair retains every data byte', () => {
  const bytes = systemFixture();
  bytes[4] ^= 1;
  const save = new SaveDocument(bytes);
  assert.throws(() => save.build(), /Acknowledge/);
  const output = save.build({ repair: true });
  assert.deepEqual(output.subarray(8), bytes.subarray(8));
  assert.deepEqual(output.subarray(0, 4), bytes.subarray(0, 4));
  assert.equal(new SaveDocument(output).crcValid, true);
});

test('experimental PC/Switch conversion preserves common fields and nonzero 224-byte trailers', () => {
  const pc = createDemo();
  pc.transact('Trailer fixture', next => next.fill(0x9a, CRC_END));
  const before = pc.data.slice();
  assert.throws(() => pc.build({ platform: 'switch' }), /experimental/);
  const converted = pc.build({ platform: 'switch', experimental: true });
  assert.equal(converted.length, SWITCH_SAVE_SIZE);
  const sw = new SaveDocument(converted);
  assert.equal(sw.platform, 'switch');
  assert.equal(sw.crcValid, true);
  assert.equal(sw.crcEnd, SWITCH_CRC_END);
  assert.equal(sw.player('money'), 200);
  assert.equal(sw.flag(STORY_REGISTER), pc.flag(STORY_REGISTER));
  assert.deepEqual(sw.bagItems(), pc.bagItems());
  assert.deepEqual(converted.subarray(SWITCH_CRC_END), before.subarray(CRC_END));
  assert.deepEqual(converted.subarray(4, SWITCH_CRC_END), before.subarray(4, SWITCH_CRC_END));
  const returned = sw.build({ platform: 'pc', experimental: true });
  assert.equal(returned.length, SAVE_SIZE);
  assert.deepEqual(returned, pc.build());
  assert.deepEqual(pc.data, before);
  assert.deepEqual(sw.build(), converted);
});

test('conversion refuses data loss, damaged sources, invalid profile and system inputs', () => {
  const pc = createDemo();
  pc.patchBytes(SWITCH_CRC_END, '01');
  assert.throws(() => pc.build({ platform: 'switch', experimental: true }), /discard data/);
  const valid = createDemo().build();
  const damaged = valid.slice();
  damaged[0] ^= 1;
  assert.throws(() => convertSlot(damaged, 'switch', { experimental: true }), /checksum/);
  const invalid = createDemo();
  invalid.setNumber(0x54, 'i32', 0);
  assert.throws(() => invalid.build({ platform: 'switch', experimental: true }), /health/);
  assert.throws(() => convertSlot(systemFixture(), 'pc', { experimental: true }), /System saves/);
  assert.throws(() => convertSlot(valid, 'ps4', { experimental: true }));
  assert.deepEqual(convertSlot(valid, 'pc'), valid);
});

test('Switch raw bounds do not expose eight nonexistent bytes', () => {
  const sw = new SaveDocument(createDemo().build({ platform: 'switch', experimental: true }));
  assert.throws(() => sw.patchBytes(SWITCH_SAVE_SIZE, 'AA'));
  assert.throws(() => sw.setNumber(SWITCH_SAVE_SIZE - 1, 'u16', 1));
  sw.setNumber(SWITCH_SAVE_SIZE - 1, 'u8', 0xa9);
  assert.equal(sw.build()[SWITCH_SAVE_SIZE - 1], 0xa9);
});

test('built-in developer and CT metadata validate, rejecting misleading partial registers', () => {
  const catalog = new ProgressCatalog(SAVE_METADATA.symbols, SAVE_METADATA.ctFlags);
  assert.equal(SAVE_METADATA.symbols.length, 1822);
  assert.equal(catalog.variables.length, 1897);
  assert.equal(catalog.byName.get('REG_MAIN_SCENARIO').width, 9);
  assert.ok(SAVE_METADATA.rejectedCT.includes('Story Progress'));
  assert.ok(SAVE_METADATA.rejectedCT.includes('Volkanon Tutorial Active'));
  assert.equal(catalog.variables.some(variable => variable.label === 'Story Progress'), false);
  assert.equal(catalog.variables.some(variable => variable.label === 'Rune Prana Locked'), true);
  assert.equal(progressGroup(catalog.byName.get('REG_SUBEV_NOW')), 'Town events');
  assert.equal(progressGroup(catalog.byName.get('REG_QUEST_AFTER')), 'Requests');
  assert.throws(() => new ProgressCatalog([STORY_REGISTER], [{ name: 'BAD', bitOffset: 6, width: 1, label: 'Wrong partial flag' }]), /conflicts/);
  assert.throws(() => new ProgressCatalog([{ ...STORY_REGISTER, width: 3 }]), /main-story/);
});

test('progress profiles use full-width MSB-first fields and apply atomically in one undo group', () => {
  const catalog = new ProgressCatalog(SAVE_METADATA.symbols, SAVE_METADATA.ctFlags);
  const save = createDemo();
  const profile = catalog.parseProfile(JSON.stringify({ format: 'rf4s-progress-v1', flags: { REG_MAIN_SCENARIO: 430, REG_SUBEV_RSV: 56, REG_SUBEV_NOW: 0, REG_QUEST_AFTER: 200, FLG_SCENARIO_END: 1 } }));
  save.setFlags(profile.entries);
  assert.equal(save.flag(STORY_REGISTER), 430);
  assert.equal(save.flag(catalog.byName.get('REG_SUBEV_RSV')), 56);
  assert.equal(save.flag(catalog.byName.get('REG_QUEST_AFTER')), 200);
  assert.equal(save.undoStack.length, 1);
  const output = save.build();
  assert.equal(new SaveDocument(output).crcValid, true);
  for (let offset = 4; offset < SAVE_SIZE; offset++) {
    if (offset >= FLAGS_OFFSET && offset < FLAGS_OFFSET + 832) continue;
    assert.equal(output[offset], save.original[offset]);
  }
  save.undo();
  assert.deepEqual(save.data, save.original);
  save.redo();
  assert.deepEqual(save.build(), output);
});

test('every 9-bit story value can be stored without changing adjacent flags', () => {
  const save = createDemo();
  const adjacent = save.data[FLAGS_OFFSET + 1] & 0xfe;
  for (let value = 0; value <= 511; value++) {
    save.setFlag(STORY_REGISTER, value);
    assert.equal(save.flag(STORY_REGISTER), value);
    assert.equal(save.data[FLAGS_OFFSET + 1] & 0xfe, adjacent);
  }
  assert.equal(new SaveDocument(save.build()).crcValid, true);
});

test('profile validation rejects unknown names, empty payloads, range and overlap without writes', () => {
  const catalog = new ProgressCatalog(SAVE_METADATA.symbols, SAVE_METADATA.ctFlags);
  const save = createDemo();
  for (const profile of [{}, { format: 'rf4s-progress-v1', flags: {} }, { format: 'rf4s-progress-v1', flags: { UNKNOWN: 1 } }, { format: 'rf4s-progress-v1', flags: { REG_MAIN_SCENARIO: 512 } }, { format: 'rf4s-progress-v1', flags: { REG_MAIN_SCENARIO: '' } }]) assert.throws(() => catalog.parseProfile(JSON.stringify(profile)));
  assert.throws(() => save.setFlags([{ variable: STORY_REGISTER, value: 1 }, { variable: { name: 'Partial', bitOffset: 2, width: 1 }, value: 1 }]), /overlap/);
  assert.throws(() => save.setFlags([{ variable: STORY_REGISTER, value: 430 }, { variable: { name: 'Outside', bitOffset: 6656, width: 1 }, value: 1 }]));
  assert.deepEqual(save.data, save.original);
  assert.equal(save.undoStack.length, 0);
});

test('donor snapshots separate story, quests and all flags without editing either save', () => {
  const catalog = new ProgressCatalog(SAVE_METADATA.symbols, SAVE_METADATA.ctFlags);
  const donor = createDemo();
  const receiver = createDemo();
  donor.setFlag(STORY_REGISTER, 511);
  const before = donor.data.slice();
  const story = catalog.snapshot(donor, 'story');
  const quests = catalog.snapshot(donor, 'quests');
  assert.equal(story.REG_MAIN_SCENARIO, 511);
  assert.equal(story.REG_QUEST_AFTER, undefined);
  assert.equal(quests.REG_QUEST_AFTER, 0);
  assert.equal(quests.REG_MAIN_SCENARIO, undefined);
  assert.ok(Object.keys(catalog.snapshot(donor)).length > Object.keys(story).length);
  receiver.setFlags(catalog.entries(story));
  assert.equal(receiver.flag(STORY_REGISTER), 511);
  assert.deepEqual(donor.data, before);
  assert.throws(() => catalog.snapshot(new SaveDocument(systemFixture())));
});

test('new material fields match serializer storage and executable 50,000 caps', () => {
  const save = createDemo();
  save.setPlayer({ lumber: 50000, material_stone: 1200, fertilizer: 500 });
  assert.equal(save.readNumber(0x3c, 'i32'), 50000);
  assert.equal(save.readNumber(0x40, 'i32'), 1200);
  assert.equal(save.readNumber(0x44, 'i32'), 500);
  const before = save.data.slice();
  assert.throws(() => save.setPlayer({ lumber: 50001 }));
  assert.deepEqual(save.data, before);
});
