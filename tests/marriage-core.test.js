import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemo, SaveDocument, FLAGS_OFFSET } from '../web/save-core.js';
import { MarriageEditor, MARRIAGE_CANDIDATES, MARRIAGE_FIELDS } from '../web/marriage-core.js';
import { SAVE_METADATA } from '../web/save-metadata.js';

test('spouse, anniversary and candidate records are one atomic undoable flag edit', () => {
  const save = createDemo(); const editor = new MarriageEditor(save);
  const before = save.data.slice();
  editor.apply({ spouse: 17, season: 3, day: 30, proposal: 1, marriageEvent: 1, newlywedEvent: 1 }, 17);
  assert.equal(editor.values().spouse, 17); assert.equal(editor.values().day, 30); assert.deepEqual(editor.events(17), { marriageEvent: 1, newlywedEvent: 1 });
  assert.deepEqual(editor.events(20), { marriageEvent: 0, newlywedEvent: 0 });
  const allowed = new Set([...MARRIAGE_FIELDS.map(field => editor.field(field.name)), ...Object.values(editor.eventFields(17))].flatMap(field => Array.from({ length: field.width }, (_, i) => field.bitOffset + i)));
  for (let index = 4; index < save.size; index++) for (let bit = 0; bit < 8; bit++) if (!allowed.has((index - FLAGS_OFFSET) * 8 + bit)) assert.equal((save.data[index] >>> bit) & 1, (before[index] >>> bit) & 1);
  assert.equal(save.undoStack.length, 1); assert.equal(new SaveDocument(save.build()).crcValid, true);
  save.undo(); assert.deepEqual(save.data, before); save.redo(); assert.equal(editor.values().spouse, 17);
});

test('all candidates have verified paired event flags and do not change other candidates', () => {
  for (const person of MARRIAGE_CANDIDATES) {
    const save = createDemo(); const editor = new MarriageEditor(save);
    editor.apply({ marriageEvent: 1 }, person.id);
    assert.equal(editor.events(person.id).marriageEvent, 1);
    assert.equal(editor.values().spouse, new MarriageEditor(new SaveDocument(save.original)).values().spouse);
  }
});

test('marriage rejects unknown spouse, fields, flags, dates and changed layouts without writes', () => {
  const save = createDemo(); const editor = new MarriageEditor(save);
  for (const changes of [{ spouse: 3 }, { spouse: 32 }, { day: 31 }, { season: 4 }, { proposal: 2 }, { day: '' }, { child: 1 }, { newlywedEvent: 2 }]) {
    assert.throws(() => editor.apply(changes, 1)); assert.deepEqual(save.data, save.original);
  }
  const symbols = SAVE_METADATA.symbols.map(field => field.name === 'REG_WIFE_ID' ? { ...field, bitOffset: 0 } : field);
  assert.throws(() => new MarriageEditor(save, symbols).apply({ spouse: 1 }, 1), /layout/);
  editor.apply({ spouse: 0, day: 0 }, 1);
  assert.equal(editor.values().spouse, 0);
});
