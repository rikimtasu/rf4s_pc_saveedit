import test from 'node:test';
import assert from 'node:assert/strict';
import { SaveDocument, SAVE_SIZE, CRC_START, CRC_END, FLAGS_OFFSET, STORY_REGISTER, SCALARS, crc32, createDemo, readFlag, writeFlag, parseEmdeb, equalBytes, integer } from '../web/save-core.js';

function fixture() {
  const bytes = Uint8Array.from({ length: SAVE_SIZE }, (_, i) => (i * 31 + 7) & 255);
  const view = new DataView(bytes.buffer);
  view.setUint32(SCALARS.day, 9, true);
  view.setUint32(SCALARS.season, 0, true);
  view.setUint32(SCALARS.year, 1, true);
  view.setUint32(0, crc32(bytes.subarray(CRC_START, CRC_END)), true);
  return bytes;
}

function symbolsFixture(variables = [STORY_REGISTER, { name: 'FLG_TEST', bitOffset: 9, width: 1 }, { name: 'REG_TEST', bitOffset: 10, width: 32 }]) {
  const namesBase = 68 + variables.length * 24;
  const size = namesBase + variables.reduce((total, v) => total + v.name.length + 1, 0);
  const bytes = new Uint8Array(size);
  bytes.set(new TextEncoder().encode('EMDb'));
  const view = new DataView(bytes.buffer);
  view.setUint32(24, variables.length, true);
  view.setUint32(28, 64, true);
  view.setUint32(52, namesBase, true);
  let pointer = namesBase;
  for (const [i, v] of variables.entries()) {
    const base = 68 + i * 24;
    view.setUint32(base, pointer, true);
    view.setUint32(base + 12, v.bitOffset, true);
    view.setUint32(base + 16, v.width << 8, true);
    bytes.set(new TextEncoder().encode(v.name), pointer);
    pointer += v.name.length + 1;
  }
  return bytes;
}

test('CRC-32 matches IEEE vectors', () => {
  assert.equal(crc32(new Uint8Array()), 0);
  assert.equal(crc32(new TextEncoder().encode('123456789')), 0xcbf43926);
  assert.equal(crc32(new TextEncoder().encode('The quick brown fox jumps over the lazy dog')), 0x414fa339);
});

test('rejects unsupported slot sizes', () => {
  for (const size of [0, 64, SAVE_SIZE - 1, SAVE_SIZE + 1]) assert.throws(() => new SaveDocument(new Uint8Array(size)), /Unsupported save size/);
  assert.equal(new SaveDocument(fixture()).crcValid, true);
});

test('copies caller data and round trips a valid original exactly', () => {
  const bytes = fixture();
  const save = new SaveDocument(bytes);
  bytes[100] ^= 1;
  assert.notEqual(save.data[100], bytes[100]);
  assert.deepEqual(save.build(), save.original);
  assert.equal(save.get('day'), 9);
});

test('calendar export changes only verified fields and CRC', () => {
  const original = fixture();
  const save = new SaveDocument(original);
  save.setCalendar({ day: 30, season: 3, year: 1234 });
  const exported = save.build();
  assert.equal(new SaveDocument(exported).crcValid, true);
  assert.deepEqual(save.original, original);
  assert.equal(save.get('year'), 1234);
  for (let i = 4; i < SAVE_SIZE; i++) {
    if (i >= 0x14 && i < 0x20) continue;
    assert.equal(exported[i], original[i], `unexpected write at ${i}`);
  }
  assert.deepEqual(exported.subarray(CRC_END), original.subarray(CRC_END));
});

test('export is immutable and deterministic', () => {
  const save = new SaveDocument(fixture());
  save.setCalendar({ day: 10, season: 1, year: 2 });
  const before = save.data.slice();
  const output = save.build();
  assert.deepEqual(save.data, before);
  assert.deepEqual(save.build(), output);
  output[200] ^= 1;
  assert.deepEqual(save.data, before);
});

