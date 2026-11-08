import test from 'node:test';
import assert from 'node:assert/strict';
import { SaveDocument, createDemo, CRC_END, SYSTEM_SAVE_SIZE, crc32 } from '../web/save-core.js';

function femaleSave() {
  const source = createDemo();
  source.patchBytes(0x36, '01');
  source.setNumber(0x38, 'u32', 0xa5210003);
  source.setNumber(0x74, 'u32', 0xadfda52b);
  source.transact('Nonzero trailer', next => next.fill(0x94, CRC_END));
  return new SaveDocument(source.build());
}

test('export can auto-correct a changed gender byte to the loaded original', () => {
  const save = femaleSave();
  save.patchBytes(0x36, '00');
  const before = save.data.slice();
  const output = save.build({ gender: 'original' });
  assert.equal(output[0x36], 1, 'Export must restore the original Frey byte');
  assert.deepEqual(save.data, before);
  assert.equal(new SaveDocument(output).crcValid, true);
});

test('explicit male/female export choices affect only gender and CRC by default', () => {
  const save = femaleSave();
  for (const [gender, expected] of [['male', 0], ['female', 1]]) {
    const output = save.build({ gender });
    assert.equal(output[0x36], expected);
    for (let offset = 4; offset < output.length; offset++) if (offset !== 0x36) assert.equal(output[offset], save.data[offset]);
    assert.equal(new SaveDocument(output).crcValid, true);
  }
  assert.deepEqual(save.data, save.original);
  assert.deepEqual(save.build(), save.original);
});

test('optional appearance reset clears only swap flag and packed outfit bits', () => {
  const save = femaleSave();
  const output = save.build({ gender: 'female', resetAppearance: true });
  const view = new DataView(output.buffer);
  assert.equal(output[0x36], 1);
  assert.equal(view.getUint32(0x38, true), (save.readNumber(0x38, 'u32') & ~1) >>> 0);
  assert.equal(view.getUint32(0x74, true), (save.readNumber(0x74, 'u32') & ~0xfc0000) >>> 0);
  for (let offset = 4; offset < output.length; offset++) {
    if (offset === 0x36 || offset >= 0x38 && offset < 0x3c || offset >= 0x74 && offset < 0x78) continue;
    assert.equal(output[offset], save.original[offset]);
  }
  assert.deepEqual(save.data, save.original);
});

test('appearance reset also removes the persistent selection that flips body and portrait on load', () => {
  const source = createDemo();
  source.setNumber(0x20740, 'i32', 9999);
  source.setNumber(0x20744, 'u32', 0xa5c37e91);
  const save = new SaveDocument(source.build());
  assert.deepEqual(save.appearance(), { swapped: false, override: 9999, outfit: 0 });
  assert.deepEqual(save.build(), save.original);
  assert.equal(new SaveDocument(save.build({ gender: 'male' })).readNumber(0x20740, 'i32'), 9999);
  for (const gender of ['male', 'female']) {
    const output = save.build({ gender, resetAppearance: true });
    const decoded = new SaveDocument(output);
    assert.equal(decoded.readNumber(0x20740, 'i32'), 0, 'A nonzero selection still overrides the protagonist visuals');
    assert.equal(decoded.readNumber(0x20744, 'u32'), 0xa5c37e91, 'Adjacent state must be preserved');
    assert.equal(decoded.player('prince_points'), save.player('prince_points'));
    assert.equal(decoded.crcValid, true);
    assert.deepEqual(decoded.appearance(), { swapped: false, override: 0, outfit: 0 });
    const switchOutput = save.build({ gender, resetAppearance: true, platform: 'switch', experimental: true });
    const sw = new SaveDocument(switchOutput);
    assert.deepEqual(sw.appearance(), decoded.appearance());
    assert.equal(sw.readNumber(0x20744, 'u32'), 0xa5c37e91);
    assert.equal(sw.crcValid, true);
    for (let offset = 4; offset < output.length; offset++) {
      if (offset === 0x36 || offset >= 0x20740 && offset < 0x20744) continue;
      assert.equal(output[offset], save.original[offset], `Unexpected reset at ${offset.toString(16)}`);
    }
  }
  assert.deepEqual(save.data, save.original);
  assert.equal(save.undoStack.length, 0);
});

test('gender correction survives PC/Switch conversion and preserves trailers', () => {
  const pc = femaleSave();
  const swBytes = pc.build({ platform: 'switch', experimental: true, gender: 'male', resetAppearance: true });
  assert.equal(swBytes[0x36], 0);
  const sw = new SaveDocument(swBytes);
  const back = sw.build({ platform: 'pc', experimental: true, gender: 'female' });
  assert.equal(back[0x36], 1);
  assert.equal(new SaveDocument(back).crcValid, true);
  assert.deepEqual(back.subarray(CRC_END), pc.original.subarray(CRC_END));
  assert.deepEqual(pc.data, pc.original);
});

test('order points expose the verified stored field and 99,999 cap', () => {
  const save = createDemo();
  save.setPlayer({ prince_points: 99999 });
  assert.equal(save.readNumber(0x20710, 'i32'), 99999);
  assert.equal(save.player('prince_points'), 99999);
  const before = save.data.slice();
  for (const value of [-1, 100000, '', 1.5]) assert.throws(() => save.setPlayer({ prince_points: value }));
  assert.deepEqual(save.data, before);
  assert.equal(new SaveDocument(save.build()).crcValid, true);
  save.undo();
  assert.deepEqual(save.data, save.original);
});

test('invalid export choices fail without changing bytes or history', () => {
  const save = femaleSave();
  for (const options of [{ gender: 'invented' }, { gender: null }, { gender: 'male', resetAppearance: 1 }, { resetAppearance: true }]) assert.throws(() => save.build(options));
  assert.deepEqual(save.data, save.original);
  assert.equal(save.undoStack.length, 0);
  const once = save.build({ gender: 'male', resetAppearance: true });
  assert.deepEqual(new SaveDocument(once).build({ gender: 'male', resetAppearance: true }), once);
});

test('matching the original never guesses an unrecognized gender, even after a valid working edit', () => {
  const source = createDemo();
  source.patchBytes(0x36, '7F');
  const save = new SaveDocument(source.build());
  assert.equal(save.gender(), null);
  assert.deepEqual(save.build(), save.original);
  save.patchBytes(0x36, '01');
  assert.equal(save.gender(), 'female');
  assert.throws(() => save.build({ gender: 'original' }), /Original gender is unrecognized/);
  assert.equal(save.build({ gender: 'male' })[0x36], 0);
  assert.equal(save.build({ gender: 'female' })[0x36], 1);
  assert.equal(save.original[0x36], 0x7f);
  assert.equal(save.data[0x36], 1);
});

test('system output stays byte-exact and rejects slot-only gender correction', () => {
  const bytes = new Uint8Array(SYSTEM_SAVE_SIZE);
  bytes.set(new TextEncoder().encode('RF4D'));
  new DataView(bytes.buffer).setUint32(4, crc32(bytes.subarray(8)), true);
  const save = new SaveDocument(bytes, 'rf4_sys.sav');
  assert.deepEqual(save.build(), bytes);
  for (const gender of ['original', 'male', 'female']) assert.throws(() => save.build({ gender }), /slot save/);
  assert.deepEqual(save.data, bytes);
});
