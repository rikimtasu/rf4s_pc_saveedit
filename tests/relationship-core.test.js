import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemo, SaveDocument, DATING_CANDIDATES, crc32 } from '../web/save-core.js';
import { RelationshipEditor } from '../web/relationship-core.js';

const offset = id => 0x1db40 + (id - 1) * 44;
function fixture(id = 1) {
  const seed = createDemo();
  seed.transact('Synthetic relationship', bytes => {
    const view = seed.view(bytes);
    bytes.fill(0xa5, offset(id), offset(id) + 44);
    view.setInt32(offset(id), 1574, true);
    view.setUint32(offset(id) + 8, 0xad400302, true);
    bytes[offset(id) + 12] = 97;
    view.setUint32(offset(id) + 20, 0xbeef807f | 133 << 7, true);
  });
  const save = new SaveDocument(seed.build());
  return { save, editor: new RelationshipEditor(save) };
}

test('dating and both nickname edits preserve all unrelated bytes and are one undoable change', () => {
  for (const person of DATING_CANDIDATES) {
    const { save, editor } = fixture(person.id);
    const before = save.data.slice();
    const expected = before.slice();
    const base = offset(person.id), view = save.view(expected);
    view.setUint32(base + 8, (view.getUint32(base + 8, true) & ~0x400000) >>> 0, true);
    expected[base + 12] = 24;
    view.setUint32(base + 20, (view.getUint32(base + 20, true) & ~0x7f80 | 185 << 7) >>> 0, true);
    editor.apply(person.id, { dating: 0, npcCallsPlayer: 24, playerCallsNpc: 185 });
    assert.deepEqual(save.data, expected);
    assert.deepEqual(save.original, before);
    assert.equal(save.undoStack.length, 1);
    assert.equal(editor.values(person.id).dating, 0);
    assert.equal(editor.values(person.id).npcCallsPlayer, 24);
    assert.equal(editor.values(person.id).playerCallsNpc, 185);
    assert.equal(save.readNumber(base, 'i32'), 1574);
    for (const platform of ['pc', 'switch']) {
      const output = new SaveDocument(save.build({ platform, experimental: true }));
      assert.equal(output.crcValid, true);
      assert.equal(new RelationshipEditor(output).values(person.id).playerCallsNpc, 185);
    }
    save.undo(); assert.deepEqual(save.data, before);
    save.redo(); assert.deepEqual(save.data, expected);
  }
});

test('dating and nicknames are independent; unknown stored nickname IDs remain untouched', () => {
  const { save, editor } = fixture();
  save.setNumber(offset(1) + 12, 'u8', 255);
  const before = save.data.slice();
  editor.apply(1, { dating: 0 });
  assert.equal(editor.values(1).npcCallsPlayer, 255);
  assert.equal(editor.values(1).playerCallsNpc, 133);
  assert.equal(editor.values(1).dating, 0);
  editor.apply(1, { dating: 1 });
  assert.deepEqual(save.data, before);
  editor.apply(1, { playerCallsNpc: 0 });
  assert.equal(editor.values(1).dating, 1);
  assert.equal(editor.values(1).npcCallsPlayer, 255);
});

test('all main NPCs have verified defaults; non-candidates only allow nickname edits', () => {
  const { save, editor } = fixture();
  for (let id = 1; id <= 23; id++) {
    const person = editor.values(id);
    assert.deepEqual(person.defaults, { male: { npcCallsPlayer: 23 + id, playerCallsNpc: id }, female: { npcCallsPlayer: 70 + id, playerCallsNpc: 47 + id } });
    editor.apply(id, person.defaults.female);
    assert.equal(editor.values(id).npcCallsPlayer, 70 + id);
    if (!person.canDate) assert.throws(() => editor.apply(id, { dating: 1 }), /marriage candidates/);
  }
  assert.equal(save.gender(), 'male');
});

test('invalid and mixed-invalid edits fail atomically without adding undo entries', () => {
  const { save, editor } = fixture();
  const before = save.data.slice();
  for (const changes of [{ dating: 2 }, { dating: '' }, { npcCallsPlayer: 186 }, { playerCallsNpc: -1 }, { playerCallsNpc: 1.5 }, { friendship: 10 }, { dating: 0, npcCallsPlayer: 256 }]) {
    assert.throws(() => editor.apply(1, changes));
    assert.deepEqual(save.data, before);
    assert.equal(save.undoStack.length, 0);
  }
  for (const id of [0, 24, 25, 26, 1.5]) assert.throws(() => editor.apply(id, { npcCallsPlayer: 97 }));
  const data = new Uint8Array(9304); data.set([82, 70, 52, 68]);
  new DataView(data.buffer).setUint32(4, crc32(data.subarray(8)), true);
  assert.throws(() => new RelationshipEditor(new SaveDocument(data)).values(1), /slot/);
});

test('current-gender nickname defaults cover all main NPCs and never alter bytes/history', () => {
  for (const gender of ['male', 'female']) for (let id = 1; id <= 23; id++) {
    const { save, editor } = fixture(id);
    save.setNumber(0x36, 'u8', gender === 'female' ? 1 : 0);
    save.setPlayer({ money: 123 }); save.undo();
    const bytes = save.data.slice(), undo = structuredClone(save.undoStack), redo = structuredClone(save.redoStack);
    const result = editor.currentGenderDefaults(id);
    assert.deepEqual(result, { id, gender, defaults: gender === 'male' ? { npcCallsPlayer: 23 + id, playerCallsNpc: id } : { npcCallsPlayer: 70 + id, playerCallsNpc: 47 + id } });
    assert.deepEqual(save.data, bytes); assert.deepEqual(save.undoStack, undo); assert.deepEqual(save.redoStack, redo);
    const dating = editor.values(id).dating, friendship = save.readNumber(offset(id), 'i32');
    editor.apply(id, result.defaults);
    assert.equal(editor.values(id).dating, dating); assert.equal(save.readNumber(offset(id), 'i32'), friendship);
    assert.equal(editor.values(id).npcCallsPlayer, result.defaults.npcCallsPlayer);
    assert.equal(editor.values(id).playerCallsNpc, result.defaults.playerCallsNpc);
    save.undo(); assert.deepEqual(save.data, bytes);
  }
});

test('nickname defaults use current saved gender, never appearance/original/export overrides or a guess', () => {
  const { save, editor } = fixture();
  save.build({ gender: 'female', resetAppearance: true });
  assert.equal(editor.currentGenderDefaults(1).gender, 'male');
  save.setNumber(0x20740, 'i32', 9999);
  assert.equal(editor.currentGenderDefaults(1).gender, 'male');
  save.setNumber(0x36, 'u8', 1);
  assert.equal(save.gender(save.original), 'male');
  assert.equal(editor.currentGenderDefaults(1).gender, 'female');
  save.setNumber(0x36, 'u8', 2);
  const before = save.data.slice(), depth = save.undoStack.length;
  assert.throws(() => editor.currentGenderDefaults(1), /unrecognized/);
  assert.deepEqual(save.data, before); assert.equal(save.undoStack.length, depth);
  for (const id of [0, 24, 25, 26]) assert.throws(() => editor.currentGenderDefaults(id));
});
