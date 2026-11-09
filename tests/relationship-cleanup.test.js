import test from 'node:test';
import assert from 'node:assert/strict';
import { SaveDocument, createDemo, CRC_END, crc32 } from '../web/save-core.js';
import { SAVE_METADATA } from '../web/save-metadata.js';

const bachelors = [1, 5, 8, 9, 15, 20];
const bachelorettes = [2, 4, 7, 11, 13, 17];
const offset = id => 0x1db40 + (id - 1) * 44;
const spouse = SAVE_METADATA.symbols.find(field => field.name === 'REG_WIFE_ID');

function sample() {
  const source = createDemo();
  source.transact('Synthetic Frey relationship leftovers', bytes => {
    bytes[0x36] = 1;
    const view = source.view(bytes);
    for (const id of [...bachelors, ...bachelorettes]) {
      view.setInt32(offset(id), 1574, true);
      view.setUint32(offset(id) + 8, 0xad400302, true);
      bytes[offset(id) + 12] = 97;
      view.setUint32(offset(id) + 20, 0xbeef807f | 133 << 7, true);
    }
    bytes.fill(0x96, CRC_END);
  });
  return new SaveDocument(source.build());
}

test('opt-in male export clears bachelor dating and both special addresses, preserving everything else', () => {
  const save = sample();
  const before = save.data.slice();
  const expected = save.data.slice();
  expected[0x36] = 0;
  for (const id of bachelors) {
    const view = save.view(expected);
    view.setUint32(offset(id) + 8, (view.getUint32(offset(id) + 8, true) & ~0x400000) >>> 0, true);
    expected[offset(id) + 12] = 23 + id;
    view.setUint32(offset(id) + 20, (view.getUint32(offset(id) + 20, true) & ~0x7f80 | id << 7) >>> 0, true);
  }
  save.view(expected).setUint32(0, crc32(expected.subarray(4, CRC_END)), true);
  assert.equal(Buffer.compare(Buffer.from(save.build({ gender: 'male', resetDating: true })), Buffer.from(expected)), 0, 'Only the selected dating/address masks, gender and CRC may change');
  assert.deepEqual(save.data, before);
  assert.deepEqual(save.original, before);
  assert.equal(save.undoStack.length, 0);
});

test('female cleanup targets only bachelorettes and uses Frey default address selectors', () => {
  const save = sample();
  const output = save.build({ gender: 'female', resetDating: true });
  const parsed = new SaveDocument(output);
  assert.equal(parsed.crcValid, true);
  for (const id of bachelorettes) {
    assert.equal(parsed.readNumber(offset(id) + 8, 'u32') & 0x400000, 0);
    assert.equal(output[offset(id) + 12], 70 + id);
    assert.equal(parsed.readNumber(offset(id) + 20, 'u32') >>> 7 & 255, 47 + id);
    assert.equal(parsed.readNumber(offset(id), 'i32'), 1574);
  }
  for (const id of bachelors) assert.deepEqual(output.slice(offset(id), offset(id) + 44), save.data.slice(offset(id), offset(id) + 44));
});

test('ordinary gender export and appearance reset do not silently erase relationships', () => {
  const save = sample();
  for (const options of [{}, { gender: 'male' }, { gender: 'male', resetAppearance: true }]) {
    const output = save.build(options);
    assert.deepEqual(output.slice(0x1db40, 0x1df34), save.data.slice(0x1db40, 0x1df34));
  }
});

test('cleanup requires explicit gender correction, boolean consent and a slot save', () => {
  const save = sample();
  assert.throws(() => save.build({ resetDating: true }), /gender/i);
  assert.throws(() => save.build({ gender: 'male', resetDating: 1 }), /checkbox/i);
  const bytes = new Uint8Array(9304); bytes.set([82, 70, 52, 68]);
  new DataView(bytes.buffer).setUint32(4, crc32(bytes.subarray(8)), true);
  assert.throws(() => new SaveDocument(bytes).build({ gender: 'male', resetDating: true }), /slot/i);
});

test('cleanup refuses to erase an incompatible spouse, but preserves a compatible spouse', () => {
  const save = sample();
  save.setFlag(spouse, 1);
  const before = save.data.slice();
  assert.throws(() => save.build({ gender: 'male', resetDating: true }), /spouse/i);
  assert.deepEqual(save.data, before);
  save.setFlag(spouse, 17);
  assert.equal(new SaveDocument(save.build({ gender: 'male', resetDating: true })).flag(spouse), 17);
  save.setFlag(spouse, 3);
  assert.throws(() => save.build({ gender: 'male', resetDating: true }), /spouse/i);
});

test('cleanup survives experimental Switch conversion and preserves the trailer', () => {
  const save = sample();
  const output = save.build({ gender: 'male', resetDating: true, platform: 'switch', experimental: true });
  assert.equal(output.length, 140416);
  const parsed = new SaveDocument(output);
  assert.equal(parsed.crcValid, true);
  assert.equal(parsed.readNumber(offset(1) + 8, 'u32') & 0x400000, 0);
  assert.deepEqual(output.slice(-224), save.data.slice(-224));
});

test('cleanup is idempotent and resolves original gender without guessing', () => {
  const save = sample();
  const first = save.build({ gender: 'original', resetDating: true });
  assert.equal(Buffer.compare(Buffer.from(new SaveDocument(first).build({ gender: 'female', resetDating: true })), Buffer.from(first)), 0);
  const bytes = save.data.slice(); bytes[0x36] = 255;
  const invalid = new SaveDocument(bytes);
  assert.throws(() => invalid.build({ repair: true, gender: 'original', resetDating: true }), /gender.*unrecognized/i);
});
