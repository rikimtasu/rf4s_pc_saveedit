import test from 'node:test';
import assert from 'node:assert/strict';
import { SaveDocument, createDemo, crc32 } from '../web/save-core.js';
import { PlayerNameEditor } from '../web/player-name-core.js';

function fixture() {
  const data = new Uint8Array(9304); data.set(new TextEncoder().encode('RF4D'));
  const view = new DataView(data.buffer);
  view.setUint32(8, 0xfffff, true); view.setUint32(12, 0xfffff, true);
  for (let id = 0; id < 40; id++) {
    const base = 0x4f0 + id * 0xa4;
    data.fill(0xa5, base, base + 0xa4);
    data.fill(0, base + 0x14, base + 0x27);
    data.set(new TextEncoder().encode('Lest'), base + 0x14);
  }
  view.setUint32(4, crc32(data.subarray(8)), true);
  const save = new SaveDocument(data);
  return { save, editor: new PlayerNameEditor(save) };
}

test('all 40 name records have bounded UTF-8 edits, preserve other bytes and share undo/redo/CRC', () => {
  for (let id = 0; id < 40; id++) {
    const { save, editor } = fixture();
    const before = save.data.slice();
    const offset = 0x504 + id * 0xa4;
    const expected = before.slice();
    expected.fill(0, offset, offset + 19); expected.set(new TextEncoder().encode('芙蕾A'), offset);
    editor.apply(id, '芙蕾A');
    assert.equal(editor.values(id).name, '芙蕾A');
    assert.equal(editor.values(id).offset, offset);
    assert.deepEqual(save.data, expected);
    assert.deepEqual(save.original, before);
    assert.equal(save.undoStack.length, 1);
    assert.equal(new SaveDocument(save.build()).crcValid, true);
    save.undo(); assert.deepEqual(save.data, before);
    save.redo(); assert.deepEqual(save.data, expected);
  }
});

test('reset clears only the name buffer so the game getter regenerates its default on load', () => {
  const { save, editor } = fixture();
  const before = save.data.slice();
  editor.apply(1, '');
  assert.equal(editor.values(1).usesDefault, true);
  assert.equal(editor.values(1).name, '');
  assert.equal(editor.values(1).gender, 'female');
  const expected = before.slice(); expected.fill(0, 0x504 + 0xa4, 0x517 + 0xa4);
  assert.deepEqual(save.data, expected);
  assert.equal(save.readNumber(8, 'u32'), 0xfffff);
  assert.equal(save.readNumber(16, 'u32'), 0);
});

test('invalid names fail without truncation, partial writes or undo entries', () => {
  const { save, editor } = fixture();
  const before = save.data.slice();
  for (const name of ['1234567', '😀😀😀😀😀', 'a\0b', 'a\nb', '\ud800', 17, null]) {
    assert.throws(() => editor.apply(0, name));
    assert.deepEqual(save.data, before);
    assert.equal(save.undoStack.length, 0);
  }
  editor.apply(0, '一二三四五六');
  assert.equal(editor.values(0).name, '一二三四五六');
  editor.apply(0, 'ABCDEF');
  assert.equal(editor.values(0).name, 'ABCDEF');
  assert.throws(() => editor.values(40));
  assert.throws(() => new PlayerNameEditor(createDemo()).values(0), /rf4_sys/);
});

test('absent slot records are protected and unrecognized names are not silently rewritten', () => {
  const { save, editor } = fixture();
  save.setNumber(8, 'u32', 0);
  const before = save.data.slice();
  assert.equal(editor.values(0).present, false);
  assert.throws(() => editor.apply(0, 'Frey'), /existing save/);
  assert.deepEqual(save.data, before);
  save.setNumber(8, 'u32', 1);
  save.setNumber(0x504, 'u8', 255);
  assert.equal(editor.values(0).valid, false);
  assert.deepEqual(save.build().subarray(0x504, 0x517), save.data.subarray(0x504, 0x517));
});