test('calendar validation is atomic', () => {
  const save = new SaveDocument(fixture());
  for (const date of [
    { day: 0, season: 0, year: 1 }, { day: 31, season: 0, year: 1 },
    { day: 2, season: 4, year: 1 }, { day: 2, season: 0, year: 0 },
    { day: 2.5, season: 0, year: 1 }, { day: '', season: 0, year: 1 },
    { day: 2, season: 0, year: 4294967296 },
  ]) assert.throws(() => save.setCalendar(date));
  assert.deepEqual(save.data, save.original);
  assert.equal(save.undoStack.length, 0);
});

test('integer parser rejects blank, nonfinite and fractional values', () => {
  for (const v of ['', ' ', NaN, Infinity, '-1', 1.2, 'nonsense', null, true, undefined]) assert.throws(() => integer(v, 0, 100));
  assert.equal(integer('0x14', 0, 100), 20);
});

test('MSB-first register bits and byte-local LSB addressing', () => {
  const bytes = new Uint8Array(SAVE_SIZE);
  writeFlag(bytes, STORY_REGISTER, 257);
  assert.equal(bytes[FLAGS_OFFSET], 1);
  assert.equal(bytes[FLAGS_OFFSET + 1], 1);
  assert.equal(readFlag(bytes, STORY_REGISTER), 257);
  writeFlag(bytes, STORY_REGISTER, 104);
  assert.equal(bytes[FLAGS_OFFSET], 44);
  assert.equal(readFlag(bytes, STORY_REGISTER), 104);
});

test('32-bit registers avoid signed JS shift truncation and preserve neighbors', () => {
  const save = new SaveDocument(fixture());
  const variable = { name: 'REG_WIDE', bitOffset: 13, width: 32 };
  for (const value of [0, 1, 0x80000000, 0xffffffff, 1234567890]) {
    save.setFlag(variable, value);
    assert.equal(save.flag(variable), value);
    for (let bit = 0; bit < 64; bit++) {
      if (bit >= 13 && bit < 45) continue;
      const index = FLAGS_OFFSET + (bit >> 3);
      assert.equal((save.data[index] >> (bit & 7)) & 1, (save.original[index] >> (bit & 7)) & 1);
    }
  }
});

test('rejects invalid bit fields and values without mutation', () => {
  const save = new SaveDocument(fixture());
  for (const variable of [
    { bitOffset: -1, width: 1 }, { bitOffset: 6656, width: 1 },
    { bitOffset: 4095, width: 2 }, { bitOffset: 0, width: 0 }, { bitOffset: 0, width: 33 },
  ]) assert.throws(() => save.setFlag(variable, 0));
  assert.throws(() => save.setFlag(STORY_REGISTER, 512));
  assert.throws(() => save.setFlag(STORY_REGISTER, -1));
  assert.deepEqual(save.data, save.original);
});

test('raw patches are bounded and checksum protected', () => {
  const save = new SaveDocument(fixture());
  for (const [offset, bytes] of [[0, '00'], [3, '00'], [SAVE_SIZE, '00'], [SAVE_SIZE - 1, '00 01'], [20, 'F'], [20, 'GG'], [20, ''], [20, Array(257).fill('01').join(' ')]]) {
    assert.throws(() => save.patchBytes(offset, bytes));
  }
  assert.equal(save.dirty, false);
  assert.throws(() => save.transact('Bad CRC edit', next => { next[0] ^= 1; }));
  save.patchBytes('0x54', 'AA bb 00 FF');
  assert.deepEqual(save.data.slice(0x54, 0x58), new Uint8Array([170, 187, 0, 255]));
  save.patchBytes(SAVE_SIZE - 1, 'FE');
  assert.equal(save.build()[SAVE_SIZE - 1], 254);
});

test('throwing transactions do not change working bytes', () => {
  const save = new SaveDocument(fixture());
  assert.throws(() => save.transact('Fail', next => { next[80] ^= 255; throw new Error('abort'); }));
  assert.deepEqual(save.data, save.original);
  assert.equal(save.undoStack.length, 0);
});

test('undo / redo groups edits and branches invalidate redo', () => {
  const save = new SaveDocument(fixture());
  save.setCalendar({ day: 30, season: 3, year: 500 });
  const calendar = save.data.slice();
  save.setFlag(STORY_REGISTER, 50);
  assert.equal(save.undoStack.length, 2);
  save.undo();
  assert.deepEqual(save.data, calendar);
  save.undo();
  assert.equal(save.dirty, false);
  save.redo();
  assert.deepEqual(save.data, calendar);
  save.patchBytes(500, '12');
  assert.equal(save.redoStack.length, 0);
  assert.equal(save.redo(), false);
});

test('restore is undoable and unchanged edits create no history', () => {
  const save = new SaveDocument(fixture());
  assert.equal(save.setCalendar({ day: 9, season: 0, year: 1 }), false);
  assert.equal(save.undoStack.length, 0);
  save.patchBytes(100, 'AA BB');
  const edited = save.data.slice();
  save.reset();
  assert.equal(save.dirty, false);
  save.undo();
  assert.deepEqual(save.data, edited);
});

test('change ranges reflect net changes, not historical touches', () => {
  const save = new SaveDocument(fixture());
  save.patchBytes(100, '00 00');
  assert.equal(save.changedBytes, 2);
  assert.equal(save.changes().length, 1);
  assert.equal(save.changes()[0].offset, 100);
  save.patchBytes(100, save.original[100].toString(16).padStart(2, '0'));
  assert.equal(save.changedBytes, 1);
  assert.equal(save.changes()[0].offset, 101);
});

test('CRC mismatch requires consent and repair preserves all body bytes', () => {
  const bytes = fixture();
  bytes[0] ^= 1;
  const save = new SaveDocument(bytes);
  assert.equal(save.crcValid, false);
  assert.throws(() => save.build(), /Acknowledge/);
  const repaired = save.build({ repair: true });
  assert.equal(new SaveDocument(repaired).crcValid, true);
  assert.deepEqual(repaired.subarray(4), bytes.subarray(4));
  assert.deepEqual(save.original, bytes);
});

test('raw invalid dates block export until corrected', () => {
  const save = new SaveDocument(fixture());
  save.patchBytes(SCALARS.day, '00 00 00 00');
  assert.throws(() => save.build(), /Day must/);
  save.setCalendar({ day: 1, season: 0, year: 1 });
  assert.equal(new SaveDocument(save.build()).crcValid, true);
});

test('symbol parser reads bounded EMDb developer records', () => {
  const variables = parseEmdeb(symbolsFixture());
  assert.equal(variables.length, 3);
  assert.deepEqual(variables[0], STORY_REGISTER);
  assert.deepEqual(variables[2], { name: 'REG_TEST', bitOffset: 10, width: 32 });
});

test('symbol parser rejects wrong magic, bounds, overlaps, duplicate names and unterminated strings', () => {
  assert.throws(() => parseEmdeb(new Uint8Array(64)), /emdeb.bin/);
  const badCount = symbolsFixture();
  new DataView(badCount.buffer).setUint32(24, 10000, true);
  assert.throws(() => parseEmdeb(badCount), /bounds/);
  assert.throws(() => parseEmdeb(symbolsFixture([{ name: 'A', bitOffset: 0, width: 9 }, { name: 'B', bitOffset: 8, width: 1 }])), /Overlapping/);
  assert.throws(() => parseEmdeb(symbolsFixture([{ name: 'A', bitOffset: 0, width: 1 }, { name: 'A', bitOffset: 1, width: 1 }])), /duplicate/);
  assert.throws(() => parseEmdeb(symbolsFixture([{ name: 'A', bitOffset: 4096, width: 1 }])), /zone 1/);
  const badPointer = symbolsFixture();
  new DataView(badPointer.buffer).setUint32(68, 12, true);
  assert.throws(() => parseEmdeb(badPointer), /pointer/);
  const missingNull = symbolsFixture([{ name: 'A', bitOffset: 0, width: 1 }]);
  missingNull[missingNull.length - 1] = 65;
  assert.throws(() => parseEmdeb(missingNull), /symbol name/);
});

test('demo has a correct checksum but only synthetic contents', () => {
  const demo = createDemo();
  assert.equal(demo.crcValid, true);
  assert.equal(demo.get('day'), 9);
  assert.equal(demo.flag(STORY_REGISTER), 104);
  assert.equal(demo.dirty, false);
  assert.equal(equalBytes(demo.build(), demo.original), true);
});
